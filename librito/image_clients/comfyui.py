"""ComfyUI API client for image generation."""

from __future__ import annotations

import copy
import io
import json
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

_RESOURCE_DIRECTORY = resources.files("librito.resources")
_WORKFLOW_FILENAME = "workflow_checkpoint.json"

# Node IDs in workflow_checkpoint.json
_SAMPLER_NODE_ID = "3"
_CHECKPOINT_NODE_ID = "4"
_LATENT_NODE_ID = "5"
_PROMPT_NODE_ID = "6"
_OUTPUT_NODE_ID = "9"

_DEFAULT_SERVER_URL = "http://127.0.0.1:8188"
_SERVER_URL_ENV_VAR = "COMFYUI_API_URL"


@dataclass(frozen=True, slots=True)
class ComfyUIImageClientConfig:
    """Configuration for ComfyUI image generation requests.

    Parameters
    ----------
    model:
        Checkpoint filename as known by ComfyUI (e.g.
        ``"sd1/arthemycomics.safetensors"``).
    server_url:
        Base URL of the ComfyUI instance.  Falls back to the
        ``COMFYUI_API_URL`` environment variable, then to
        ``http://127.0.0.1:8188``.
    aspect_ratio:
        Requested image aspect ratio.
    image_size:
        Requested overall image resolution (``"1K"`` or ``"2K"``).
    poll_interval:
        Seconds between history polling requests.
    """

    model: str
    server_url: str = ""
    aspect_ratio: str = "1:1"
    image_size: str = "1K"
    poll_interval: float = 1.0

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

    url = f"{server_url}/object_info/CheckpointLoaderSimple"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise ComfyUIImageClientError(
            f"Failed to query available checkpoints from ComfyUI: {error}."
        ) from error

    try:
        return list(data["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0])
    except (KeyError, IndexError) as error:
        raise ComfyUIImageClientError(
            f"Unexpected checkpoint info response structure: {error}."
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


def resolve_model_name(model: str, server_url: str) -> str:
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

    Returns
    -------
    str
        The canonical checkpoint name recognised by the server.

    Raises
    ------
    ComfyUIImageClientError
        If the model cannot be found on the server.
    """

    available = _fetch_available_checkpoints(server_url)

    if model in available:
        return model

    normalized_input = _normalize_path(model)
    for candidate in available:
        if _normalize_path(candidate) == normalized_input:
            return candidate

    raise ComfyUIImageClientError(
        f"Model {model!r} not found on the ComfyUI server. "
        f"Available checkpoints: {available}"
    )


def _load_workflow_template() -> dict[str, Any]:
    """Load the default checkpoint workflow from package resources.

    Returns
    -------
    dict[str, Any]
        Parsed workflow JSON.
    """

    raw = _RESOURCE_DIRECTORY.joinpath(_WORKFLOW_FILENAME).read_text(encoding="utf-8")
    return json.loads(raw)


def prepare_workflow(
    workflow_template: dict[str, Any],
    prompt: str,
    model: str,
    width: int,
    height: int,
) -> dict[str, Any]:
    """Create a workflow copy with injected generation parameters.

    Parameters
    ----------
    workflow_template:
        Base workflow loaded from the resource file.
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
    workflow[_SAMPLER_NODE_ID]["inputs"]["seed"] = random.randint(0, 2**31 - 1)
    workflow[_CHECKPOINT_NODE_ID]["inputs"]["ckpt_name"] = model
    workflow[_LATENT_NODE_ID]["inputs"]["width"] = width
    workflow[_LATENT_NODE_ID]["inputs"]["height"] = height
    workflow[_PROMPT_NODE_ID]["inputs"]["text"] = prompt
    return workflow


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


def extract_output_image_info(history_entry: dict[str, Any]) -> dict[str, Any]:
    """Extract image metadata from the output node.

    Parameters
    ----------
    history_entry:
        History entry for a completed prompt.

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

    if _OUTPUT_NODE_ID not in outputs:
        raise ComfyUIImageClientError(
            f"No output found for node {_OUTPUT_NODE_ID}."
        )

    images = outputs[_OUTPUT_NODE_ID].get("images", [])
    if not images:
        raise ComfyUIImageClientError(
            f"No image found in output node {_OUTPUT_NODE_ID}."
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

    Loads the ``workflow_checkpoint.json`` template, injects prompt, model,
    and dimensions, submits the workflow via the ComfyUI REST API, then
    polls for the result and downloads the generated image.
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
        self._model = resolve_model_name(config.model, self._server_url)
        self._workflow_template = _load_workflow_template()

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

        workflow = prepare_workflow(
            workflow_template=self._workflow_template,
            prompt=prompt,
            model=self._model,
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

        image_info = extract_output_image_info(history_entry)
        return download_image(
            image_info=image_info,
            server_url=self._server_url,
        )
