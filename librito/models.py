"""Storybook and normalization data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class StoryScene:
    """Single segmented story scene.

    Parameters
    ----------
    label:
        Stable unique identifier for the scene within the storybook.
    text:
        Reader-facing scene text.
    prompt:
        Illustration prompt using English and optional recurring concept tags.
    image_path:
        Relative path to the generated image within the story directory.
    """

    label: str
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


@dataclass(slots=True)
class NormalizedUnit:
    """Single normalized evaluation unit.

    Parameters
    ----------
    label:
        Stable unique identifier for the unit within the normalized story.
    type:
        Canonical unit type, for example ``"narration"`` or
        ``"dialogue_turn"``.
    text:
        Normalized unit text kept as close as possible to the source story.
    """

    label: str
    type: str
    text: str


@dataclass(slots=True)
class NormalizedStory:
    """Normalized story ready for semantic evaluation.

    Parameters
    ----------
    units:
        Ordered normalized units extracted from the source story.
    """

    units: list[NormalizedUnit]
