"""Schema-aware JSON loading and saving utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from librito.models import BookParts, Concept, IllustrationSpec, PageSpec, StoryScene, Storybook, Unit, Units

_STORYBOOK_TOP_LEVEL_KEYS = {"title", "author", "style", "style_image_path", "constraints", "concepts", "parts", "scenes"}
_STORYBOOK_PART_KEYS = {
    "front_cover",
    "front_endpaper",
    "opening_page",
    "frontispiece",
    "title_page",
    "closing_facing_page",
    "closing_illustration",
    "back_cover",
}
_STORYBOOK_SCENE_KEYS = {"label", "text", "prompt", "image_path"}
_CONCEPT_KEYS = {"tag", "description", "image_path", "scenes"}
_PAGE_KEYS = {"text", "illustration"}
_ILLUSTRATION_KEYS = {"prompt", "image_path", "text_mode"}
_UNITS_TOP_LEVEL_KEYS = {"units"}
_UNIT_KEYS = {"label", "type", "text"}
_ALLOWED_UNIT_TYPES = {"narration", "dialogue_turn"}
_ALLOWED_TEXT_MODES = {"overlay", "embedded"}


def load_storybook(path: Path) -> Storybook:
    """Load and validate a storybook JSON file.

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

    concepts = payload["concepts"]
    if not isinstance(concepts, list):
        raise ValueError("story.concepts must be an array.")

    parsed_concepts: list[Concept] = []
    seen_tags: set[str] = set()
    for position, concept_payload in enumerate(concepts, start=1):
        if not isinstance(concept_payload, dict):
            raise ValueError(f"concept {position} must be an object.")
        _require_exact_keys(concept_payload, _CONCEPT_KEYS, f"concept {position}")
        concept_tag = _require_non_empty_trimmed_string(concept_payload["tag"], f"concept {position}.tag")
        if concept_tag in seen_tags:
            raise ValueError(f"concept tags must be unique, duplicate found: {concept_tag}.")
        seen_tags.add(concept_tag)
        concept_scenes = concept_payload["scenes"]
        if not isinstance(concept_scenes, list):
            raise ValueError(f"concept {position}.scenes must be an array.")
        parsed_concepts.append(
            Concept(
                tag=concept_tag,
                description=_require_string(concept_payload["description"], f"concept {position}.description"),
                image_path=_require_string(concept_payload["image_path"], f"concept {position}.image_path"),
                scenes=[
                    _require_string(scene_label, f"concept {position}.scenes[{index}]")
                    for index, scene_label in enumerate(concept_scenes)
                ],
            )
        )

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
        author=_require_string(payload["author"], "story.author"),
        style=_require_string(payload["style"], "story.style"),
        style_image_path=_require_string(payload["style_image_path"], "story.style_image_path"),
        constraints=_require_string(payload["constraints"], "story.constraints"),
        concepts=parsed_concepts,
        parts=_parse_book_parts(payload["parts"]),
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
            "author": storybook.author,
            "style": storybook.style,
            "style_image_path": storybook.style_image_path,
            "constraints": storybook.constraints,
            "concepts": [
                {
                    "tag": concept.tag,
                    "description": concept.description,
                    "image_path": concept.image_path,
                    "scenes": list(concept.scenes),
                }
                for concept in storybook.concepts
            ],
            "parts": _serialize_book_parts(storybook.parts),
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


def load_units(path: Path) -> Units:
    """Load and validate a units JSON file.

    Parameters
    ----------
    path:
        Path to the ``units.json`` file.

    Returns
    -------
    Units
        Parsed units instance.

    Raises
    ------
    ValueError
        If the file content does not follow the expected structure.
    """

    payload = _load_json_object(path)
    _require_exact_keys(payload, _UNITS_TOP_LEVEL_KEYS, "units")

    units_payload = payload["units"]
    if not isinstance(units_payload, list):
        raise ValueError("units.units must be an array.")

    units: list[Unit] = []
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
            Unit(
                label=unit_label,
                type=unit_type,
                text=_require_non_empty_trimmed_string(unit_payload["text"], f"unit {position}.text"),
            )
        )

    return Units(units=units)


