"""Story, storybook, and units data models."""

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
        Illustration prompt using English and optional concept tags.
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
    concepts:
        Mapping from anchor tags such as ``<CALMIO>`` to their expanded
        descriptions.
    scenes:
        Ordered story scenes to illustrate.
    """

    title: str
    style: str
    concepts: dict[str, str]
    scenes: list[StoryScene]
    constraints: str = field(default="")


@dataclass(slots=True)
class Unit:
    """Single unit from the units artifact.

    Parameters
    ----------
    label:
        Stable unique identifier for the unit within the units artifact.
    type:
        Canonical unit type, for example ``"narration"`` or
        ``"dialogue_turn"``.
    text:
        Unit text kept as close as possible to the source story.
    """

    label: str
    type: str
    text: str


@dataclass(slots=True)
class Units:
    """Units artifact used for semantic evaluation.

    Parameters
    ----------
    units:
        Ordered units extracted from the story.
    """

    units: list[Unit]
