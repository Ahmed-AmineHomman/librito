"""Normalized story JSON loading and saving."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from librito.models import NormalizedStory, NormalizedUnit

_TOP_LEVEL_KEYS = {"units"}
_UNIT_KEYS = {"label", "type", "text"}
_ALLOWED_UNIT_TYPES = {"narration", "dialogue_turn"}


def load_normalized_story(path: Path) -> NormalizedStory:
    """Load and validate a normalized story JSON file.

    Parameters
    ----------
    path:
        Path to the ``units.json`` file.

    Returns
    -------
    NormalizedStory
        Parsed normalized story instance.

    Raises
    ------
    ValueError
        If the file content does not follow the expected structure.
    """

    payload = json.loads(path.read_text(encoding="utf-8"))
    _require_exact_keys(payload, _TOP_LEVEL_KEYS, "normalized_story")

    units_payload = payload["units"]
    if not isinstance(units_payload, list):
        raise ValueError("normalized_story.units must be an array.")

    units: list[NormalizedUnit] = []
    seen_labels: set[str] = set()
    for position, unit_payload in enumerate(units_payload, start=1):
        if not isinstance(unit_payload, dict):
            raise ValueError(f"unit {position} must be an object.")
        _require_exact_keys(unit_payload, _UNIT_KEYS, f"unit {position}")
        unit_label = _require_non_empty_trimmed_string(unit_payload["label"], f"unit {position}.label")
        if unit_label in seen_labels:
            raise ValueError(f"unit labels must be unique, duplicate found: {unit_label}.")
        seen_labels.add(unit_label)

        unit_type = _require_non_empty_trimmed_string(unit_payload["type"], f"unit {position}.type")
        if unit_type not in _ALLOWED_UNIT_TYPES:
            raise ValueError(
                f"unit {position}.type must be one of {sorted(_ALLOWED_UNIT_TYPES)!r}, got {unit_type!r}."
            )

        units.append(
            NormalizedUnit(
                label=unit_label,
                type=unit_type,
                text=_require_non_empty_trimmed_string(unit_payload["text"], f"unit {position}.text"),
            )
        )

    return NormalizedStory(units=units)


def save_normalized_story(normalized_story: NormalizedStory, path: Path) -> None:
    """Persist a normalized story to JSON.

    Parameters
    ----------
    normalized_story:
        Normalized story instance to serialize.
    path:
        Destination JSON path.
    """

    serialized = json.dumps(
        {
            "units": [
                {
                    "label": unit.label,
                    "type": unit.type,
                    "text": unit.text,
                }
                for unit in normalized_story.units
            ]
        },
        indent=4,
        ensure_ascii=False,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{serialized}\n", encoding="utf-8")


def _require_exact_keys(payload: dict[str, Any], expected_keys: set[str], context: str) -> None:
    """Ensure a mapping contains exactly the expected keys.

    Parameters
    ----------
    payload:
        Mapping to validate.
    expected_keys:
        Allowed key set.
    context:
        Human-readable validation context.

    Raises
    ------
    ValueError
        If the keys do not match the expected set.
    """

    actual_keys = set(payload)
    if actual_keys != expected_keys:
        raise ValueError(
            f"{context} must contain exactly the keys {sorted(expected_keys)!r}, "
            f"got {sorted(actual_keys)!r}."
        )


def _require_non_empty_trimmed_string(value: Any, context: str) -> str:
    """Ensure a value is a non-empty trimmed string.

    Parameters
    ----------
    value:
        Value to validate.
    context:
        Human-readable validation context.

    Returns
    -------
    str
        Validated string value.

    Raises
    ------
    ValueError
        If the value is not a valid non-empty trimmed string.
    """

    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string.")
    if not value or value != value.strip():
        raise ValueError(f"{context} must be a non-empty trimmed string.")
    return value
