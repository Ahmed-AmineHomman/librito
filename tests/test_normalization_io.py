"""Tests for normalized story JSON I/O."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from librito.io import load_normalized_story, save_normalized_story

from tests.conftest import workspace_temporary_directory


class NormalizationIoTests(unittest.TestCase):
    """Validate normalized story parsing and serialization."""

    def test_load_normalized_story_reads_expected_structure(self) -> None:
        """A valid normalized story should parse into typed fields."""

        with workspace_temporary_directory() as temporary_directory:
            units_path = Path(temporary_directory) / "units.json"
            units_path.write_text(json.dumps(_sample_normalized_story_payload()), encoding="utf-8")

            normalized_story = load_normalized_story(units_path)

        self.assertEqual(len(normalized_story.units), 2)
        self.assertEqual(normalized_story.units[0].label, "unit-001")
        self.assertEqual(normalized_story.units[0].type, "narration")
        self.assertEqual(normalized_story.units[1].type, "dialogue_turn")

    def test_load_normalized_story_rejects_unexpected_top_level_keys(self) -> None:
        """Unexpected keys should fail validation."""

        payload = _sample_normalized_story_payload()
        payload["extra"] = "not allowed"

        with workspace_temporary_directory() as temporary_directory:
            units_path = Path(temporary_directory) / "units.json"
            units_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "exactly the keys"):
                load_normalized_story(units_path)

    def test_load_normalized_story_rejects_unknown_unit_type(self) -> None:
        """Unsupported unit types should fail validation."""

        payload = _sample_normalized_story_payload()
        payload["units"][1]["type"] = "description"

        with workspace_temporary_directory() as temporary_directory:
            units_path = Path(temporary_directory) / "units.json"
            units_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must be one of"):
                load_normalized_story(units_path)

    def test_save_normalized_story_persists_updated_unit_text(self) -> None:
        """Saving should write the current normalized story state back to JSON."""

        with workspace_temporary_directory() as temporary_directory:
            units_path = Path(temporary_directory) / "units.json"
            units_path.write_text(json.dumps(_sample_normalized_story_payload()), encoding="utf-8")
            normalized_story = load_normalized_story(units_path)
            normalized_story.units[1].text = '"No," Omar said. "What is it?"'

            save_normalized_story(normalized_story, units_path)
            stored_payload = json.loads(units_path.read_text(encoding="utf-8"))

        self.assertEqual(stored_payload["units"][1]["text"], '"No," Omar said. "What is it?"')


def _sample_normalized_story_payload() -> dict[str, object]:
    """Build a minimal valid normalized story payload.

    Returns
    -------
    dict[str, object]
        Serializable normalized story payload.
    """

    return {
        "units": [
            {
                "label": "unit-001",
                "type": "narration",
                "text": "Lina looked at the door.",
            },
            {
                "label": "unit-002",
                "type": "dialogue_turn",
                "text": '"Do you hear that?" she asked.',
            },
        ]
    }
