"""Print selected storybook scene attributes as Markdown."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from textwrap import dedent
from typing import Sequence

import logging

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.environment import load_repository_environment
from librito.logging import add_logging_arguments, configure_logging
from librito.io import load_storybook
from librito.prompt_builder import expand_prompt_anchors
from librito.workspace import StoryWorkspace

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
        description=dedent(
            """
            Inspect one or more scenes from a segmented storybook.

            Use this when you already know which scene labels you want to inspect
            and need the scene text, the raw prompt, or the expanded prompt with
            anchors resolved to their descriptions.
            """
        ).strip(),
        epilog=dedent(
            """
            Output behavior:
              - prints one Markdown section per requested scene
              - keeps the requested scene order
              - optionally expands prompt anchors with --expand

            Typical use:
              - inspect scene text after segmentation edits
              - inspect raw prompts before illustration generation
              - inspect expanded prompts after a global anchor check

            Examples:
              python helpers/get_scene.py --story leo --scenes scene-01 --attributes text
              python helpers/get_scene.py --story leo --scenes scene-01 scene-04 --attributes prompt --expand
              python helpers/get_scene.py --story leo --scenes scene-01 --scenes scene-04 --attributes text --attributes prompt
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    add_logging_arguments(parser)
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story folder name under ./database/<story>/.",
    )
    parser.add_argument(
        "--scenes",
        required=True,
        action="extend",
        nargs="+",
        type=str,
        help="Scene labels to inspect.",
    )
    parser.add_argument(
        "--attributes",
        required=True,
        action="extend",
        nargs="+",
        choices=["text", "prompt"],
        type=str,
        help="Scene attributes to print for each selected scene.",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Expand prompt anchors before printing them. Only valid with 'prompt'.",
    )
    return parser.parse_args(argv)


def build_scene_report(
        story: str,
        scenes: Sequence[str],
        attributes: Sequence[str],
        expand_prompts: bool,
) -> str:
    """Build a Markdown report for the requested scenes.

    Parameters
    ----------
    story:
        Story identifier stored under ``database/``.
    scenes:
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

    workspace = StoryWorkspace.from_story(story)
    workspace.require_directory()
    storybook_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", storybook_path)
    storybook = load_storybook(storybook_path)
    scenes_by_label = {scene.label: scene for scene in storybook.scenes}
    missing_labels = [label for label in scenes if label not in scenes_by_label]
    if missing_labels:
        raise SystemExit(f"Unknown scene label(s): {', '.join(missing_labels)}")

    requested_attributes = ", ".join(attributes)
    prompt_mode = "expanded" if expand_prompts else "raw"
    if "prompt" not in attributes:
        prompt_mode = "not requested"
    logger.info(
        "Building scene report for story '%s' with %d scene(s), attributes=%s, prompt_mode=%s.",
        workspace.story,
        len(scenes),
        requested_attributes,
        prompt_mode,
    )

    sections: list[str] = [
        "\n".join(
            [
                "# Scene Report",
                "",
                f"- **Story:** {workspace.story}",
                f"- **Title:** {storybook.title}",
                f"- **Scenes requested:** {len(scenes)}",
                f"- **Attributes:** {requested_attributes}",
                f"- **Prompt mode:** {prompt_mode}",
            ]
        )
    ]
    for label in scenes:
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

    load_repository_environment()
    arguments = load_parameters(argv)
    configure_logging(arguments.log_level)
    logger.info("Starting scene report generation for story '%s'.", arguments.story)
    sys.stdout.write(
        build_scene_report(
            story=arguments.story,
            scenes=arguments.scenes,
            attributes=arguments.attributes,
            expand_prompts=arguments.expand,
        )
        + "\n"
    )
    logger.info("Scene report generation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
