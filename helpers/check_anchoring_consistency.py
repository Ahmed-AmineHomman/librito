"""Check anchor usage consistency in a segmented storybook."""

from __future__ import annotations

import logging
import re
import sys
from argparse import ArgumentParser, Namespace
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.logging import add_logging_arguments, configure_logging
from librito.io import load_storybook
from librito.models import Storybook
from librito.workspace import StoryWorkspace

_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")
logger = logging.getLogger(__name__)


def load_parameters(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command-line arguments.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    Namespace
        Parsed command-line arguments.
    """

    parser = ArgumentParser(
        description="Check anchoring consistency for a storybook and print a Markdown report.",
    )
    add_logging_arguments(parser)
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story identifier stored under ./database/<story>/.",
    )
    return parser.parse_args(argv)


def build_anchor_report(story: str) -> str:
    """Build a Markdown anchoring consistency report.

    Parameters
    ----------
    story:
        Story identifier stored under ``database/``.

    Returns
    -------
    str
        Markdown report suitable for stdout.
    """

    workspace = StoryWorkspace.from_story(story)
    workspace.require_directory()
    input_json = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", input_json)
    storybook = load_storybook(input_json)
    defined_anchors = set(storybook.recurring_concepts)
    occurrence_counts: Counter[str] = Counter()
    scene_counts: Counter[str] = Counter()
    scene_labels_by_anchor: dict[str, list[str]] = defaultdict(list)
    undefined_anchors: dict[str, list[str]] = defaultdict(list)
    undefined_seen: dict[str, set[str]] = defaultdict(set)

    for scene in storybook.scenes:
        anchors_in_scene = _ANCHOR_PATTERN.findall(scene.prompt)
        occurrence_counts.update(anchors_in_scene)

        seen_in_scene: set[str] = set()
        for anchor in anchors_in_scene:
            if anchor not in defined_anchors:
                if scene.label not in undefined_seen[anchor]:
                    undefined_seen[anchor].add(scene.label)
                    undefined_anchors[anchor].append(scene.label)
                continue
            if anchor in seen_in_scene:
                continue
            seen_in_scene.add(anchor)
            scene_counts[anchor] += 1
            scene_labels_by_anchor[anchor].append(scene.label)

    unused_anchors = sorted(anchor for anchor in defined_anchors if occurrence_counts[anchor] == 0)
    single_scene_anchors = sorted(anchor for anchor in defined_anchors if scene_counts[anchor] == 1)
    undefined_anchor_names = sorted(undefined_anchors)
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
        f"- **Defined recurring concepts:** {len(storybook.recurring_concepts)}",
        f"- **Result:** {'PASS' if is_consistent else 'FAIL'}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Undefined anchors | {len(undefined_anchor_names)} |",
        f"| Unused recurring concepts | {len(unused_anchors)} |",
        f"| Single-scene recurring concepts | {len(single_scene_anchors)} |",
        "",
        "## Checks",
        "",
        _format_check(
            "Undefined anchors in prompts",
            undefined_anchor_names,
            undefined_anchors,
        ),
        _format_check(
            "Unused recurring concepts",
            unused_anchors,
        ),
        _format_check(
            "Recurring concepts used in only one scene",
            single_scene_anchors,
            scene_labels_by_anchor,
        ),
        "",
        "## Anchor Usage",
        "",
        "| Anchor | Prompt occurrences | Scenes | Status |",
        "| --- | ---: | --- | --- |",
    ]

    for anchor in sorted(defined_anchors):
        usage_status = "ok"
        if anchor in unused_anchors:
            usage_status = "unused"
        elif anchor in single_scene_anchors:
            usage_status = "single-scene"

        lines.append(
            "| {anchor} | {occurrences} | {scenes} | {status} |".format(
                anchor=anchor,
                occurrences=occurrence_counts[anchor],
                scenes=", ".join(scene_labels_by_anchor.get(anchor, [])) or "-",
                status=usage_status,
            )
        )

    if undefined_anchor_names:
        lines.extend(
            [
                "",
                "## Undefined Anchor Details",
                "",
                "| Anchor | Scenes |",
                "| --- | --- |",
            ]
        )
        for anchor in undefined_anchor_names:
            lines.append(f"| {anchor} | {', '.join(undefined_anchors[anchor])} |")

    return "\n".join(lines)


def _format_check(
    title: str,
    anchors: Sequence[str],
    details: dict[str, list[str]] | None = None,
) -> str:
    """Format one checklist item for the Markdown report.

    Parameters
    ----------
    title:
        Human-readable check title.
    anchors:
        Anchors involved in the finding.
    details:
        Optional scene labels associated with each anchor.

    Returns
    -------
    str
        Formatted Markdown bullet.
    """

    if not anchors:
        return f"- [x] {title}"

    if details is None:
        return f"- [ ] {title}: {', '.join(anchors)}"

    formatted_items = [f"{anchor} ({', '.join(details[anchor])})" for anchor in anchors]
    return f"- [ ] {title}: {', '.join(formatted_items)}"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the anchoring consistency helper.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    int
        Process exit status.
    """

    arguments = load_parameters(argv)
    configure_logging(arguments.log_level)
    logger.info("Starting anchoring consistency check for story '%s'.", arguments.story)
    sys.stdout.write(build_anchor_report(arguments.story) + "\n")
    logger.info("Anchoring consistency check complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