def save_units(units: Units, path: Path) -> None:
    """Persist a units artifact to JSON.

    Parameters
    ----------
    units:
        Units instance to serialize.
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
                for unit in units.units
            ]
        },
        path,
    )


def _parse_book_parts(payload: Any) -> BookParts:
    """Parse the ``parts`` section of a storybook."""

    if not isinstance(payload, dict):
        raise ValueError("story.parts must be an object.")
    _require_exact_keys(payload, _STORYBOOK_PART_KEYS, "story.parts")

    return BookParts(
        front_cover=_parse_required_page(payload["front_cover"], "story.parts.front_cover"),
        front_endpaper=_parse_optional_page(payload["front_endpaper"], "story.parts.front_endpaper"),
        opening_page=_parse_optional_page(payload["opening_page"], "story.parts.opening_page"),
        frontispiece=_parse_optional_page(payload["frontispiece"], "story.parts.frontispiece"),
        title_page=_parse_required_page(payload["title_page"], "story.parts.title_page"),
        closing_facing_page=_parse_optional_page(
            payload["closing_facing_page"],
            "story.parts.closing_facing_page",
        ),
        closing_illustration=_parse_optional_page(
            payload["closing_illustration"],
            "story.parts.closing_illustration",
        ),
        back_cover=_parse_required_page(payload["back_cover"], "story.parts.back_cover"),
    )


def _parse_required_page(payload: Any, context: str) -> PageSpec:
    """Parse a required page object."""

    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object.")
    return _parse_page(payload, context)


def _parse_optional_page(payload: Any, context: str) -> PageSpec | None:
    """Parse an optional page object."""

    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object or null.")
    return _parse_page(payload, context)


def _parse_page(payload: dict[str, Any], context: str) -> PageSpec:
    """Parse a page object."""

    _require_exact_keys(payload, _PAGE_KEYS, context)

    text_payload = payload["text"]
    if not isinstance(text_payload, list):
        raise ValueError(f"{context}.text must be an array.")
    text = [_require_string(item, f"{context}.text[{index}]") for index, item in enumerate(text_payload)]

    return PageSpec(
        text=text,
        illustration=_parse_optional_illustration(payload["illustration"], f"{context}.illustration"),
    )


def _parse_optional_illustration(payload: Any, context: str) -> IllustrationSpec | None:
    """Parse an optional illustration object."""

    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"{context} must be an object or null.")
    _require_exact_keys(payload, _ILLUSTRATION_KEYS, context)

    text_mode_value = payload["text_mode"]
    if text_mode_value is not None:
        text_mode = _require_non_empty_trimmed_string(text_mode_value, f"{context}.text_mode")
        if text_mode not in _ALLOWED_TEXT_MODES:
            raise ValueError(
                f"{context}.text_mode must be one of {sorted(_ALLOWED_TEXT_MODES)!r}, got {text_mode!r}."
            )
    else:
        text_mode = None

    return IllustrationSpec(
        prompt=_require_string(payload["prompt"], f"{context}.prompt"),
        image_path=_require_string(payload["image_path"], f"{context}.image_path"),
        text_mode=text_mode,
    )


def _serialize_book_parts(parts: BookParts) -> dict[str, object]:
    """Serialize the ``parts`` section of a storybook."""

    return {
        "front_cover": _serialize_page(parts.front_cover),
        "front_endpaper": _serialize_optional_page(parts.front_endpaper),
        "opening_page": _serialize_optional_page(parts.opening_page),
        "frontispiece": _serialize_optional_page(parts.frontispiece),
        "title_page": _serialize_page(parts.title_page),
        "closing_facing_page": _serialize_optional_page(parts.closing_facing_page),
        "closing_illustration": _serialize_optional_page(parts.closing_illustration),
        "back_cover": _serialize_page(parts.back_cover),
    }


def _serialize_optional_page(page: PageSpec | None) -> dict[str, object] | None:
    """Serialize an optional page object."""

    if page is None:
        return None
    return _serialize_page(page)


def _serialize_page(page: PageSpec) -> dict[str, object]:
    """Serialize a page object."""

    return {
        "text": list(page.text),
        "illustration": _serialize_optional_illustration(page.illustration),
    }


def _serialize_optional_illustration(illustration: IllustrationSpec | None) -> dict[str, object] | None:
    """Serialize an optional illustration object."""

    if illustration is None:
        return None
    return {
        "prompt": illustration.prompt,
        "image_path": illustration.image_path,
        "text_mode": illustration.text_mode,
    }


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
