"""Tests for illustration generation orchestration."""

from __future__ import annotations

import json
import shutil
import unittest
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from PIL import Image

from librito.generate_illustrations import (
    IllustrationGenerationConfig,
    generate_story_illustrations,
)


class GenerateIllustrationsTests(unittest.TestCase):
    """Validate sequential generation and resume behavior."""

    def test_generate_story_illustrations_updates_story_and_writes_files(self) -> None:
        """Missing scene images should be generated and stored."""

        with _workspace_temporary_directory() as temporary_directory:
            story_path = Path(temporary_directory) / "story.json"
            story_path.write_text(json.dumps(_sample_story_payload()), encoding="utf-8")
            fake_client = _FakeGeminiClient(
                [
                    Image.new("RGB", (2, 2), color="red"),
                    Image.new("RGB", (2, 2), color="blue"),
                ]
            )

            generate_story_illustrations(
                story_path,
                client=fake_client,
                config=IllustrationGenerationConfig(),
            )

            stored_payload = json.loads(story_path.read_text(encoding="utf-8"))
            with Image.open(story_path.parent / "illustrations" / "scene-001.png") as first_image:
                first_image_size = first_image.size
            with Image.open(story_path.parent / "illustrations" / "scene-002.png") as second_image:
                second_image_size = second_image.size

        self.assertEqual(len(fake_client.prompts), 2)
        self.assertEqual(stored_payload["scenes"][0]["image_path"], "illustrations/scene-001.png")
        self.assertEqual(stored_payload["scenes"][1]["image_path"], "illustrations/scene-002.png")
        self.assertEqual(first_image_size, (2, 2))
        self.assertEqual(second_image_size, (2, 2))

    def test_generate_story_illustrations_skips_existing_scene_images(self) -> None:
        """Existing images should not be regenerated."""

        with _workspace_temporary_directory() as temporary_directory:
            story_directory = Path(temporary_directory)
            illustrations_directory = story_directory / "illustrations"
            illustrations_directory.mkdir()
            existing_image_path = illustrations_directory / "scene-001.png"
            existing_image_path.write_bytes(b"existing")

            payload = _sample_story_payload()
            payload["scenes"][0]["image_path"] = "illustrations/scene-001.png"
            story_path = story_directory / "story.json"
            story_path.write_text(json.dumps(payload), encoding="utf-8")

            fake_client = _FakeGeminiClient([Image.new("RGB", (2, 2), color="blue")])

            generate_story_illustrations(
                story_path,
                client=fake_client,
                config=IllustrationGenerationConfig(),
            )

            stored_payload = json.loads(story_path.read_text(encoding="utf-8"))

        self.assertEqual(len(fake_client.prompts), 1)
        self.assertEqual(stored_payload["scenes"][0]["image_path"], "illustrations/scene-001.png")
        self.assertEqual(stored_payload["scenes"][1]["image_path"], "illustrations/scene-002.png")


class _FakeGeminiClient:
    """Minimal test double for the Gemini client."""

    def __init__(self, generated_images: list[Image.Image]) -> None:
        """Store predetermined images.

        Parameters
        ----------
        generated_images:
            Images returned in successive calls.
        """

        self._generated_images = generated_images
        self.prompts: list[str] = []

    def generate_image(self, prompt: str) -> Image.Image:
        """Return the next predetermined image.

        Parameters
        ----------
        prompt:
            Prompt requested by the generator.

        Returns
        -------
        Image.Image
            Next generated image.
        """

        self.prompts.append(prompt)
        return self._generated_images.pop(0)


def _sample_story_payload() -> dict[str, object]:
    """Build a valid two-scene story payload.

    Returns
    -------
    dict[str, object]
        Serializable story payload.
    """

    return {
        "title": "Calmio",
        "constants": {
            "style": "soft watercolor",
            "recurring_concepts": {
                "<CALMIO>": "A fluffy dog",
                "<RIVER>": "A bright river",
            },
        },
        "scenes": [
            {
                "text": "Calmio runs.",
                "prompt": "<CALMIO> runs toward <RIVER>.",
                "image_path": "",
            },
            {
                "text": "Calmio rests.",
                "prompt": "<CALMIO> rests beside <RIVER>.",
                "image_path": "",
            },
        ],
    }


@contextmanager
def _workspace_temporary_directory() -> Path:
    """Create a temporary directory inside the repository workspace.

    Yields
    ------
    Path
        Temporary directory rooted in the current workspace.
    """

    base_directory = Path.cwd() / ".tmp-tests"
    temporary_directory = base_directory / uuid4().hex
    temporary_directory.mkdir(parents=True, exist_ok=False)
    try:
        yield temporary_directory
    finally:
        shutil.rmtree(temporary_directory, ignore_errors=True)
