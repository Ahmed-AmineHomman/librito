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
from dataclasses import dataclass
from importlib import resources
from typing import Any

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

_DEFAULT_SERVER_URL = "http://127.0.0.1:8188"
_SERVER_URL_ENV_VAR = "COMFYUI_API_URL"


@dataclass(frozen=True, slots=True)
class ComfyUIImageClientConfig:
    """Configuration for ComfyUI image generation requests.

    Exactly one workflow mode must be selected:

    * **Checkpoint mode** — set ``checkpoint`` to the checkpoint filename
      (e.g. ``"sd1/arthemycomics.safetensors"``).
    * **Diffusion mode** — set ``diffusion_model``, ``clip``, and ``vae``
      to the respective filenames used by the separate loader nodes.

    Parameters
    ----------
    checkpoint:
        Checkpoint filename for the ``CheckpointLoaderSimple`` node.
    diffusion_model:
        UNET model filename for the ``UNETLoader`` node.
    clip:
        CLIP model filename for the ``CLIPLoader`` node.
    vae:
        VAE model filename for the ``VAELoader`` node.
    server_url:
        Base URL of the ComfyUI instance.  Falls back to the
        ``COMFYUI_API_URL`` environment variable, then to
        ``http://127.0.0.1:8188``.
    aspect_ratio:
        Requested image aspect ratio.
    image_size:
        Requested overall image resolution (``"0.5K"``, ``"1K"``, or
        ``"2K"``).
    poll_interval:
        Seconds between history polling requests.
    """

    checkpoint: str = ""
    diffusion_model: str = ""
    clip: str = ""
    vae: str = ""
    server_url: str = ""
    aspect_ratio: str = "1:1"
    image_size: str = "1K"
    poll_interval: float = 1.0

    @property
    def is_checkpoint_mode(self) -> bool:
        """Return ``True`` when the checkpoint workflow should be used.

        Returns
        -------
        bool
        """

        return bool(self.checkpoint)

    def resolved_server_url(self) -> str:
        """Return the effective server URL.

        Returns
        -------
        str
            The explicitly configured URL, the ``COMFYUI_API_URL`` environment
            variable, or the default ``http://127.0.0.1:8188``.
        """

        if self.server_url:
            return self.server_url.rstrip("/")
        return os.getenv(_SERVER_URL_ENV_VAR, _DEFAULT_SERVER_URL).rstrip("/")


class ComfyUIImageClientError(RuntimeError):
    """Raised when ComfyUI image generation fails."""


def _fetch_available_checkpoints(server_url: str) -> list[str]:
    """Query the ComfyUI server for available checkpoint names.

    Parameters
    ----------
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    list[str]
        Checkpoint filenames as known by the server.

    Raises
    ------
    ComfyUIImageClientError
        If the request fails.
    """

    return _fetch_available_models(server_url, "CheckpointLoaderSimple", "ckpt_name")


def _fetch_available_unet_models(server_url: str) -> list[str]:
    """Query the ComfyUI server for available UNET model names.

    Parameters
    ----------
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    list[str]
        UNET model filenames as known by the server.

    Raises
    ------
    ComfyUIImageClientError
        If the request fails.
    """

    return _fetch_available_models(server_url, "UNETLoader", "unet_name")


def _fetch_available_clip_models(server_url: str) -> list[str]:
    """Query the ComfyUI server for available CLIP model names.

    Parameters
    ----------
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    list[str]
        CLIP model filenames as known by the server.

    Raises
    ------
    ComfyUIImageClientError
        If the request fails.
    """

    return _fetch_available_models(server_url, "CLIPLoader", "clip_name")


def _fetch_available_vae_models(server_url: str) -> list[str]:
    """Query the ComfyUI server for available VAE model names.

    Parameters
    ----------
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    list[str]
        VAE model filenames as known by the server.

    Raises
    ------
    ComfyUIImageClientError
        If the request fails.
    """

    return _fetch_available_models(server_url, "VAELoader", "vae_name")


