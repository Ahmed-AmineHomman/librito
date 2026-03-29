"""Print selected storybook scene attributes as Markdown."""

from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
        description="Return selected scene text and/or prompt attributes as Markdown.",
    )
    add_logging_arguments(parser)
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story identifier stored under ./database/<story>/.",
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
    story: str,
    labels: Sequence[str],
    attributes: Sequence[str],
    expand_prompts: bool,
) -> str:
    """Build a Markdown report for the requested scenes.

    Parameters
    ----------
    story:
        Story identifier stored under ``database/``.
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

    workspace = StoryWorkspace.from_story(story)
    workspace.require_directory()
    storybook_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", storybook_path)
    storybook = load_storybook(storybook_path)
    scenes_by_label = {scene.label: scene for scene in storybook.scenes}
    missing_labels = [label for label in labels if label not in scenes_by_label]
    if missing_labels:
        raise SystemExit(f"Unknown scene label(s): {', '.join(missing_labels)}")

    requested_attributes = ", ".join(attributes)
    prompt_mode = "expanded" if expand_prompts else "raw"
    if "prompt" not in attributes:
        prompt_mode = "not requested"
    logger.info(
        "Building scene report for story '%s' with %d scene(s), attributes=%s, prompt_mode=%s.",
        workspace.story,
        len(labels),
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
                f"- **Scenes requested:** {len(labels)}",
                f"- **Attributes:** {requested_attributes}",
                f"- **Prompt mode:** {prompt_mode}",
            ]
        )
    ]
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
    configure_logging(arguments.log_level)
    logger.info("Starting scene report generation for story '%s'.", arguments.story)
    sys.stdout.write(
        build_scene_report(
            story=arguments.story,
            labels=arguments.labels,
            attributes=arguments.attributes,
            expand_prompts=arguments.expand,
        )
        + "\n"
    )
    logger.info("Scene report generation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
