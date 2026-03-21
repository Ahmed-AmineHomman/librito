"""Prompt-consistency checks and scene expansion helpers for segmentation."""

from __future__ import annotations

import re

from librito.models import StoryScene, Storybook
from librito.prompt_builder import build_scene_prompt, expand_prompt_anchors

_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")
_STRICT_ANCHOR_PATTERN = re.compile(r"^<[A-Z0-9_]+>$")


def is_valid_anchor_tag(tag: str) -> bool:
    """Check whether an anchor tag follows the canonical format.

    Parameters
    ----------
    tag:
        Candidate recurring concept tag.

    Returns
    -------
    bool
        ``True`` when the tag matches ``<NAME>`` with uppercase letters,
        digits, and underscores only.
    """

    return _STRICT_ANCHOR_PATTERN.fullmatch(tag) is not None


def count_concept_occurrences(storybook: Storybook) -> dict[str, dict[str, object]]:
    """Count recurring concept usage across the storybook.

    Parameters
    ----------
    storybook:
        Parsed storybook definition.

    Returns
    -------
    dict[str, dict[str, object]]
        Mapping from each defined anchor to its total token count, number of
        distinct scenes using it, and the ordered list of those scene labels.
    """

    counts: dict[str, dict[str, object]] = {
        anchor: {
            "occurrence_count": 0,
            "scene_count": 0,
            "scene_labels": [],
        }
        for anchor in sorted(storybook.recurring_concepts)
    }

    for scene in storybook.scenes:
        anchors_in_scene = _ANCHOR_PATTERN.findall(scene.prompt)
        unique_scene_anchors = set(anchors_in_scene)
        for anchor in anchors_in_scene:
            if anchor in counts:
                counts[anchor]["occurrence_count"] = int(counts[anchor]["occurrence_count"]) + 1
        for anchor in sorted(unique_scene_anchors):
            if anchor in counts:
                scene_labels = list(counts[anchor]["scene_labels"])
                scene_labels.append(scene.label)
                counts[anchor]["scene_labels"] = scene_labels
                counts[anchor]["scene_count"] = len(scene_labels)

    return counts


def check_prompt_consistency(storybook: Storybook) -> dict[str, object]:
    """Check prompt-consistency rules for a storybook.

    Parameters
    ----------
    storybook:
        Storybook to inspect.

    Returns
    -------
    dict[str, object]
        Plain dictionary describing prompt-consistency findings.
    """

    undefined_anchors: list[dict[str, str]] = []
    for scene in storybook.scenes:
        for anchor in sorted(set(_ANCHOR_PATTERN.findall(scene.prompt))):
            if anchor not in storybook.recurring_concepts:
                undefined_anchors.append(
                    {
                        "scene_label": scene.label,
                        "anchor": anchor,
                    }
                )

    counts = count_concept_occurrences(storybook)
    unused_concepts = [
        anchor
        for anchor, entry in counts.items()
        if int(entry["occurrence_count"]) == 0
    ]
    single_scene_anchors = [
        {
            "anchor": anchor,
            "scene_labels": list(entry["scene_labels"]),
        }
        for anchor, entry in counts.items()
        if int(entry["scene_count"]) == 1
    ]

    return {
        "is_valid": not undefined_anchors and not unused_concepts and not single_scene_anchors,
        "undefined_anchors": undefined_anchors,
        "unused_concepts": unused_concepts,
        "single_scene_anchors": single_scene_anchors,
    }


def expand_prompt_for_scene(
    storybook: Storybook,
    scene: StoryScene,
    *,
    full: bool = False,
) -> str:
    """Expand one scene prompt.

    Parameters
    ----------
    storybook:
        Storybook containing the recurring concepts and global prompt context.
    scene:
        Scene whose prompt should be expanded.
    full:
        When ``True``, include the style and constraints wrapper used for
        illustration generation.

    Returns
    -------
    str
        Expanded prompt string.
    """

    if full:
        return build_scene_prompt(storybook, scene)
    return expand_prompt_anchors(scene.prompt, storybook.recurring_concepts).strip()
