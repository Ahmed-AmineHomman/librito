"""Prompt-consistency checks and scene expansion helpers for segmentation."""

from __future__ import annotations

import re

from librito.models import StoryScene, Storybook
from librito.prompt_builder import build_scene_prompt, expand_prompt_anchors

_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")
_STRICT_ANCHOR_PATTERN = re.compile(r"^<[A-Z0-9_]+>$")


def normalize_anchor_tag(tag: str) -> str:
    """Normalize a recurring concept tag to the canonical anchor format.

    Parameters
    ----------
    tag:
        User-provided recurring concept tag, with or without angle brackets.

    Returns
    -------
    str
        Canonical anchor tag in the ``<NAME>`` format.

    Raises
    ------
    ValueError
        If the tag is empty or cannot be normalized to a valid anchor.
    """

    normalized_tag = tag.strip()
    if not normalized_tag:
        raise ValueError("Anchor tags must be non-empty.")
    if is_valid_anchor_tag(normalized_tag):
        return normalized_tag
    if normalized_tag.startswith("<") and normalized_tag.endswith(">"):
        normalized_tag = normalized_tag[1:-1].strip()
    normalized_tag = re.sub(r"[^A-Z0-9]+", "_", normalized_tag.upper()).strip("_")
    if not normalized_tag:
        raise ValueError("Anchor tags must contain at least one letter or digit.")
    canonical_tag = f"<{normalized_tag}>"
    if not is_valid_anchor_tag(canonical_tag):
        raise ValueError("Anchor tags must normalize to the strict format <NAME>.")
    return canonical_tag


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

    occurrence_counts: dict[str, int] = {anchor: 0 for anchor in storybook.recurring_concepts}
    scene_labels: dict[str, list[str]] = {anchor: [] for anchor in storybook.recurring_concepts}

    for scene in storybook.scenes:
        anchors_in_scene = _ANCHOR_PATTERN.findall(scene.prompt)
        for anchor in anchors_in_scene:
            if anchor in occurrence_counts:
                occurrence_counts[anchor] += 1
        for anchor in sorted(set(anchors_in_scene)):
            if anchor in scene_labels:
                scene_labels[anchor].append(scene.label)

    return {
        anchor: {
            "occurrence_count": occurrence_counts[anchor],
            "scene_count": len(scene_labels[anchor]),
            "scene_labels": scene_labels[anchor],
        }
        for anchor in sorted(storybook.recurring_concepts)
    }


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
