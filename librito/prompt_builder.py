"""Prompt construction helpers for illustration generation."""

from __future__ import annotations

import re
from importlib import resources

from librito.models import StoryScene, Storybook

_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")
_RESOURCE_DIRECTORY = resources.files("librito.resources")


def resolve_prompt(prompt: str, concepts: dict[str, str]) -> str:
    """Resolve concept anchors into bracketed descriptions.

    Parameters
    ----------
    prompt:
        Scene prompt that may contain concept anchors.
    concepts:
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
        if anchor not in concepts:
            raise ValueError(f"Undefined concept anchor: {anchor}.")
        return f"[{concepts[anchor]}]"

    return _ANCHOR_PATTERN.sub(replace_anchor, prompt)


def build_render_prompt(
        storybook: Storybook,
        scene: StoryScene,
) -> str:
    """Build the render prompt for one scene.

    Parameters
    ----------
    storybook:
        Storybook containing the global style, constraints, and recurring
        concepts.
    scene:
        Scene to render.

    Returns
    -------
    str
        Final prompt to send to the image generation API.
    """

    return build_render_prompt_from_text(storybook, scene.prompt)


def build_render_prompt_from_text(storybook: Storybook, prompt: str) -> str:
    """Build the render prompt for one raw illustration prompt string.

    Parameters
    ----------
    storybook:
        Storybook containing the global style, constraints, and recurring
        concepts.
    prompt:
        Illustration prompt to resolve and package for generation.

    Returns
    -------
    str
        Final prompt to send to the image generation API.
    """

    resolved_prompt = resolve_prompt(prompt, storybook.concepts).strip()
    template = _RESOURCE_DIRECTORY.joinpath("image_prompt_template.txt").read_text(encoding="utf-8")
    if storybook.constraints:
        constraints = storybook.constraints.strip()
    else:
        constraints = _RESOURCE_DIRECTORY.joinpath("prompt_constraints.txt").read_text(encoding="utf-8").strip()
    return template.format(
        style=storybook.style.strip(),
        scene_prompt=resolved_prompt,
        constraints=constraints,
    ).strip()
