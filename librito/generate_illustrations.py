"""Illustration generation orchestration."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from librito.image_clients import ImageClient
from librito.image_clients.comfyui import ComfyUIImageClient, ComfyUIImageClientConfig
from librito.image_clients.gemini import GeminiImageClient, GeminiImageClientConfig
from librito.image_clients.mock import MockImageClient, MockImageClientConfig
from librito.prompt_builder import build_scene_prompt
from librito.story_io import load_storybook, save_storybook

logger = logging.getLogger(__name__)

_OUTPUT_DIRECTORY_NAME = "illustrations"
_STORYBOOK_FILENAME = "story.json"
_GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"


def _build_default_client(
    *,
    mock: bool = False,
    provider: str = "gemini",
    checkpoint: str | None = None,
    diffusion_model: str | None = None,
    clip: str | None = None,
    vae: str | None = None,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
) -> ImageClient:
    """Build the default image generation client.

    Parameters
    ----------
    mock:
        When ``True``, return a mock client that produces pixel-noise images
        instead of calling a real API.
    provider:
        Image generation provider (``"gemini"`` or ``"comfyui"``).
    checkpoint:
        Checkpoint filename for the ComfyUI checkpoint workflow.
    diffusion_model:
        UNET model filename for the ComfyUI diffusion workflow.
    clip:
        CLIP model filename for the ComfyUI diffusion workflow.
    vae:
        VAE model filename for the ComfyUI diffusion workflow.
    aspect_ratio:
        Requested image aspect ratio.
    image_size:
        Requested overall image resolution (``"0.5K"``, ``"1K"``, or
        ``"2K"``).

    Returns
    -------
    ImageClient
        Ready-to-use image generation client.
    """

    if mock:
        logger.info("Using mock image client.")
        return MockImageClient(MockImageClientConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ))

    if provider == "comfyui":
        if not checkpoint and not (diffusion_model and clip and vae):
            raise RuntimeError(
                "ComfyUI provider requires either --checkpoint or all three of "
                "--diffusion-model, --clip, and --vae."
            )
        logger.info(
            "Using ComfyUI provider (%s mode).",
            "checkpoint" if checkpoint else "diffusion",
        )
        return ComfyUIImageClient(ComfyUIImageClientConfig(
            checkpoint=checkpoint or "",
            diffusion_model=diffusion_model or "",
            clip=clip or "",
            vae=vae or "",
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ))

    # Default: Gemini
    api_key = os.getenv(_GEMINI_API_KEY_ENV_VAR)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {_GEMINI_API_KEY_ENV_VAR}.")

    logger.info("Using Gemini provider.")
    config_kwargs: dict[str, str] = {
        "api_key": api_key,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
    }
    if checkpoint:
        config_kwargs["model"] = checkpoint

    return GeminiImageClient(GeminiImageClientConfig(**config_kwargs))


def generate_story_illustrations(
    story_directory: Path,
    client: ImageClient | None = None,
    *,
    mock: bool = False,
    provider: str = "gemini",
    checkpoint: str | None = None,
    diffusion_model: str | None = None,
    clip: str | None = None,
    vae: str | None = None,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
) -> None:
    """Generate all missing illustrations for a segmented story.

    Parameters
    ----------
    story_directory:
        Path to the story folder containing ``story.json``.
    client:
        Optional preconfigured image client used mainly for tests.
    mock:
        When ``True`` and no *client* is provided, use the mock image client
        instead of the real API.
    provider:
        Image generation provider (``"gemini"`` or ``"comfyui"``).
    checkpoint:
        Checkpoint filename for the ComfyUI checkpoint workflow.
    diffusion_model:
        UNET model filename for the ComfyUI diffusion workflow.
    clip:
        CLIP model filename for the ComfyUI diffusion workflow.
    vae:
        VAE model filename for the ComfyUI diffusion workflow.
    aspect_ratio:
        Requested image aspect ratio.
    image_size:
        Requested overall image resolution.
    """

    story_path = story_directory / _STORYBOOK_FILENAME
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)
    output_directory = story_directory / _OUTPUT_DIRECTORY_NAME
    output_directory.mkdir(parents=True, exist_ok=True)

    if client is None:
        client = _build_default_client(
            mock=mock,
            provider=provider,
            checkpoint=checkpoint,
            diffusion_model=diffusion_model,
            clip=clip,
            vae=vae,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )

    total_scenes = len(storybook.scenes)
    logger.info("Starting illustration generation for %d scene(s).", total_scenes)

    for scene_position, scene in enumerate(storybook.scenes, start=1):
        if scene.image_path and (story_directory / scene.image_path).exists():
            logger.info(
                "Scene %d/%d (%s): skipping (image already exists).",
                scene_position,
                total_scenes,
                scene.label,
            )
            continue

        logger.info(
            "Scene %d/%d (%s): generating illustration...",
            scene_position,
            total_scenes,
            scene.label,
        )
        prompt = build_scene_prompt(
            storybook,
            scene,
        )
        generated_image = client.generate_image(prompt)
        output_path = output_directory / f"scene-{scene_position:03d}.png"
        generated_image.save(output_path)
        scene.image_path = output_path.relative_to(story_directory).as_posix()
        save_storybook(storybook, story_path)
        logger.info(
            "Scene %d/%d (%s): saved to %s.",
            scene_position,
            total_scenes,
            scene.label,
            scene.image_path,
        )

    logger.info("Illustration generation complete.")
