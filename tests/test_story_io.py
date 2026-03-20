"""Tests for storybook JSON I/O."""

from __future__ import annotations

import json
import shutil
import unittest
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from librito.story_io import load_storybook, save_storybook


class StoryIoTests(unittest.TestCase):
    """Validate storybook parsing and serialization."""

    def test_load_storybook_reads_expected_structure(self) -> None:
        """A valid storybook should parse into typed fields."""

        with _workspace_temporary_directory() as temporary_directory:
            story_path = Path(temporary_directory) / "story.json"
            story_path.write_text(json.dumps(_sample_story_payload()), encoding="utf-8")

            storybook = load_storybook(story_path)

        self.assertEqual(storybook.title, "Calmio")
        self.assertEqual(storybook.style, "soft watercolor")
        self.assertEqual(storybook.constraints, "")
        self.assertEqual(storybook.scenes[0].index, 1)
        self.assertEqual(storybook.scenes[0].image_path, "")

    def test_load_storybook_rejects_unexpected_top_level_keys(self) -> None:
        """Unexpected keys should fail validation."""

        payload = _sample_story_payload()
        payload["extra"] = "not allowed"

        with _workspace_temporary_directory() as temporary_directory:
            story_path = Path(temporary_directory) / "story.json"
            story_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "exactly the keys"):
                load_storybook(story_path)

    def test_save_storybook_persists_updated_image_path(self) -> None:
        """Saving should write the current story state back to JSON."""

        with _workspace_temporary_directory() as temporary_directory:
            story_path = Path(temporary_directory) / "story.json"
            story_path.write_text(json.dumps(_sample_story_payload()), encoding="utf-8")
            storybook = load_storybook(story_path)
            storybook.scenes[0].image_path = "illustrations/scene-001.png"

            save_storybook(storybook, story_path)
            stored_payload = json.loads(story_path.read_text(encoding="utf-8"))

        self.assertEqual(stored_payload["scenes"][0]["image_path"], "illustrations/scene-001.png")


def _sample_story_payload() -> dict[str, object]:
    """Build a minimal valid story payload.

    Returns
    -------
    dict[str, object]
        Serializable storybook payload.
    """

    return {
        "title": "Calmio",
        "style": "soft watercolor",
        "constraints": "",
        "recurring_concepts": {
            "<CALMIO>": "A fluffy dog",
        },
        "scenes": [
            {
                "index": 1,
                "text": "Calmio runs.",
                "prompt": "<CALMIO> runs across the street.",
                "image_path": "",
            }
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