def _fetch_available_models(
    server_url: str,
    node_class: str,
    field_name: str,
) -> list[str]:
    """Query the ComfyUI server for available model names of a given node type.

    Parameters
    ----------
    server_url:
        Base URL of the ComfyUI server (without trailing slash).
    node_class:
        ComfyUI node class name (e.g. ``"CheckpointLoaderSimple"``).
    field_name:
        Input field name holding the list of model filenames.

    Returns
    -------
    list[str]
        Model filenames as known by the server.

    Raises
    ------
    ComfyUIImageClientError
        If the request fails.
    """

    url = f"{server_url}/object_info/{node_class}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise ComfyUIImageClientError(
            f"Failed to query available {node_class} models from ComfyUI: {error}."
        ) from error

    try:
        return list(data[node_class]["input"]["required"][field_name][0])
    except (KeyError, IndexError) as error:
        raise ComfyUIImageClientError(
            f"Unexpected {node_class} info response structure: {error}."
        ) from error


def _normalize_path(value: str) -> str:
    """Normalize a path string for comparison by using forward slashes.

    Parameters
    ----------
    value:
        Path string that may use backslashes or forward slashes.

    Returns
    -------
    str
        Path with all separators converted to ``/``.
    """

    return value.replace("\\", "/")


def resolve_model_name(
    model: str,
    server_url: str,
    fetcher: Any = _fetch_available_checkpoints,
    label: str = "checkpoint",
) -> str:
    """Resolve a user-provided model name to the server's canonical form.

    The user may type ``sd1/dreamshaper.safetensors`` while the server knows
    the checkpoint as ``sd1\\dreamshaper.safetensors`` (or vice-versa depending
    on the platform).  This function queries the server and returns the exact
    name the server expects.

    Parameters
    ----------
    model:
        Model name as provided by the user.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).
    fetcher:
        Callable that queries the server for available model names.
        Defaults to :func:`_fetch_available_checkpoints`.
    label:
        Human-readable label for error messages (e.g. ``"checkpoint"``,
        ``"UNET model"``).

    Returns
    -------
    str
        The canonical model name recognised by the server.

    Raises
    ------
    ComfyUIImageClientError
        If the model cannot be found on the server.
    """

    available = fetcher(server_url)

    if model in available:
        return model

    normalized_input = _normalize_path(model)
    for candidate in available:
        if _normalize_path(candidate) == normalized_input:
            return candidate

    raise ComfyUIImageClientError(
        f"{label.capitalize()} {model!r} not found on the ComfyUI server. "
        f"Available: {available}"
    )


def resolve_checkpoint_name(model: str, server_url: str) -> str:
    """Resolve a checkpoint name against the server.

    Parameters
    ----------
    model:
        User-provided checkpoint filename.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    str
        Canonical checkpoint name recognised by the server.
    """

    return resolve_model_name(model, server_url, _fetch_available_checkpoints, "checkpoint")


def resolve_unet_name(model: str, server_url: str) -> str:
    """Resolve a UNET model name against the server.

    Parameters
    ----------
    model:
        User-provided UNET model filename.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    str
        Canonical UNET model name recognised by the server.
    """

    return resolve_model_name(model, server_url, _fetch_available_unet_models, "diffusion model")


def resolve_clip_name(model: str, server_url: str) -> str:
    """Resolve a CLIP model name against the server.

    Parameters
    ----------
    model:
        User-provided CLIP model filename.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    str
        Canonical CLIP model name recognised by the server.
    """

    return resolve_model_name(model, server_url, _fetch_available_clip_models, "CLIP model")


def resolve_vae_name(model: str, server_url: str) -> str:
    """Resolve a VAE model name against the server.

    Parameters
    ----------
    model:
        User-provided VAE model filename.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    str
        Canonical VAE model name recognised by the server.
    """

    return resolve_model_name(model, server_url, _fetch_available_vae_models, "VAE model")


def _load_workflow_template(filename: str) -> dict[str, Any]:
    """Load a workflow template from package resources.

    Parameters
    ----------
    filename:
        Resource filename (e.g. ``"workflow_checkpoint.json"``).

    Returns
    -------
    dict[str, Any]
        Parsed workflow JSON.
    """

    raw = _RESOURCE_DIRECTORY.joinpath(filename).read_text(encoding="utf-8")
    return json.loads(raw)


