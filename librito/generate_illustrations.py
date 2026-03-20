"""Illustration generation entrypoint."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

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

    for index, scene in enumerate(storybook.scenes, start=1):
        if scene.image_path and (story_path.parent / scene.image_path).exists():
            continue

        prompt = build_scene_prompt(
            storybook,
            scene,
        )
        generated_image = client.generate_image(prompt)
        output_path = output_directory / f"scene-{index:03d}.png"
        generated_image.save(output_path)
        scene.image_path = output_path.relative_to(story_path.parent).as_posix()
        save_storybook(storybook, story_path)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the illustration generation module entrypoint.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    int
        Process exit status.
    """

    parser = argparse.ArgumentParser(description="Generate illustrations for a segmented storybook.")
    parser.add_argument("story_path", type=Path, help="Path to the story JSON file.")
    arguments = parser.parse_args(argv)
    generate_story_illustrations(arguments.story_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
