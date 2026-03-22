"""Tests for the ComfyUI image generation client."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

from librito.image_clients.comfyui import (
    ComfyUIImageClient,
    ComfyUIImageClientConfig,
    ComfyUIImageClientError,
    extract_output_image_info,
    prepare_workflow,
    resolve_model_name,
)


class PrepareWorkflowTests(unittest.TestCase):
    """Validate workflow template injection."""

    def test_injects_prompt_model_and_dimensions(self) -> None:
        """All user parameters should appear in the prepared workflow."""

        template = _minimal_workflow_template()

        result = prepare_workflow(
            workflow_template=template,
            prompt="a cute cat",
            model="mymodel.safetensors",
            width=768,
            height=512,
        )

        self.assertEqual(result["4"]["inputs"]["ckpt_name"], "mymodel.safetensors")
        self.assertEqual(result["5"]["inputs"]["width"], 768)
        self.assertEqual(result["5"]["inputs"]["height"], 512)
        self.assertEqual(result["6"]["inputs"]["text"], "a cute cat")

    def test_does_not_mutate_original_template(self) -> None:
        """The original template must remain unchanged."""

        template = _minimal_workflow_template()
        original_prompt = template["6"]["inputs"]["text"]

        prepare_workflow(
            workflow_template=template,
            prompt="changed",
            model="m.safetensors",
            width=100,
            height=100,
        )

        self.assertEqual(template["6"]["inputs"]["text"], original_prompt)


class ExtractOutputImageInfoTests(unittest.TestCase):
    """Validate image metadata extraction from history."""

    def test_returns_first_image_from_output_node(self) -> None:
        """Should return the first image dict from the output node."""

        history_entry = {
            "outputs": {
                "9": {
                    "images": [
                        {
                            "filename": "ComfyUI_00001_.png",
                            "subfolder": "",
                            "type": "output",
                        }
                    ]
                }
            }
        }

        result = extract_output_image_info(history_entry)

        self.assertEqual(result["filename"], "ComfyUI_00001_.png")

    def test_raises_when_output_node_missing(self) -> None:
        """Should raise when the expected output node is absent."""

        with self.assertRaises(ComfyUIImageClientError):
            extract_output_image_info({"outputs": {}})

    def test_raises_when_no_images(self) -> None:
        """Should raise when the output node has no images."""

        history_entry = {"outputs": {"9": {"images": []}}}

        with self.assertRaises(ComfyUIImageClientError):
            extract_output_image_info(history_entry)


class ComfyUIImageClientConfigTests(unittest.TestCase):
    """Validate configuration resolution."""

    def test_explicit_server_url_takes_precedence(self) -> None:
        """An explicit server_url should be used as-is."""

        config = ComfyUIImageClientConfig(
            model="m.safetensors",
            server_url="http://myhost:9999/",
        )

        self.assertEqual(config.resolved_server_url(), "http://myhost:9999")

    @patch.dict("os.environ", {"COMFYUI_API_URL": "http://envhost:7777"})
    def test_env_var_used_when_no_explicit_url(self) -> None:
        """The COMFYUI_API_URL env var should be used as fallback."""

        config = ComfyUIImageClientConfig(model="m.safetensors")

        self.assertEqual(config.resolved_server_url(), "http://envhost:7777")

    @patch.dict("os.environ", {}, clear=True)
    def test_default_url_when_nothing_configured(self) -> None:
        """Should fall back to localhost:8188."""

        config = ComfyUIImageClientConfig(model="m.safetensors")

        self.assertEqual(
            config.resolved_server_url(), "http://127.0.0.1:8188"
        )


class ResolveModelNameTests(unittest.TestCase):
    """Validate model name resolution against server checkpoints."""

    @patch("librito.image_clients.comfyui._fetch_available_checkpoints")
    def test_exact_match_returned_as_is(self, mock_fetch: MagicMock) -> None:
        """An exact match should be returned unchanged."""

        mock_fetch.return_value = ["sd1\\dreamshaper.safetensors"]

        result = resolve_model_name("sd1\\dreamshaper.safetensors", "http://test")

        self.assertEqual(result, "sd1\\dreamshaper.safetensors")

    @patch("librito.image_clients.comfyui._fetch_available_checkpoints")
    def test_forward_slash_resolved_to_backslash(self, mock_fetch: MagicMock) -> None:
        """Forward slashes should match backslash-based server names."""

        mock_fetch.return_value = ["sd1\\dreamshaper.safetensors"]

        result = resolve_model_name("sd1/dreamshaper.safetensors", "http://test")

        self.assertEqual(result, "sd1\\dreamshaper.safetensors")

    @patch("librito.image_clients.comfyui._fetch_available_checkpoints")
    def test_unknown_model_raises(self, mock_fetch: MagicMock) -> None:
        """An unknown model should raise with available checkpoints listed."""

        mock_fetch.return_value = ["sd1\\dreamshaper.safetensors"]

        with self.assertRaises(ComfyUIImageClientError):
            resolve_model_name("nonexistent.safetensors", "http://test")


class ComfyUIImageClientIntegrationTests(unittest.TestCase):
    """Validate the full generate_image flow with mocked HTTP calls."""

    @patch("librito.image_clients.comfyui.resolve_model_name", side_effect=lambda m, s: m)
    @patch("librito.image_clients.comfyui._load_workflow_template")
    @patch("librito.image_clients.comfyui.download_image")
    @patch("librito.image_clients.comfyui.wait_for_completion")
    @patch("librito.image_clients.comfyui.submit_workflow")
    def test_generate_image_returns_pil_image(
        self,
        mock_submit: MagicMock,
        mock_wait: MagicMock,
        mock_download: MagicMock,
        mock_load_template: MagicMock,
        mock_resolve: MagicMock,
    ) -> None:
        """The full pipeline should return a PIL Image."""

        mock_load_template.return_value = _minimal_workflow_template()
        mock_submit.return_value = "test-prompt-id"
        mock_wait.return_value = {
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
            }
        }
        expected_image = Image.new("RGB", (4, 4), color="green")
        mock_download.return_value = expected_image

        client = ComfyUIImageClient(
            ComfyUIImageClientConfig(
                model="test.safetensors",
                server_url="http://test:8188",
            )
        )
        result = client.generate_image("a landscape")

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (4, 4))
        mock_submit.assert_called_once()
        mock_wait.assert_called_once_with(
            prompt_id="test-prompt-id",
            server_url="http://test:8188",
            poll_interval=1.0,
        )

    @patch("librito.image_clients.comfyui.resolve_model_name", side_effect=lambda m, s: m)
    @patch("librito.image_clients.comfyui._load_workflow_template")
    @patch("librito.image_clients.comfyui.submit_workflow")
    def test_submit_failure_raises_error(
        self,
        mock_submit: MagicMock,
        mock_load_template: MagicMock,
        mock_resolve: MagicMock,
    ) -> None:
        """A submission failure should propagate as ComfyUIImageClientError."""

        mock_load_template.return_value = _minimal_workflow_template()
        mock_submit.side_effect = ComfyUIImageClientError("connection refused")

        client = ComfyUIImageClient(
            ComfyUIImageClientConfig(
                model="test.safetensors",
                server_url="http://test:8188",
            )
        )

        with self.assertRaises(ComfyUIImageClientError):
            client.generate_image("a prompt")


def _minimal_workflow_template() -> dict[str, object]:
    """Build a minimal workflow template matching workflow_checkpoint.json structure.

    Returns
    -------
    dict[str, object]
        Workflow with nodes 4, 5, 6, and 9.
    """

    return {
        "3": {
            "inputs": {
                "seed": 42,
                "steps": 20,
                "cfg": 7,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "4": {
            "inputs": {"ckpt_name": "default.safetensors"},
            "class_type": "CheckpointLoaderSimple",
        },
        "5": {
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
            "class_type": "EmptyLatentImage",
        },
        "6": {
            "inputs": {"text": "", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {"text": "bad quality", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode",
        },
        "8": {
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            "class_type": "VAEDecode",
        },
        "9": {
            "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
            "class_type": "SaveImage",
        },
    }
