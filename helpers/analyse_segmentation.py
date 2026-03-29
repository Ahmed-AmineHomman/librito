"""Analyse the segmentation by performing consistency diagnosis & prompt anchor expansion."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

from librito.io import load_storybook
from librito.models import Storybook
from librito.prompt_builder import expand_prompt_anchors

logger = logging.getLogger(__name__)

_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")
_STORYBOOK_FILENAME = "story.json"


def count_anchor_occurrences(storybook: Storybook) -> dict[str, int]:
    """Count recurring concept anchor occurrences across all scene prompts.

    Parameters
    ----------
    storybook:
        Parsed storybook definition loaded from JSON.

    Returns
    -------
    dict[str, int]
        Mapping from each defined recurring concept anchor to the number of
        times it appears in the raw scene prompts across the full storybook.
    """

    counts: Counter[str] = Counter(
        anchor
        for scene in storybook.scenes
        for anchor in _ANCHOR_PATTERN.findall(scene.prompt)
    )
    return {
        anchor: counts.get(anchor, 0)
        for anchor in sorted(storybook.recurring_concepts)
    }


def build_anchor_occurrence_report(storybook: Storybook) -> str:
    """Build a textual report describing anchor usage across the storybook.

    Parameters
    ----------
    storybook:
        Parsed storybook definition loaded from JSON.

    Returns
    -------
    str
        Human-readable anchor occurrence report suitable for stdout.
    """

    counts = count_anchor_occurrences(storybook)
    lines = ["Anchor occurrences:"]
    lines.extend(f"- {anchor}: {count}" for anchor, count in counts.items())
    single_use_anchors = [anchor for anchor, count in counts.items() if count == 1]
    if single_use_anchors:
        anchor_list = ", ".join(single_use_anchors)
        lines.append(f"WARNING: single-use anchors detected: {anchor_list}")
    return "\n".join(lines)


def build_storybook_skeleton_markdown(
    storybook: Storybook,
    scene_labels: list[str] | None = None,
) -> str:
    """Build the Markdown skeleton for a segmented storybook.

    Only anchor expansion is performed; style and constraints are omitted so
    the output focuses on prompt consistency.

    Parameters
    ----------
    storybook:
        Parsed storybook definition loaded from JSON.
    scene_labels:
        Optional list of scene labels to include.  When ``None`` or empty, all
        scenes are included.

    Returns
    -------
    str
        Markdown content containing one section per scene with text and the
        anchor-expanded prompt.
    """

    sections: list[str] = []
    for scene in storybook.scenes:
        if scene_labels and scene.label not in scene_labels:
            continue
        expanded_prompt = expand_prompt_anchors(
            scene.prompt,
            storybook.recurring_concepts,
        ).strip()
        scene_name = scene.label
        sections.append(
            "\n".join(
                [
                    f"## {scene_name}",
                    "",
                    "### Text",
                    "",
                    scene.text.strip(),
                    "",
                    "### Prompt",
                    "",
                    expanded_prompt,
                ]
            )
        )

    return "\n\n".join(sections).rstrip() + "\n"


def export_storybook_skeleton(
    story_directory: Path,
    output_filepath: Path | None = None,
    scene_labels: list[str] | None = None,
) -> None:
    """Print (and optionally write) a Markdown story skeleton.

    Parameters
    ----------
    story_directory:
        Path to the story folder containing ``story.json``.
    output_filepath:
        Optional destination path for the generated Markdown file.
    scene_labels:
        Optional scene labels to include.
    """

    input_json = story_directory / _STORYBOOK_FILENAME
    logger.info("Loading storybook from %s.", input_json)
    storybook = load_storybook(input_json)
    report = build_anchor_occurrence_report(storybook)
    markdown = build_storybook_skeleton_markdown(storybook, scene_labels)
    sys.stdout.write(f"{report}\n\n{markdown}")
    if output_filepath is not None:
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        output_filepath.write_text(markdown, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the storybook skeleton exporter.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    int
        Process exit status.
    """

    parser = argparse.ArgumentParser(
        description="Analyse segmentation consistency (anchor count, prompt with anchor expansion).",
    )
    parser.add_argument(
        "--storybook",
        required=True,
        type=Path,
        help="Path to the story folder (must contain story.json).",
    )
    parser.add_argument(
        "--output-file",
        required=False,
        default=None,
        type=Path,
        help="Optional path to a Markdown output file.",
    )
    parser.add_argument(
        "--scenes",
        nargs="*",
        type=str,
        default=None,
        help="Scene labels to include (all scenes if omitted).",
    )
    arguments = parser.parse_args(argv)
    export_storybook_skeleton(
        arguments.storybook,
        arguments.output_file,
        arguments.scenes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
