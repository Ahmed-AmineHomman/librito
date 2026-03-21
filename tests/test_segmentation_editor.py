"""Tests for the filesystem-backed segmentation editor."""

from __future__ import annotations

import json
import shutil
import unittest
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from librito.segmentation.editor import StorybookEditor
from librito.segmentation.session import SegmentationSession


class StorybookEditorTests(unittest.TestCase):
    """Validate draft editing and prompt-consistency helpers."""

    def test_add_scene_generates_default_label_and_respects_position(self) -> None:
        """New scenes should receive default labels and 1-based insertions."""

        with _workspace_temporary_directory() as temporary_directory:
            session = _build_session(temporary_directory)
            editor = StorybookEditor(session)

            first_label = editor.add_scene(
                text="First scene.",
                prompt="A calm opening.",
            )
            second_label = editor.add_scene(
                text="Inserted scene.",
                prompt="A new moment.",
                position=1,
            )

            scenes = editor.list_scenes()

        self.assertEqual(first_label, "scene-001")
        self.assertEqual(second_label, "scene-002")
        self.assertEqual([scene["label"] for scene in scenes], ["scene-002", "scene-001"])

    def test_rename_concept_updates_prompt_references(self) -> None:
        """Renaming a concept should update scene prompt references."""

        with _workspace_temporary_directory() as temporary_directory:
            session = _build_session(temporary_directory)
            editor = StorybookEditor(session)
            editor.add_concept("<DOG>", "A fluffy dog")
            editor.add_scene(
                label="opening",
                text="Calmio runs.",
                prompt="<DOG> runs through the field.",
            )

            editor.rename_concept("<DOG>", "<CALMIO>")

            scenes = editor.list_scenes()
            concepts = editor.list_concepts()

        self.assertEqual(scenes[0]["prompt"], "<CALMIO> runs through the field.")
        self.assertEqual(concepts, {"<CALMIO>": "A fluffy dog"})

    def test_check_prompt_consistency_reports_current_findings(self) -> None:
        """Undefined, unused, and single-scene anchors should be reported."""

        with _workspace_temporary_directory() as temporary_directory:
            session = _build_session(temporary_directory)
            editor = StorybookEditor(session)
            editor.add_concept("<DOG>", "A fluffy dog")
            editor.add_concept("<RIVER>", "A bright river")
            editor.add_scene(
                label="opening",
                text="Calmio runs.",
                prompt="<DOG> runs beside <MISSING>.",
            )

            report = editor.check_prompt_consistency()

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["undefined_anchors"], [{"scene_label": "opening", "anchor": "<MISSING>"}])
        self.assertEqual(report["unused_concepts"], ["<RIVER>"])
        self.assertEqual(report["single_scene_anchors"], [{"anchor": "<DOG>", "scene_labels": ["opening"]}])

    def test_export_storybook_requires_prompt_consistency(self) -> None:
        """Export should fail until prompt-consistency findings are resolved."""

        with _workspace_temporary_directory() as temporary_directory:
            session = _build_session(temporary_directory)
            editor = StorybookEditor(session)
            editor.set_title("Calmio")
            editor.set_style("soft watercolor")
            editor.add_concept("<DOG>", "A fluffy dog")
            editor.add_scene(
                label="opening",
                text="Calmio runs.",
                prompt="<DOG> runs.",
            )

            with self.assertRaisesRegex(ValueError, "Prompt consistency validation failed"):
                editor.export_storybook()

            editor.add_scene(
                label="ending",
                text="Calmio rests.",
                prompt="<DOG> rests.",
            )
            export_path = editor.export_storybook()
            exported_payload = json.loads(export_path.read_text(encoding="utf-8"))

        self.assertEqual(exported_payload["title"], "Calmio")
        self.assertEqual([scene["label"] for scene in exported_payload["scenes"]], ["opening", "ending"])


def _build_session(base_directory: Path) -> SegmentationSession:
    """Build a test session rooted in a temporary workspace directory.

    Parameters
    ----------
    base_directory:
        Temporary workspace directory.

    Returns
    -------
    SegmentationSession
        Filesystem-backed test session.
    """

    story_path = base_directory / "story.md"
    story_path.write_text("Calmio runs by the river.", encoding="utf-8")
    return SegmentationSession(
        story_path=story_path,
        draft_path=base_directory / "story.segmentation.draft.json",
        export_path=base_directory / "story.json",
    )


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
