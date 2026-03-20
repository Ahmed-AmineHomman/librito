"""Storybook data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StoryConstants:
    """Visual constants shared by all story scenes.

    Parameters
    ----------
    style:
        Global visual style description written in English.
    recurring_concepts:
        Mapping from anchor tags such as ``<CALMIO>`` to their expanded
        descriptions.
    """

    style: str
    recurring_concepts: dict[str, str]


@dataclass(slots=True)
class StoryScene:
    """Single segmented story scene.

    Parameters
    ----------
    text:
        Reader-facing scene text.
    prompt:
        Illustration prompt using English and optional recurring concept tags.
    image_path:
        Relative path to the generated image within the story directory.
    """

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
    constants:
        Shared visual constants used across all scenes.
    scenes:
        Ordered story scenes to illustrate.
    """

    title: str
    constants: StoryConstants
    scenes: list[StoryScene]
