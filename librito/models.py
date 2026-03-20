"""Storybook data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class StoryScene:
    """Single segmented story scene.

    Parameters
    ----------
    index:
        One-based position of the scene within the story.
    text:
        Reader-facing scene text.
    prompt:
        Illustration prompt using English and optional recurring concept tags.
    image_path:
        Relative path to the generated image within the story directory.
    """

    index: int
    text: str
    prompt: str
    image_path: str


@dataclass(slots=True)
class Storybook:
    """Segmented storybook ready for illustration generation.

    Parameters
    ----------
    title:
        Story title.
    style:
        Global visual style description written in English.
    constraints:
        Optional generation constraints.  When empty, the default constraints
        shipped in ``librito/resources/prompt_constraints.txt`` are used.
    recurring_concepts:
        Mapping from anchor tags such as ``<CALMIO>`` to their expanded
        descriptions.
    scenes:
        Ordered story scenes to illustrate.
    """

    title: str
    style: str
    recurring_concepts: dict[str, str]
    scenes: list[StoryScene]
    constraints: str = field(default="")
