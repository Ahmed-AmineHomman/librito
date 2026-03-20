"""Export expanded storybook prompts for consistency diagnosis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from librito.models import Storybook
from librito.prompt_builder import expand_prompt_anchors
from librito.story_io import load_storybook


def build_storybook_skeleton_markdown(
    storybook: Storybook,
    scene_indexes: list[int] | None = None,
) -> str:
    """Build the Markdown skeleton for a segmented storybook.

    Only anchor expansion is performed; style and constraints are omitted so
    the output focuses on prompt consistency.

    Parameters
    ----------
    storybook:
        Parsed storybook definition loaded from JSON.
    scene_indexes:
        Optional list of scene indexes to include.  When ``None`` or empty,
        all scenes are included.

    Returns
    -------
    str
        Markdown content containing one section per scene with text and the
        anchor-expanded prompt.
    """

    sections: list[str] = []
    for scene in storybook.scenes:
        if scene_indexes and scene.index not in scene_indexes:
            continue
        expanded_prompt = expand_prompt_anchors(
            scene.prompt,
            storybook.recurring_concepts,
        ).strip()
        scene_name = f"Scene {scene.index:02d}"
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
    input_json: Path,
    output_filepath: Path | None = None,
    scene_indexes: list[int] | None = None,
) -> None:
    """Print (and optionally write) a Markdown story skeleton.

    Parameters
    ----------
    input_json:
        Path to the segmented story JSON file.
    output_filepath:
        Optional destination path for the generated Markdown file.
    scene_indexes:
        Optional scene indexes to include.
    """

    storybook = load_storybook(input_json)
    markdown = build_storybook_skeleton_markdown(storybook, scene_indexes)
    sys.stdout.write(markdown)
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
        description="Export expanded storybook prompts for consistency diagnosis.",
    )
    parser.add_argument(
        "--storybook",
        required=True,
        type=Path,
        help="Path to the story JSON file.",
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
        type=int,
        default=None,
        help="Scene indexes to include (all scenes if omitted).",
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