def prepare_checkpoint_workflow(
    workflow_template: dict[str, Any],
    prompt: str,
    model: str,
    width: int,
    height: int,
) -> dict[str, Any]:
    """Create a checkpoint workflow copy with injected generation parameters.

    Parameters
    ----------
    workflow_template:
        Base workflow loaded from ``workflow_checkpoint.json``.
    prompt:
        Positive text prompt for the image.
    model:
        Checkpoint name for the ``CheckpointLoaderSimple`` node.
    width:
        Image width in pixels.
    height:
        Image height in pixels.

    Returns
    -------
    dict[str, Any]
        Ready-to-submit workflow with all parameters injected.
    """

    workflow = copy.deepcopy(workflow_template)
    workflow[_CKP_SAMPLER_NODE_ID]["inputs"]["seed"] = random.randint(0, 2**31 - 1)
    workflow[_CKP_CHECKPOINT_NODE_ID]["inputs"]["ckpt_name"] = model
    workflow[_CKP_LATENT_NODE_ID]["inputs"]["width"] = width
    workflow[_CKP_LATENT_NODE_ID]["inputs"]["height"] = height
    workflow[_CKP_PROMPT_NODE_ID]["inputs"]["text"] = prompt
    return workflow


def prepare_diffusion_workflow(
    workflow_template: dict[str, Any],
    prompt: str,
    diffusion_model: str,
    clip: str,
    vae: str,
    width: int,
    height: int,
) -> dict[str, Any]:
    """Create a diffusion workflow copy with injected generation parameters.

    Parameters
    ----------
    workflow_template:
        Base workflow loaded from ``workflow_diffusion.json``.
    prompt:
        Positive text prompt for the image.
    diffusion_model:
        UNET model filename for the ``UNETLoader`` node.
    clip:
        CLIP model filename for the ``CLIPLoader`` node.
    vae:
        VAE model filename for the ``VAELoader`` node.
    width:
        Image width in pixels.
    height:
        Image height in pixels.

    Returns
    -------
    dict[str, Any]
        Ready-to-submit workflow with all parameters injected.
    """

    workflow = copy.deepcopy(workflow_template)
    workflow[_DIF_SAMPLER_NODE_ID]["inputs"]["seed"] = random.randint(0, 2**31 - 1)
    workflow[_DIF_UNET_NODE_ID]["inputs"]["unet_name"] = diffusion_model
    workflow[_DIF_CLIP_NODE_ID]["inputs"]["clip_name"] = clip
    workflow[_DIF_VAE_NODE_ID]["inputs"]["vae_name"] = vae
    workflow[_DIF_LATENT_NODE_ID]["inputs"]["width"] = width
    workflow[_DIF_LATENT_NODE_ID]["inputs"]["height"] = height
    workflow[_DIF_PROMPT_NODE_ID]["inputs"]["text"] = prompt
    return workflow


# Keep backward-compatible aliases
prepare_workflow = prepare_checkpoint_workflow


def submit_workflow(workflow: dict[str, Any], server_url: str) -> str:
    """Submit a workflow to ComfyUI and return the prompt ID.

    Parameters
    ----------
    workflow:
        Fully configured workflow to queue.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    str
        The ``prompt_id`` assigned by ComfyUI.

    Raises
    ------
    ComfyUIImageClientError
        If the HTTP request fails.
    """

    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    request = urllib.request.Request(
        f"{server_url}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise ComfyUIImageClientError(
            f"ComfyUI rejected the workflow (HTTP {error.code}): {body}"
        ) from error
    except Exception as error:
        raise ComfyUIImageClientError(
            f"Failed to submit workflow to ComfyUI: {error}."
        ) from error

    return result["prompt_id"]


def wait_for_completion(
    prompt_id: str,
    server_url: str,
    poll_interval: float,
) -> dict[str, Any]:
    """Poll ComfyUI history until the prompt has completed.

    Parameters
    ----------
    prompt_id:
        Prompt ID returned by :func:`submit_workflow`.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).
    poll_interval:
        Seconds between polling attempts.

    Returns
    -------
    dict[str, Any]
        The history entry for the completed prompt.

    Raises
    ------
    ComfyUIImageClientError
        If polling fails.
    """

    history_url = f"{server_url}/history/{prompt_id}"

    while True:
        try:
            with urllib.request.urlopen(history_url) as response:
                history = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            raise ComfyUIImageClientError(
                f"Failed to poll ComfyUI history: {error}."
            ) from error

        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                error_detail = "unknown error"
                for msg_type, msg_data in status.get("messages", []):
                    if msg_type == "execution_error":
                        node_id = msg_data.get("node_id", "?")
                        node_type = msg_data.get("node_type", "?")
                        exc_msg = msg_data.get("exception_message", "")
                        error_detail = (
                            f"node {node_id} ({node_type}): {exc_msg}"
                        )
                        break
                raise ComfyUIImageClientError(
                    f"ComfyUI execution failed at {error_detail}"
                )
            return entry

        time.sleep(poll_interval)


