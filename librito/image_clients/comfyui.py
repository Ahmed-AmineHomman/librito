"""ComfyUI API client for image generation."""

from __future__ import annotations

import copy
import io
import json
import logging
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from importlib import resources

from PIL import Image

from librito.image_clients.utils import compute_dimensions

logger = logging.getLogger(__name__)

_RESOURCE_DIRECTORY = resources.files("librito.resources")
_CHECKPOINT_WORKFLOW_FILENAME = "workflow_checkpoint.json"
_DIFFUSION_WORKFLOW_FILENAME = "workflow_diffusion.json"

# Node IDs in workflow_checkpoint.json
_CKP_SAMPLER_NODE_ID = "3"
_CKP_CHECKPOINT_NODE_ID = "4"
_CKP_LATENT_NODE_ID = "5"
_CKP_PROMPT_NODE_ID = "6"
_CKP_OUTPUT_NODE_ID = "9"

# Node IDs in workflow_diffusion.json
_DIF_UNET_NODE_ID = "1"
_DIF_CLIP_NODE_ID = "2"
_DIF_VAE_NODE_ID = "3"
_DIF_LATENT_NODE_ID = "5"
_DIF_PROMPT_NODE_ID = "6"
_DIF_SAMPLER_NODE_ID = "8"
_DIF_OUTPUT_NODE_ID = "11"

_SERVER_URL_ENV_VAR = "COMFYUI_API_URL"
_API_KEY_ENV_VAR = "COMFYUI_API_KEY"


class ComfyUIImageClientError(RuntimeError):
    """Raised when ComfyUI image generation fails."""


