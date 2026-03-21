"""Illustration generation orchestration."""

from __future__ import annotations

import os
from pathlib import Path

from librito.image_clients import ImageClient
from librito.image_clients.gemini import GeminiImageClient, GeminiImageClientConfig
from librito.image_clients.mock import MockImageClient, MockImageClientConfig
from librito.prompt_builder import build_scene_prompt
from librito.story_io import load_storybook, save_storybook

_OUTPUT_DIRECTORY_NAME = "illustrations"
_GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"


def _build_default_client(*, mock: bool = False) -> ImageClient:
    """Build the default image generation client.

    Parameters
    ----------
    mock:
        When ``True``, return a mock client that produces pixel-noise images
        instead of calling a real API.

    Returns
    -------
    ImageClient
        Ready-to-use image generation client.
    """

    if mock:
        return MockImageClient()

    api_key = os.getenv(_GEMINI_API_KEY_ENV_VAR)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {_GEMINI_API_KEY_ENV_VAR}.")
    return GeminiImageClient(GeminiImageClientConfig(api_key=api_key))


def generate_story_illustrations(
    story_path: Path,
    client: ImageClient | None = None,
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
    mock:
        When ``True`` and no *client* is provided, use the mock image client
        instead of the real Gemini client.
    """

    storybook = load_storybook(story_path)
    output_directory = story_path.parent / _OUTPUT_DIRECTORY_NAME
    output_directory.mkdir(parents=True, exist_ok=True)

    if client is None:
        client = _build_default_client(mock=mock)

    for scene_position, scene in enumerate(storybook.scenes, start=1):
        if scene.image_path and (story_path.parent / scene.image_path).exists():
            continue

        prompt = build_scene_prompt(
            storybook,
            scene,
        )
        generated_image = client.generate_image(prompt)
        output_path = output_directory / f"scene-{scene_position:03d}.png"
        generated_image.save(output_path)
        scene.image_path = output_path.relative_to(story_path.parent).as_posix()
        save_storybook(storybook, story_path)
