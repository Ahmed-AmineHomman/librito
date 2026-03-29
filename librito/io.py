"""Schema-aware JSON loading and saving utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from librito.models import NormalizedStory, StoryScene, StoryUnit, Storybook

_STORYBOOK_TOP_LEVEL_KEYS = {"title", "style", "constraints", "recurring_concepts", "scenes"}
_STORYBOOK_SCENE_KEYS = {"label", "text", "prompt", "image_path"}
_NORMALIZED_STORY_TOP_LEVEL_KEYS = {"units"}
_NORMALIZED_STORY_UNIT_KEYS = {"label", "type", "text"}
_ALLOWED_UNIT_TYPES = {"narration", "dialogue_turn"}


def load_storybook(path: Path) -> Storybook:
    """Load and validate a segmented storybook JSON file.

    Parameters
    ----------
    path:
        Path to the ``story.json`` file.

    Returns
    -------
    Storybook
        Parsed storybook instance.

    Raises
    ------
    ValueError
        If the file content does not follow the expected structure.
    """

    payload = _load_json_object(path)
    _require_exact_keys(payload, _STORYBOOK_TOP_LEVEL_KEYS, "story")

    recurring_concepts = payload["recurring_concepts"]
    if not isinstance(recurring_concepts, dict):
        raise ValueError("story.recurring_concepts must be an object.")

    parsed_concepts: dict[str, str] = {}
    for key, value in recurring_concepts.items():
        parsed_concepts[str(key)] = _require_string(value, f"recurring_concepts.{key}")

    scenes_payload = payload["scenes"]
    if not isinstance(scenes_payload, list):
        raise ValueError("story.scenes must be an array.")

    scenes: list[StoryScene] = []
    seen_labels: set[str] = set()
    for position, scene_payload in enumerate(scenes_payload, start=1):
        if not isinstance(scene_payload, dict):
            raise ValueError(f"scene {position} must be an object.")
        _require_exact_keys(scene_payload, _STORYBOOK_SCENE_KEYS, f"scene {position}")
        scene_label = _require_non_empty_trimmed_string(scene_payload["label"], f"scene {position}.label")
        if scene_label in seen_labels:
            raise ValueError(f"scene labels must be unique, duplicate found: {scene_label}.")
        seen_labels.add(scene_label)
        scenes.append(
            StoryScene(
                label=scene_label,
                text=_require_string(scene_payload["text"], f"scene {position}.text"),
                prompt=_require_string(scene_payload["prompt"], f"scene {position}.prompt"),
                image_path=_require_string(scene_payload["image_path"], f"scene {position}.image_path"),
            )
        )

    return Storybook(
        title=_require_string(payload["title"], "story.title"),
        style=_require_string(payload["style"], "story.style"),
        constraints=_require_string(payload["constraints"], "story.constraints"),
        recurring_concepts=parsed_concepts,
        scenes=scenes,
    )


def save_storybook(storybook: Storybook, path: Path) -> None:
    """Persist a storybook to JSON.

    Parameters
    ----------
    storybook:
        Storybook instance to serialize.
    path:
        Destination JSON path.
    """

    _write_json(
        {
            "title": storybook.title,
            "style": storybook.style,
            "constraints": storybook.constraints,
            "recurring_concepts": storybook.recurring_concepts,
            "scenes": [
                {
                    "label": scene.label,
                    "text": scene.text,
                    "prompt": scene.prompt,
                    "image_path": scene.image_path,
                }
                for scene in storybook.scenes
            ],
        },
        path,
    )


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

    payload = _load_json_object(path)
    _require_exact_keys(payload, _NORMALIZED_STORY_TOP_LEVEL_KEYS, "normalized_story")

    units_payload = payload["units"]
    if not isinstance(units_payload, list):
        raise ValueError("normalized_story.units must be an array.")

    units: list[StoryUnit] = []
    seen_labels: set[str] = set()
    for position, unit_payload in enumerate(units_payload, start=1):
        if not isinstance(unit_payload, dict):
            raise ValueError(f"unit {position} must be an object.")
        _require_exact_keys(unit_payload, _NORMALIZED_STORY_UNIT_KEYS, f"unit {position}")
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
            StoryUnit(
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

    _write_json(
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
        path,
    )


def _load_json_object(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk.

    Parameters
    ----------
    path:
        Path to the JSON file.

    Returns
    -------
    dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    ValueError
        If the payload is not a JSON object.
    """

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _write_json(payload: dict[str, Any], path: Path) -> None:
    """Serialize a JSON object to disk with standard formatting.

    Parameters
    ----------
    payload:
        JSON-serializable mapping to persist.
    path:
        Destination JSON path.
    """

    serialized = json.dumps(payload, indent=4, ensure_ascii=False)
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


def _require_string(value: Any, context: str) -> str:
    """Ensure a value is a string.

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
        If the value is not a string.
    """

    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string.")
    return value


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

    string_value = _require_string(value, context)
    if not string_value or string_value != string_value.strip():
        raise ValueError(f"{context} must be a non-empty trimmed string.")
    return string_value