class ComfyUIImageClient:
    """Image generation client backed by a ComfyUI instance.

    Loads either the checkpoint or diffusion workflow template (depending on
    the provided configuration), injects prompt, model(s), and dimensions,
    submits the workflow via the ComfyUI REST API, then polls for the result
    and downloads the generated image.
    """

    def __init__(
            self,
            *,
            checkpoint: str = "",
            diffusion_model: str = "",
            clip: str = "",
            vae: str = "",
            aspect_ratio: str = "1:1",
            image_size: str = "1K",
            poll_interval: float = 1.0,
    ) -> None:
        """Initialize the client.

        Parameters
        ----------
        checkpoint:
            Checkpoint filename for the checkpoint workflow.
        diffusion_model:
            UNET model filename for the diffusion workflow.
        clip:
            CLIP model filename for the diffusion workflow.
        vae:
            VAE model filename for the diffusion workflow.
        aspect_ratio:
            Requested image aspect ratio.
        image_size:
            Requested overall image resolution.
        poll_interval:
            Seconds between history polling requests.
        """

        server_url = os.getenv(_SERVER_URL_ENV_VAR, "").strip()
        if not server_url:
            raise RuntimeError(f"Missing required environment variable: {_SERVER_URL_ENV_VAR}.")
        if checkpoint and (diffusion_model or clip or vae):
            raise ValueError("Checkpoint and diffusion parameters are mutually exclusive.")
        if not checkpoint and not (diffusion_model and clip and vae):
            raise ValueError(
                "Provide either checkpoint or all of diffusion_model, clip, and vae."
            )

        self._server_url = server_url.rstrip("/")
        self._poll_interval = poll_interval
        self._is_checkpoint_mode = bool(checkpoint)
        self._width, self._height = compute_dimensions(
            aspect_ratio,
            image_size,
        )

        if self._is_checkpoint_mode:
            self._checkpoint = self._resolve_server_model(
                checkpoint,
                "CheckpointLoaderSimple",
                "ckpt_name",
                "checkpoint",
            )
            workflow_filename = _CHECKPOINT_WORKFLOW_FILENAME
            self._output_node_id = _CKP_OUTPUT_NODE_ID
            logger.info("ComfyUI client initialised in checkpoint mode (model: %s).", self._checkpoint)
        else:
            self._diffusion_model = self._resolve_server_model(
                diffusion_model,
                "UNETLoader",
                "unet_name",
                "diffusion model",
            )
            self._clip = self._resolve_server_model(
                clip,
                "CLIPLoader",
                "clip_name",
                "CLIP model",
            )
            self._vae = self._resolve_server_model(
                vae,
                "VAELoader",
                "vae_name",
                "VAE model",
            )
            workflow_filename = _DIFFUSION_WORKFLOW_FILENAME
            self._output_node_id = _DIF_OUTPUT_NODE_ID
            logger.info(
                "ComfyUI client initialised in diffusion mode (unet: %s, clip: %s, vae: %s).",
                self._diffusion_model,
                self._clip,
                self._vae,
            )
        self._workflow_template = json.loads(
            _RESOURCE_DIRECTORY.joinpath(workflow_filename).read_text(encoding="utf-8")
        )

    @staticmethod
    def _request_headers(extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        """Build HTTP headers for ComfyUI requests.

        Parameters
        ----------
        extra_headers:
            Additional headers to merge into the request.

        Returns
        -------
        dict[str, str]
            Headers including optional API-key authentication.
        """

        headers = dict(extra_headers or {})
        api_key = os.getenv(_API_KEY_ENV_VAR, "").strip()
        if api_key:
            headers.setdefault("Authorization", f"Bearer {api_key}")
            headers.setdefault("X-API-Key", api_key)
        return headers

    def _resolve_server_model(
            self,
            model: str,
            node_class: str,
            field_name: str,
            label: str,
    ) -> str:
        """Resolve a user-provided model name to the server's canonical form.

        Parameters
        ----------
        model:
            Model name as provided by the user.
        node_class:
            ComfyUI node class name exposing the target model list.
        field_name:
            Input field name holding the list of model filenames.
        label:
            Human-readable label for error messages.

        Returns
        -------
        str
            The canonical model name recognised by the server.

        Raises
        ------
        ComfyUIImageClientError
            If the model cannot be found on the server.
        """

        url = f"{self._server_url}/object_info/{node_class}"
        try:
            request = urllib.request.Request(url, headers=self._request_headers())
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode("utf-8"))
            available = list(data[node_class]["input"]["required"][field_name][0])
        except (KeyError, IndexError) as error:
            raise ComfyUIImageClientError(
                f"Unexpected {node_class} info response structure: {error}."
            ) from error
        except Exception as error:
            raise ComfyUIImageClientError(
                f"Failed to query available {node_class} models from ComfyUI: {error}."
            ) from error

        if model in available:
            return model

        normalized_input = model.replace("\\", "/")
        for candidate in available:
            if candidate.replace("\\", "/") == normalized_input:
                return candidate

        raise ComfyUIImageClientError(
            f"{label.capitalize()} {model!r} not found on the ComfyUI server. "
            f"Available: {available}"
        )

    def generate_image(self, prompt: str) -> Image.Image:
        """Generate a single image for a prompt.

        Parameters
        ----------
        prompt:
            Fully assembled prompt to send to ComfyUI.

        Returns
        -------
        Image.Image
            Generated image.

        Raises
        ------
        ComfyUIImageClientError
            If any step of the generation pipeline fails.
        """

        if self._is_checkpoint_mode:
            workflow = copy.deepcopy(self._workflow_template)
            workflow[_CKP_SAMPLER_NODE_ID]["inputs"]["seed"] = random.randint(0, 2 ** 31 - 1)
            workflow[_CKP_CHECKPOINT_NODE_ID]["inputs"]["ckpt_name"] = self._checkpoint
            workflow[_CKP_LATENT_NODE_ID]["inputs"]["width"] = self._width
            workflow[_CKP_LATENT_NODE_ID]["inputs"]["height"] = self._height
            workflow[_CKP_PROMPT_NODE_ID]["inputs"]["text"] = prompt
        else:
            workflow = copy.deepcopy(self._workflow_template)
            workflow[_DIF_SAMPLER_NODE_ID]["inputs"]["seed"] = random.randint(0, 2 ** 31 - 1)
            workflow[_DIF_UNET_NODE_ID]["inputs"]["unet_name"] = self._diffusion_model
            workflow[_DIF_CLIP_NODE_ID]["inputs"]["clip_name"] = self._clip
            workflow[_DIF_VAE_NODE_ID]["inputs"]["vae_name"] = self._vae
            workflow[_DIF_LATENT_NODE_ID]["inputs"]["width"] = self._width
            workflow[_DIF_LATENT_NODE_ID]["inputs"]["height"] = self._height
            workflow[_DIF_PROMPT_NODE_ID]["inputs"]["text"] = prompt

        payload = json.dumps({"prompt": workflow}).encode("utf-8")
        submit_request = urllib.request.Request(
            f"{self._server_url}/prompt",
            data=payload,
            headers=self._request_headers({"Content-Type": "application/json"}),
            method="POST",
        )
        try:
            with urllib.request.urlopen(submit_request) as response:
                submit_result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise ComfyUIImageClientError(
                f"ComfyUI rejected the workflow (HTTP {error.code}): {body}"
            ) from error
        except Exception as error:
            raise ComfyUIImageClientError(
                f"Failed to submit workflow to ComfyUI: {error}."
            ) from error

        prompt_id = submit_result["prompt_id"]
        history_url = f"{self._server_url}/history/{prompt_id}"

        while True:
            try:
                history_request = urllib.request.Request(
                    history_url,
                    headers=self._request_headers(),
                )
                with urllib.request.urlopen(history_request) as response:
                    history = json.loads(response.read().decode("utf-8"))
            except Exception as error:
                raise ComfyUIImageClientError(
                    f"Failed to poll ComfyUI history: {error}."
                ) from error

            if prompt_id in history:
                history_entry = history[prompt_id]
                status = history_entry.get("status", {})
                if status.get("status_str") == "error":
                    error_detail = "unknown error"
                    for msg_type, msg_data in status.get("messages", []):
                        if msg_type == "execution_error":
                            node_id = msg_data.get("node_id", "?")
                            node_type = msg_data.get("node_type", "?")
                            exc_msg = msg_data.get("exception_message", "")
                            error_detail = f"node {node_id} ({node_type}): {exc_msg}"
                            break
                    raise ComfyUIImageClientError(
                        f"ComfyUI execution failed at {error_detail}"
                    )
                break

            time.sleep(self._poll_interval)

        outputs = history_entry.get("outputs", {})
        if self._output_node_id not in outputs:
            raise ComfyUIImageClientError(f"No output found for node {self._output_node_id}.")

        images = outputs[self._output_node_id].get("images", [])
        if not images:
            raise ComfyUIImageClientError(f"No image found in output node {self._output_node_id}.")

        image_info = images[0]
        query = urllib.parse.urlencode(
            {
                "filename": image_info["filename"],
                "subfolder": image_info.get("subfolder", ""),
                "type": image_info.get("type", "output"),
            }
        )
        url = f"{self._server_url}/view?{query}"

        try:
            request = urllib.request.Request(url, headers=self._request_headers())
            with urllib.request.urlopen(request) as response:
                data = response.read()
        except Exception as error:
            raise ComfyUIImageClientError(
                f"Failed to download image from ComfyUI: {error}."
            ) from error

        return Image.open(io.BytesIO(data))
