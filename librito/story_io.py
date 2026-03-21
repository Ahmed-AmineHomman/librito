"""Storybook JSON loading and saving."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from librito.models import StoryScene, Storybook

_TOP_LEVEL_KEYS = {"title", "style", "constraints", "recurring_concepts", "scenes"}
_SCENE_KEYS = {"label", "text", "prompt", "image_path"}


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

    recurring_concepts = payload["recurring_concepts"]
    if not isinstance(recurring_concepts, dict):
        raise ValueError("story.recurring_concepts must be an object.")

    parsed_concepts: dict[str, str] = {}
    for key, value in recurring_concepts.items():
        if not isinstance(value, str):
            raise ValueError(f"recurring_concepts.{key} must be a string.")
        parsed_concepts[str(key)] = value

    scenes_payload = payload["scenes"]
    if not isinstance(scenes_payload, list):
        raise ValueError("story.scenes must be an array.")

    scenes: list[StoryScene] = []
    seen_labels: set[str] = set()
    for position, scene_payload in enumerate(scenes_payload, start=1):
        if not isinstance(scene_payload, dict):
            raise ValueError(f"scene {position} must be an object.")
        _require_exact_keys(scene_payload, _SCENE_KEYS, f"scene {position}")
        scene_label = _require_string(scene_payload["label"], f"scene {position}.label")
        if not scene_label or scene_label != scene_label.strip():
            raise ValueError(f"scene {position}.label must be a non-empty trimmed string.")
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

    serialized = json.dumps(
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