def extract_output_image_info(
    history_entry: dict[str, Any],
    output_node_id: str = _CKP_OUTPUT_NODE_ID,
) -> dict[str, Any]:
    """Extract image metadata from the output node.

    Parameters
    ----------
    history_entry:
        History entry for a completed prompt.
    output_node_id:
        Node ID of the output (preview/save) node.

    Returns
    -------
    dict[str, Any]
        Image metadata dict with ``filename``, ``subfolder``, and ``type``
        keys.

    Raises
    ------
    ComfyUIImageClientError
        If no image is found in the output node.
    """

    outputs = history_entry.get("outputs", {})

    if output_node_id not in outputs:
        raise ComfyUIImageClientError(
            f"No output found for node {output_node_id}."
        )

    images = outputs[output_node_id].get("images", [])
    if not images:
        raise ComfyUIImageClientError(
            f"No image found in output node {output_node_id}."
        )

    return images[0]


def download_image(image_info: dict[str, Any], server_url: str) -> Image.Image:
    """Download an image from ComfyUI and return it as a PIL Image.

    Parameters
    ----------
    image_info:
        Image metadata returned by :func:`extract_output_image_info`.
    server_url:
        Base URL of the ComfyUI server (without trailing slash).

    Returns
    -------
    Image.Image
        The downloaded image.

    Raises
    ------
    ComfyUIImageClientError
        If the download fails.
    """

    query = urllib.parse.urlencode(
        {
            "filename": image_info["filename"],
            "subfolder": image_info.get("subfolder", ""),
            "type": image_info.get("type", "output"),
        }
    )
    url = f"{server_url}/view?{query}"

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
    except Exception as error:
        raise ComfyUIImageClientError(
            f"Failed to download image from ComfyUI: {error}."
        ) from error

    return Image.open(io.BytesIO(data))


class ComfyUIImageClient:
    """Image generation client backed by a ComfyUI instance.

    Loads either the checkpoint or diffusion workflow template (depending on
    the provided configuration), injects prompt, model(s), and dimensions,
    submits the workflow via the ComfyUI REST API, then polls for the result
    and downloads the generated image.
    """

    def __init__(self, config: ComfyUIImageClientConfig) -> None:
        """Initialize the client.

        Parameters
        ----------
        config:
            Runtime configuration for ComfyUI requests.
        """

        self._config = config
        self._server_url = config.resolved_server_url()
        self._width, self._height = compute_dimensions(
            config.aspect_ratio,
            config.image_size,
        )

        if config.is_checkpoint_mode:
            self._checkpoint = resolve_checkpoint_name(config.checkpoint, self._server_url)
            self._workflow_template = _load_workflow_template(_CHECKPOINT_WORKFLOW_FILENAME)
            self._output_node_id = _CKP_OUTPUT_NODE_ID
            logger.info("ComfyUI client initialised in checkpoint mode (model: %s).", self._checkpoint)
        else:
            self._diffusion_model = resolve_unet_name(config.diffusion_model, self._server_url)
            self._clip = resolve_clip_name(config.clip, self._server_url)
            self._vae = resolve_vae_name(config.vae, self._server_url)
            self._workflow_template = _load_workflow_template(_DIFFUSION_WORKFLOW_FILENAME)
            self._output_node_id = _DIF_OUTPUT_NODE_ID
            logger.info(
                "ComfyUI client initialised in diffusion mode (unet: %s, clip: %s, vae: %s).",
                self._diffusion_model,
                self._clip,
                self._vae,
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

        if self._config.is_checkpoint_mode:
            workflow = prepare_checkpoint_workflow(
                workflow_template=self._workflow_template,
                prompt=prompt,
                model=self._checkpoint,
                width=self._width,
                height=self._height,
            )
        else:
            workflow = prepare_diffusion_workflow(
                workflow_template=self._workflow_template,
                prompt=prompt,
                diffusion_model=self._diffusion_model,
                clip=self._clip,
                vae=self._vae,
                width=self._width,
                height=self._height,
            )

        prompt_id = submit_workflow(
            workflow=workflow,
            server_url=self._server_url,
        )

        history_entry = wait_for_completion(
            prompt_id=prompt_id,
            server_url=self._server_url,
            poll_interval=self._config.poll_interval,
        )

        image_info = extract_output_image_info(history_entry, self._output_node_id)
        return download_image(
            image_info=image_info,
            server_url=self._server_url,
        )
