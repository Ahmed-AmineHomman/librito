"""Storybook JSON loading and saving."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from librito.models import StoryConstants, StoryScene, Storybook

_TOP_LEVEL_KEYS = {"title", "constants", "scenes"}
_CONSTANT_KEYS = {"style", "recurring_concepts"}
_SCENE_KEYS = {"text", "prompt", "image_path"}


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

    payload = json.loads(path.read_text(encoding="utf-8"))
    _require_exact_keys(payload, _TOP_LEVEL_KEYS, "story")

    constants_payload = payload["constants"]
    if not isinstance(constants_payload, dict):
        raise ValueError("story.constants must be an object.")

    scenes_payload = payload["scenes"]
    if not isinstance(scenes_payload, list):
        raise ValueError("story.scenes must be an array.")

    _require_exact_keys(constants_payload, _CONSTANT_KEYS, "constants")
    recurring_concepts = constants_payload["recurring_concepts"]
    if not isinstance(recurring_concepts, dict):
        raise ValueError("constants.recurring_concepts must be an object.")

    parsed_concepts: dict[str, str] = {}
    for key, value in recurring_concepts.items():
        if not isinstance(value, str):
            raise ValueError(f"constants.recurring_concepts.{key} must be a string.")
        parsed_concepts[str(key)] = value

    scenes: list[StoryScene] = []
    for index, scene_payload in enumerate(scenes_payload, start=1):
        if not isinstance(scene_payload, dict):
            raise ValueError(f"scene {index} must be an object.")
        _require_exact_keys(scene_payload, _SCENE_KEYS, f"scene {index}")
        scenes.append(
            StoryScene(
                text=_require_string(scene_payload["text"], f"scene {index}.text"),
                prompt=_require_string(scene_payload["prompt"], f"scene {index}.prompt"),
                image_path=_require_string(scene_payload["image_path"], f"scene {index}.image_path"),
            )
        )

    return Storybook(
        title=_require_string(payload["title"], "story.title"),
        constants=StoryConstants(
            style=_require_string(constants_payload["style"], "constants.style"),
            recurring_concepts=parsed_concepts,
        ),
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

    serialized = json.dumps(asdict(storybook), indent=4, ensure_ascii=False)
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
    """

    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string.")
    return value
