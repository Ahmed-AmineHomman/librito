"""Print selected storybook scene attributes as Markdown."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.io import load_storybook
from librito.prompt_builder import expand_prompt_anchors

_DATABASE_DIRECTORY = Path(__file__).resolve().parent.parent / "database"
_STORYBOOK_FILENAME = "story.json"


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
        description="Return selected scene text and/or prompt attributes as Markdown.",
    )
    parser.add_argument(
        "--storybook",
        required=True,
        type=str,
        help="Storybook label. Files are resolved from ./database/<label>/.",
    )
    parser.add_argument(
        "--labels",
        required=True,
        nargs="+",
        type=str,
        help="Scene labels to inspect.",
    )
    parser.add_argument(
        "--attributes",
        required=True,
        nargs="+",
        choices=["text", "prompt"],
        type=str,
        help="Attributes to print for each selected scene.",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Expand prompt anchors before printing them. Only valid with 'prompt'.",
    )
    return parser.parse_args(argv)


def build_scene_report(
    storybook_label: str,
    labels: Sequence[str],
    attributes: Sequence[str],
    expand_prompts: bool,
) -> str:
    """Build a Markdown report for the requested scenes.

    Parameters
    ----------
    storybook_label:
        Storybook label stored under ``database/``.
    labels:
        Scene labels to include, in output order.
    attributes:
        Attribute names to include for each scene.
    expand_prompts:
        Whether prompts should be printed with anchors expanded.

    Returns
    -------
    str
        Markdown report suitable for stdout.
    """

    if expand_prompts and "prompt" not in attributes:
        raise SystemExit("The --expand flag can only be used when 'prompt' is requested.")

    story_directory = _DATABASE_DIRECTORY / storybook_label
    storybook_path = story_directory / _STORYBOOK_FILENAME
    if not story_directory.is_dir():
        raise SystemExit(f"Missing story directory: {story_directory}")
    if not storybook_path.is_file():
        raise SystemExit(f"Missing required file: {storybook_path}")

    storybook = load_storybook(storybook_path)
    scenes_by_label = {scene.label: scene for scene in storybook.scenes}
    missing_labels = [label for label in labels if label not in scenes_by_label]
    if missing_labels:
        raise SystemExit(f"Unknown scene label(s): {', '.join(missing_labels)}")

    sections: list[str] = []
    for label in labels:
        scene = scenes_by_label[label]
        blocks = [f"## {scene.label}"]
        for attribute in attributes:
            if attribute == "text":
                blocks.extend(["", "### Text", "", scene.text.strip()])
                continue

            prompt = scene.prompt.strip()
            if expand_prompts:
                prompt = expand_prompt_anchors(prompt, storybook.recurring_concepts).strip()
                blocks.extend(["", "### Expanded Prompt", "", prompt])
            else:
                blocks.extend(["", "### Prompt", "", prompt])
        sections.append("\n".join(blocks))

    return "\n\n".join(sections)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the scene inspection helper.

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
    sys.stdout.write(
        build_scene_report(
            storybook_label=arguments.storybook,
            labels=arguments.labels,
            attributes=arguments.attributes,
            expand_prompts=arguments.expand,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
