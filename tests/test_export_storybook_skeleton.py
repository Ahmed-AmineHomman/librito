"""Tests for the dummy storybook skeleton exporter."""

from __future__ import annotations

import json
import shutil
import unittest
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from librito.export_storybook_skeleton import build_storybook_skeleton_markdown, export_storybook_skeleton, main
from librito.models import StoryConstants, StoryScene, Storybook


class ExportStorybookSkeletonTests(unittest.TestCase):
    """Validate Markdown skeleton export behavior."""

    def test_build_storybook_skeleton_markdown_expands_scene_prompts(self) -> None:
        """The exported markdown should include fully built prompts per scene."""

        storybook = Storybook(
            title="Calmio",
            constants=StoryConstants(
                style="soft watercolor",
                recurring_concepts={"<CALMIO>": "A fluffy dog"},
            ),
            scenes=[
                StoryScene(
                    text="Calmio runs.",
                    prompt="<CALMIO> runs toward the river.",
                    image_path="",
                )
            ],
        )

        markdown = build_storybook_skeleton_markdown(storybook)

        self.assertIn("## Scene 01", markdown)
        self.assertIn("### Text", markdown)
        self.assertIn("Calmio runs.", markdown)
        self.assertIn("### Prompt", markdown)
        self.assertIn("Style: soft watercolor", markdown)
        self.assertIn("Scene: [A fluffy dog] runs toward the river.", markdown)
        self.assertIn("single scene", markdown)
        self.assertIn("no visible text", markdown)

    def test_export_storybook_skeleton_writes_output_file(self) -> None:
        """Exporting should write the expected markdown file."""

        with _workspace_temporary_directory() as temporary_directory:
            story_path = temporary_directory / "story.json"
            output_path = temporary_directory / "out" / "storybook.md"
            story_path.write_text(json.dumps(_sample_story_payload()), encoding="utf-8")

            export_storybook_skeleton(story_path, output_path)

            markdown = output_path.read_text(encoding="utf-8")

        self.assertIn("## Scene 01", markdown)
        self.assertIn("## Scene 02", markdown)
        self.assertIn("Scene: [A fluffy dog] runs across the street.", markdown)
        self.assertIn("Scene: [A fluffy dog] rests at home.", markdown)

    def test_main_accepts_named_parameters(self) -> None:
        """The command-line entrypoint should accept the required named flags."""

        with _workspace_temporary_directory() as temporary_directory:
            story_path = temporary_directory / "story.json"
            output_path = temporary_directory / "storybook.md"
            story_path.write_text(json.dumps(_sample_story_payload()), encoding="utf-8")

            exit_code = main(
                [
                    "--input-json",
                    str(story_path),
                    "--output-filepath",
                    str(output_path),
                ]
            )

            markdown = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("### Prompt", markdown)


def _sample_story_payload() -> dict[str, object]:
    """Build a minimal valid story payload for export tests.

    Returns
    -------
    dict[str, object]
        Serializable storybook payload.
    """

    return {
        "title": "Calmio",
        "constants": {
            "style": "soft watercolor",
            "recurring_concepts": {
                "<CALMIO>": "A fluffy dog",
            },
        },
        "scenes": [
            {
                "text": "Calmio runs.",
                "prompt": "<CALMIO> runs across the street.",
                "image_path": "",
            },
            {
                "text": "Calmio rests.",
                "prompt": "<CALMIO> rests at home.",
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
