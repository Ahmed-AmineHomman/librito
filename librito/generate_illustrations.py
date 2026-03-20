"""Illustration generation orchestration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from librito.image_clients import ImageClient
from librito.image_clients.gemini import GeminiImageClient, GeminiImageClientConfig
from librito.image_clients.mock import MockImageClient, MockImageClientConfig
from librito.prompt_builder import build_scene_prompt
from librito.story_io import load_storybook, save_storybook


@dataclass(frozen=True, slots=True)
class IllustrationGenerationConfig:
    """Internal configuration for the illustration generation process.

    Parameters
    ----------
    model:
        Gemini image generation model.
    aspect_ratio:
        Target image aspect ratio.
    image_size:
        Target image size.
    timeout_seconds:
        HTTP timeout in seconds.
    output_directory_name:
        Subdirectory used to store generated illustrations.
    api_key_env_var:
        Environment variable holding the Gemini API key.
    """

    model: str = "gemini-3.1-flash-image-preview"
    aspect_ratio: str = "1:1"
    image_size: str = "1K"
    timeout_seconds: float = 60.0
    output_directory_name: str = "illustrations"
    api_key_env_var: str = "GEMINI_API_KEY"


def _build_default_client(
    config: IllustrationGenerationConfig,
    *,
    mock: bool = False,
) -> ImageClient:
    """Build the default image generation client.

    Parameters
    ----------
    config:
        Generation configuration.
    mock:
        When ``True``, return a mock client that produces pixel-noise images
        instead of calling a real API.

    Returns
    -------
    ImageClient
        Ready-to-use image generation client.
    """

    if mock:
        return MockImageClient(
            MockImageClientConfig(
                aspect_ratio=config.aspect_ratio,
                image_size=config.image_size,
            )
        )

    api_key = os.getenv(config.api_key_env_var)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {config.api_key_env_var}.")
    return GeminiImageClient(
        GeminiImageClientConfig(
            api_key=api_key,
            model=config.model,
            aspect_ratio=config.aspect_ratio,
            image_size=config.image_size,
            timeout_seconds=config.timeout_seconds,
        )
    )


def generate_story_illustrations(
    story_path: Path,
    client: ImageClient | None = None,
    config: IllustrationGenerationConfig | None = None,
    *,
    mock: bool = False,
) -> None:
    """Generate all missing illustrations for a segmented story.

    Parameters
    ----------
    story_path:
        Path to the segmented ``story.json`` file.
    client:
        Optional preconfigured image client used mainly for tests.
    config:
        Optional internal generation configuration.
    mock:
        When ``True`` and no *client* is provided, use the mock image client
        instead of the real Gemini client.
    """

    config = config or IllustrationGenerationConfig()
    storybook = load_storybook(story_path)
    output_directory = story_path.parent / config.output_directory_name
    output_directory.mkdir(parents=True, exist_ok=True)

    if client is None:
        client = _build_default_client(config, mock=mock)

    for scene in storybook.scenes:
        if scene.image_path and (story_path.parent / scene.image_path).exists():
            continue

        prompt = build_scene_prompt(
            storybook,
            scene,
        )
        generated_image = client.generate_image(prompt)
        output_path = output_directory / f"scene-{scene.index:03d}.png"
        generated_image.save(output_path)
        scene.image_path = output_path.relative_to(story_path.parent).as_posix()
        save_storybook(storybook, story_path)
