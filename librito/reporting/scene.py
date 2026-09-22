"""Scene inspection and reporting."""

from __future__ import annotations

from typing import Sequence

import logging

from librito.io import load_storybook
from librito.prompt_builder import resolve_prompt
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)


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
        Whether prompts should be printed with anchors resolved.

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
    prompt_mode = "resolved" if expand_prompts else "raw"
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
                prompt = resolve_prompt(prompt, storybook.concept_map).strip()
                blocks.extend(["", "### Resolved Prompt", "", prompt])
            else:
                blocks.extend(["", "### Prompt", "", prompt])
        sections.append("\n".join(blocks))

    return "\n\n".join(sections)
