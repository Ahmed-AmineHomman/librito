"""Prompt construction helpers for illustration generation."""

from __future__ import annotations

import re
from importlib import resources

from librito.models import StoryScene, Storybook

_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")
_RESOURCE_DIRECTORY = resources.files("librito.resources")


def expand_prompt_anchors(prompt: str, recurring_concepts: dict[str, str]) -> str:
    """Expand recurring concept anchors into bracketed descriptions.

    Parameters
    ----------
    prompt:
        Scene prompt that may contain recurring concept anchors.
    recurring_concepts:
        Mapping from anchor tags to expanded descriptions.

    Returns
    -------
    str
        Prompt with anchors replaced by bracketed descriptions.

    Raises
    ------
    ValueError
        If an anchor is referenced but not defined.
    """

    def replace_anchor(match: re.Match[str]) -> str:
        anchor = match.group(0)
        if anchor not in recurring_concepts:
            raise ValueError(f"Undefined recurring concept anchor: {anchor}.")
        return f"[{recurring_concepts[anchor]}]"

    return _ANCHOR_PATTERN.sub(replace_anchor, prompt)


def build_scene_prompt(
    storybook: Storybook,
    scene: StoryScene,
) -> str:
    """Build the final image-generation prompt for one scene.

    Parameters
    ----------
    storybook:
        Storybook containing the global style and recurring concepts.
    scene:
        Scene to render.
    Returns
    -------
    str
        Final prompt to send to the image generation API.
    """

    expanded_prompt = expand_prompt_anchors(scene.prompt, storybook.constants.recurring_concepts).strip()
    template = _RESOURCE_DIRECTORY.joinpath("image_prompt_template.txt").read_text(encoding="utf-8")
    constraints = _RESOURCE_DIRECTORY.joinpath("prompt_constraints.txt").read_text(encoding="utf-8").strip()
    return template.format(
        style=storybook.constants.style.strip(),
        scene_prompt=expanded_prompt,
        constraints=constraints,
    ).strip()
