"""Tests for the storybook skeleton exporter."""

from __future__ import annotations

import json
import shutil
import unittest
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from analyse_segmentation import (
    build_anchor_occurrence_report,
    build_storybook_skeleton_markdown,
    count_anchor_occurrences,
    export_storybook_skeleton,
    main,
)
from librito.models import StoryScene, Storybook


class ExportStorybookSkeletonTests(unittest.TestCase):
    """Validate Markdown skeleton export behavior."""

    def test_count_anchor_occurrences_scans_all_story_scenes(self) -> None:
        """Anchor occurrence counts should cover the full storybook."""

        storybook = Storybook(
            title="Calmio",
            style="soft watercolor",
            recurring_concepts={
                "<CALMIO>": "A fluffy dog",
                "<RIVER>": "A clear river",
                "<FLOWER>": "A yellow flower",
            },
            scenes=[
                StoryScene(
                    index=1,
                    text="Scene one.",
                    prompt="<CALMIO> runs by the <RIVER>.",
                    image_path="",
                ),
                StoryScene(
                    index=2,
                    text="Scene two.",
                    prompt="<CALMIO> smells a <FLOWER> near the <RIVER>.",
                    image_path="",
                ),
            ],
        )

        counts = count_anchor_occurrences(storybook)

        self.assertEqual(
            counts,
            {
                "<CALMIO>": 2,
                "<FLOWER>": 1,
                "<RIVER>": 2,
            },
        )

    def test_build_anchor_occurrence_report_warns_on_single_use_anchor(self) -> None:
        """The scan report should warn when at least one anchor appears once."""

        storybook = Storybook(
            title="Calmio",
            style="soft watercolor",
            recurring_concepts={
                "<CALMIO>": "A fluffy dog",
                "<FLOWER>": "A yellow flower",
            },
            scenes=[
                StoryScene(
                    index=1,
                    text="Scene one.",
                    prompt="<CALMIO> smells a <FLOWER>.",
                    image_path="",
                ),
                StoryScene(
                    index=2,
                    text="Scene two.",
                    prompt="<CALMIO> rests.",
                    image_path="",
                ),
            ],
        )

        report = build_anchor_occurrence_report(storybook)

        self.assertIn("Anchor occurrences:", report)
        self.assertIn("- <CALMIO>: 2", report)
        self.assertIn("- <FLOWER>: 1", report)
        self.assertIn("WARNING: single-use anchors detected: <FLOWER>", report)

    def test_build_storybook_skeleton_markdown_expands_anchors(self) -> None:
        """The exported markdown should include anchor-expanded prompts per scene."""

        storybook = Storybook(
            title="Calmio",
            style="soft watercolor",
            recurring_concepts={"<CALMIO>": "A fluffy dog"},
            scenes=[
                StoryScene(
                    index=1,
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
        self.assertIn("[A fluffy dog] runs toward the river.", markdown)
        self.assertNotIn("Style:", markdown)
        self.assertNotIn("Constraints:", markdown)

    def test_build_storybook_skeleton_markdown_filters_by_scene_index(self) -> None:
        """Only scenes whose index is in the provided list should appear."""

        storybook = Storybook(
            title="Calmio",
            style="soft watercolor",
            recurring_concepts={"<CALMIO>": "A fluffy dog"},
            scenes=[
                StoryScene(index=1, text="Scene one.", prompt="<CALMIO> runs.", image_path=""),
                StoryScene(index=2, text="Scene two.", prompt="<CALMIO> rests.", image_path=""),
                StoryScene(index=3, text="Scene three.", prompt="<CALMIO> sleeps.", image_path=""),
            ],
        )

        markdown = build_storybook_skeleton_markdown(storybook, scene_indexes=[1, 3])

        self.assertIn("## Scene 01", markdown)
        self.assertNotIn("## Scene 02", markdown)
        self.assertIn("## Scene 03", markdown)

    def test_export_storybook_skeleton_writes_output_file(self) -> None:
        """Exporting should write the expected markdown file when output path is given."""

        with _workspace_temporary_directory() as temporary_directory:
            story_path = temporary_directory / "story.json"
            output_path = temporary_directory / "out" / "storybook.md"
            story_path.write_text(json.dumps(_sample_story_payload()), encoding="utf-8")

            stdout_buffer = StringIO()
            with patch("sys.stdout", stdout_buffer):
                export_storybook_skeleton(story_path, output_path)

            markdown = output_path.read_text(encoding="utf-8")
            stdout_text = stdout_buffer.getvalue()

        self.assertIn("Anchor occurrences:", stdout_text)
        self.assertIn("- <CALMIO>: 2", stdout_text)
        self.assertIn("## Scene 01", markdown)
        self.assertIn("## Scene 02", markdown)
        self.assertIn("[A fluffy dog] runs across the street.", markdown)
        self.assertIn("[A fluffy dog] rests at home.", markdown)
        self.assertNotIn("Anchor occurrences:", markdown)

    def test_main_accepts_named_parameters(self) -> None:
        """The command-line entrypoint should accept the required named flags."""

        with _workspace_temporary_directory() as temporary_directory:
            story_path = temporary_directory / "story.json"
            output_path = temporary_directory / "storybook.md"
            story_path.write_text(json.dumps(_sample_story_payload()), encoding="utf-8")

            stdout_buffer = StringIO()
            with patch("sys.stdout", stdout_buffer):
                exit_code = main(
                    [
                        "--storybook",
                        str(story_path),
                        "--output-file",
                        str(output_path),
                    ]
                )

            markdown = output_path.read_text(encoding="utf-8")
            stdout_text = stdout_buffer.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Anchor occurrences:", stdout_text)
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
            },
            {
                "index": 2,
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
