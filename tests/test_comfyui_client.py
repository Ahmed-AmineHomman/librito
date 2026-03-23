"""Tests for the ComfyUI image generation client."""

from __future__ import annotations

import io
import json
import unittest
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

from PIL import Image

from librito.image_clients.comfyui import ComfyUIImageClient, ComfyUIImageClientError


class ComfyUIImageClientTests(unittest.TestCase):
    """Validate ComfyUI client behavior."""

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_server_url_env_var_raises(self) -> None:
        """The client should fail fast when ``COMFYUI_API_URL`` is absent."""

        with self.assertRaisesRegex(RuntimeError, "COMFYUI_API_URL"):
            ComfyUIImageClient(checkpoint="model.safetensors")

    @patch.dict("os.environ", {"COMFYUI_API_URL": "http://test:8188"}, clear=True)
    @patch("librito.image_clients.comfyui.urllib.request.urlopen")
    def test_checkpoint_generate_image_returns_pil_image(
        self,
        mock_urlopen: MagicMock,
    ) -> None:
        """Checkpoint mode should return the generated image."""

        mock_urlopen.side_effect = [
            _json_response(
                {
                    "CheckpointLoaderSimple": {
                        "input": {"required": {"ckpt_name": [["model.safetensors"]]}}
                    }
                }
            ),
            _json_response({"prompt_id": "prompt-123"}),
            _json_response(
                {
                    "prompt-123": {
                        "status": {"status_str": "success"},
                        "outputs": {
                            "9": {
                                "images": [
                                    {
                                        "filename": "result.png",
                                        "subfolder": "",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                    }
                }
            ),
            _binary_response(_image_bytes("green")),
        ]

        client = ComfyUIImageClient(checkpoint="model.safetensors")
        result = client.generate_image("a landscape")

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (4, 4))

    @patch.dict("os.environ", {"COMFYUI_API_URL": "http://test:8188"}, clear=True)
    @patch("librito.image_clients.comfyui.urllib.request.urlopen")
    def test_checkpoint_submit_failure_raises_error(
        self,
        mock_urlopen: MagicMock,
    ) -> None:
        """Checkpoint mode should propagate submission failures."""

        mock_urlopen.side_effect = [
            _json_response(
                {
                    "CheckpointLoaderSimple": {
                        "input": {"required": {"ckpt_name": [["model.safetensors"]]}}
                    }
                }
            ),
            _http_error("http://test:8188/prompt", 500, "connection refused"),
        ]

        client = ComfyUIImageClient(checkpoint="model.safetensors")

        with self.assertRaisesRegex(ComfyUIImageClientError, "connection refused"):
            client.generate_image("a prompt")

    @patch.dict("os.environ", {"COMFYUI_API_URL": "http://test:8188"}, clear=True)
    @patch("librito.image_clients.comfyui.urllib.request.urlopen")
    def test_diffusion_generate_image_returns_pil_image(
        self,
        mock_urlopen: MagicMock,
    ) -> None:
        """Diffusion mode should return the generated image."""

        mock_urlopen.side_effect = [
            _json_response(
                {"UNETLoader": {"input": {"required": {"unet_name": [["unet.safetensors"]]}}}}
            ),
            _json_response(
                {"CLIPLoader": {"input": {"required": {"clip_name": [["clip.safetensors"]]}}}}
            ),
            _json_response(
                {"VAELoader": {"input": {"required": {"vae_name": [["vae.safetensors"]]}}}}
            ),
            _json_response({"prompt_id": "prompt-123"}),
            _json_response(
                {
                    "prompt-123": {
                        "status": {"status_str": "success"},
                        "outputs": {
                            "11": {
                                "images": [
                                    {
                                        "filename": "result.png",
                                        "subfolder": "",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                    }
                }
            ),
            _binary_response(_image_bytes("blue")),
        ]

        client = ComfyUIImageClient(
            diffusion_model="unet.safetensors",
            clip="clip.safetensors",
            vae="vae.safetensors",
        )
        result = client.generate_image("a landscape")

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (4, 4))

    @patch.dict("os.environ", {"COMFYUI_API_URL": "http://test:8188"}, clear=True)
    @patch("librito.image_clients.comfyui.urllib.request.urlopen")
    def test_execution_error_raises_client_error(
        self,
        mock_urlopen: MagicMock,
    ) -> None:
        """Execution failures reported by ComfyUI should raise a client error."""

        mock_urlopen.side_effect = [
            _json_response(
                {
                    "CheckpointLoaderSimple": {
                        "input": {"required": {"ckpt_name": [["model.safetensors"]]}}
                    }
                }
            ),
            _json_response({"prompt_id": "prompt-123"}),
            _json_response(
                {
                    "prompt-123": {
                        "status": {
                            "status_str": "error",
                            "messages": [
                                [
                                    "execution_error",
                                    {
                                        "node_id": "3",
                                        "node_type": "KSampler",
                                        "exception_message": "boom",
                                    },
                                ]
                            ],
                        }
                    }
                }
            ),
        ]

        client = ComfyUIImageClient(checkpoint="model.safetensors")

        with self.assertRaisesRegex(ComfyUIImageClientError, "node 3 \\(KSampler\\): boom"):
            client.generate_image("a prompt")


def _binary_response(payload: bytes) -> MagicMock:
    """Build a mocked HTTP response returning raw bytes.

    Parameters
    ----------
    payload:
        Response body to expose through ``read()``.

    Returns
    -------
    MagicMock
        Context-manager compatible mocked response.
    """

    response = MagicMock()
    response.__enter__.return_value.read.return_value = payload
    return response


def _http_error(url: str, code: int, body: str) -> urllib.error.HTTPError:
    """Build an ``HTTPError`` carrying a text response body.

    Parameters
    ----------
    url:
        URL associated with the failing request.
    code:
        HTTP status code.
    body:
        Response body returned by the server.

    Returns
    -------
    urllib.error.HTTPError
        Error object readable by the client code.
    """

    return urllib.error.HTTPError(
        url=url,
        code=code,
        msg="Server Error",
        hdrs=None,
        fp=io.BytesIO(body.encode("utf-8")),
    )


def _image_bytes(color: str) -> bytes:
    """Build a tiny PNG payload for mocked HTTP responses.

    Parameters
    ----------
    color:
        Fill color used in the generated image.

    Returns
    -------
    bytes
        PNG-encoded image bytes.
    """

    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def _json_response(payload: object) -> MagicMock:
    """Build a mocked HTTP response returning JSON data.

    Parameters
    ----------
    payload:
        JSON-serializable body returned by the mock response.

    Returns
    -------
    MagicMock
        Context-manager compatible mocked response.
    """

    return _binary_response(json.dumps(payload).encode("utf-8"))
