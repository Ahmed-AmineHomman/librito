"""Anchoring consistency analysis for storybooks."""

from __future__ import annotations

import re
from typing import Sequence

import logging

from librito.io import load_storybook
from librito.models import Storybook
from librito.segmentation.validators import check_prompt_consistency
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)
_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")


def build_anchor_report(
        story: str,
        details: str,
        anchors: Sequence[str] | None = None,
) -> str:
    """Build a Markdown anchoring consistency report.

    Parameters
    ----------
    story:
        Story identifier stored under ``database/``.
    details:
        Detail level for the report.
    anchors:
        Optional anchors to expand when ``details`` is ``selected``.

    Returns
    -------
    str
        Markdown report suitable for stdout.
    """

    requested_anchors = _deduplicate(anchors or [])
    workspace = StoryWorkspace.from_story(story)
    workspace.require_directory()
    input_json = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", input_json)
    storybook = load_storybook(input_json)
    defined_anchors = sorted(storybook.concept_tags)
    report = check_prompt_consistency(storybook)
    undefined_anchor_names = sorted(
        {
            item["anchor"]
            for item in report["undefined_anchors"]
        }
    )
    unused_anchors = list(report["unused_concepts"])
    single_scene_anchors = sorted(
        {
            item["anchor"]
            for item in report["single_scene_anchors"]
        }
    )
    prompt_occurrences = _count_prompt_anchor_occurrences(storybook)
    selectable_anchors = defined_anchors + [
        anchor
        for anchor in undefined_anchor_names
        if anchor not in storybook.concept_map
    ]
    detailed_anchors = _resolve_anchor_names(
        available_anchors=selectable_anchors,
        details=details,
        requested_anchors=requested_anchors,
    )
    is_consistent = not undefined_anchor_names and not unused_anchors and not single_scene_anchors
    logger.info(
        "Anchoring analysis complete for story '%s': undefined=%d, unused=%d, single_scene=%d.",
        workspace.story,
        len(undefined_anchor_names),
        len(unused_anchors),
        len(single_scene_anchors),
    )

    lines = [
        "# Anchoring Consistency Report",
        "",
        f"- **Story:** {workspace.story}",
        f"- **Title:** {storybook.title}",
        f"- **Scenes:** {len(storybook.scenes)}",
        f"- **Defined concepts:** {len(storybook.concepts)}",
        f"- **Result:** {'PASS' if is_consistent else 'FAIL'}",
        f"- **Detail mode:** {details}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Undefined anchors | {len(undefined_anchor_names)} |",
        f"| Unused concepts | {len(unused_anchors)} |",
        f"| Single-scene concepts | {len(single_scene_anchors)} |",
        "",
        "## Checks",
        "",
        _format_check("Undefined anchors in prompts", len(undefined_anchor_names)),
        _format_check("Unused concepts", len(unused_anchors)),
        _format_check("Concepts used in only one scene", len(single_scene_anchors)),
    ]

    if details != "summary":
        lines.extend(
            [
                "",
                "## Anchor Breakdown",
                "",
                f"- **Anchors detailed:** {len(detailed_anchors)}",
                "",
                "| Anchor | Kind | Prompt occurrences | Scenes | Status |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        for anchor in detailed_anchors:
            kind = "defined" if anchor in storybook.concept_map else "undefined"
            usage_status = _determine_anchor_status(
                anchor=anchor,
                is_defined=kind == "defined",
                unused_anchors=unused_anchors,
                single_scene_anchors=single_scene_anchors,
            )
            lines.append(
                "| {anchor} | {kind} | {occurrences} | {scenes} | {status} |".format(
                    anchor=anchor,
                    kind=kind,
                    occurrences=prompt_occurrences.get(anchor, {}).get("occurrence_count", 0),
                    scenes=", ".join(prompt_occurrences.get(anchor, {}).get("scene_labels", [])) or "-",
                    status=usage_status,
                )
            )

    return "\n".join(lines)


def _format_check(
        title: str,
        finding_count: int,
) -> str:
    """Format one checklist item for the Markdown report.

    Parameters
    ----------
    title:
        Human-readable check title.
    finding_count:
        Number of findings for this check.

    Returns
    -------
    str
        Formatted Markdown bullet.
    """

    if finding_count == 0:
        return f"- [x] {title}"
    return f"- [ ] {title} ({finding_count})"


def _count_prompt_anchor_occurrences(storybook: Storybook) -> dict[str, dict[str, object]]:
    """Count prompt anchor usage for all anchors found in scene prompts.

    Parameters
    ----------
    storybook:
        Parsed storybook definition.

    Returns
    -------
    dict[str, dict[str, object]]
        Mapping from each prompt anchor to its total token count, number of
        distinct scenes using it, and the ordered list of those scene labels.
    """

    prompt_occurrences: dict[str, int] = {}
    scene_labels_by_anchor: dict[str, list[str]] = {}
    for scene in storybook.scenes:
        anchors_in_scene = _ANCHOR_PATTERN.findall(scene.prompt)
        for anchor in anchors_in_scene:
            prompt_occurrences[anchor] = prompt_occurrences.get(anchor, 0) + 1
        for anchor in _deduplicate(anchors_in_scene):
            scene_labels_by_anchor.setdefault(anchor, []).append(scene.label)

    return {
        anchor: {
            "occurrence_count": prompt_occurrences[anchor],
            "scene_count": len(scene_labels_by_anchor.get(anchor, [])),
            "scene_labels": scene_labels_by_anchor.get(anchor, []),
        }
        for anchor in sorted(prompt_occurrences)
    }


def _resolve_anchor_names(
        available_anchors: Sequence[str],
        details: str,
        requested_anchors: Sequence[str],
) -> list[str]:
    """Resolve which anchors should receive detailed output.

    Parameters
    ----------
    available_anchors:
        Anchors that can be expanded in the report.
    details:
        Requested detail level.
    requested_anchors:
        Anchors explicitly requested by the caller.

    Returns
    -------
    list[str]
        Anchors to expand in the report.

    Raises
    ------
    SystemExit
        If the requested anchors include unknown names.
    """

    if details == "summary":
        return []
    if details == "all":
        return list(available_anchors)

    available_anchor_set = set(available_anchors)
    unknown_anchors = [
        anchor
        for anchor in requested_anchors
        if anchor not in available_anchor_set
    ]
    if unknown_anchors:
        raise SystemExit(f"Unknown anchor(s): {', '.join(unknown_anchors)}")
    return list(requested_anchors)


def _determine_anchor_status(
        anchor: str,
        is_defined: bool,
        unused_anchors: Sequence[str],
        single_scene_anchors: Sequence[str],
) -> str:
    """Return the status label for one anchor.

    Parameters
    ----------
    anchor:
        Anchor name to classify.
    is_defined:
        Whether the anchor is a declared concept.
    unused_anchors:
        Anchors defined but unused across prompts.
    single_scene_anchors:
        Anchors defined but used in only one scene.

    Returns
    -------
    str
        Status label for the report.
    """

    if anchor in unused_anchors:
        return "unused"
    if anchor in single_scene_anchors:
        return "single-scene"
    if is_defined:
        return "ok"
    return "undefined"


def _deduplicate(values: Sequence[str]) -> list[str]:
    """Return values without duplicates while preserving their first-seen order.

    Parameters
    ----------
    values:
        Input strings in arbitrary order.

    Returns
    -------
    list[str]
        Deduplicated values.
    """

    ordered_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            continue
        seen_values.add(value)
        ordered_values.append(value)
    return ordered_values
