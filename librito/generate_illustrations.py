"""Illustration generation orchestration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from librito.gemini_client import GeminiImageClient, GeminiImageClientConfig
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


def generate_story_illustrations(
    story_path: Path,
    client: GeminiImageClient | None = None,
    config: IllustrationGenerationConfig | None = None,
) -> None:
    """Generate all missing illustrations for a segmented story.

    Parameters
    ----------
    story_path:
        Path to the segmented ``story.json`` file.
    client:
        Optional preconfigured Gemini client used mainly for tests.
    config:
        Optional internal generation configuration.
    """

    config = config or IllustrationGenerationConfig()
    storybook = load_storybook(story_path)
    output_directory = story_path.parent / config.output_directory_name
    output_directory.mkdir(parents=True, exist_ok=True)

    if client is None:
        api_key = os.getenv(config.api_key_env_var)
        if not api_key:
            raise RuntimeError(f"Missing required environment variable: {config.api_key_env_var}.")
        client = GeminiImageClient(
            GeminiImageClientConfig(
                api_key=api_key,
                model=config.model,
                aspect_ratio=config.aspect_ratio,
                image_size=config.image_size,
                timeout_seconds=config.timeout_seconds,
            )
        )

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
