"""Story, storybook, and units data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class IllustrationSpec:
    """Illustration content stored in the storybook.

    Parameters
    ----------
    prompt:
        Illustration prompt written in English.
    image_path:
        Relative path to the generated image within the story directory.
    text_mode:
        Whether reader-facing text is overlaid by the assembler or is already
        embedded inside the illustration itself. Use ``None`` when the concept
        is not relevant for the page.
    """

    prompt: str = ""
    image_path: str = ""
    text_mode: str | None = field(default=None)


@dataclass(slots=True)
class Concept:
    """A recurring visual concept tracked across scenes.

    Parameters
    ----------
    tag:
        Canonical anchor tag in ``<UPPER_SNAKE>`` format.
    description:
        Stable visual description of the concept.
    image_path:
        Relative path to the concept's reference artwork within the story
        directory. Empty until the artwork-generation stage fills it.
    scenes:
        Ordered scene labels where this concept visually appears.
    """

    tag: str
    description: str
    image_path: str = ""
    scenes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PageSpec:
    """Reusable non-scene page content stored in the storybook.

    Parameters
    ----------
    text:
        Ordered reader-facing text blocks for the page.
    illustration:
        Optional illustration associated with the page.
    """

    text: list[str] = field(default_factory=list)
    illustration: IllustrationSpec | None = field(default=None)


@dataclass(slots=True)
class BookParts:
    """Non-scene book parts stored alongside the story scenes.

    Parameters
    ----------
    front_cover:
        Required front-cover page content.
    front_endpaper:
        Optional front-endpaper page content.
    opening_page:
        Optional dedication and/or epigraph page content.
    frontispiece:
        Optional frontispiece page content.
    title_page:
        Required title-page content.
    closing_facing_page:
        Optional text page facing the closing illustration.
    closing_illustration:
        Optional closing-illustration page content.
    back_cover:
        Required back-cover page content.
    """

    front_cover: PageSpec
    front_endpaper: PageSpec | None = field(default=None)
    opening_page: PageSpec | None = field(default=None)
    frontispiece: PageSpec | None = field(default=None)
    title_page: PageSpec = field(default_factory=PageSpec)
    closing_facing_page: PageSpec | None = field(default=None)
    closing_illustration: PageSpec | None = field(default=None)
    back_cover: PageSpec = field(default_factory=PageSpec)


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
        Empty until the prompt-design stage fills it.
    image_path:
        Relative path to the generated image within the story directory.
        Empty until the illustration-generation stage fills it.
    """

    label: str
    text: str
    prompt: str = ""
    image_path: str = ""


@dataclass(slots=True)
class Storybook:
    """Segmented storybook ready for illustration generation and assembly.

    Parameters
    ----------
    title:
        Story title.
    author:
        Reader-facing author name.
    style:
        Global visual style description written in English.
    constraints:
        Optional generation constraints. When empty, the default constraints
        shipped in ``librito/resources/prompt_constraints.txt`` are used.
    concepts:
        Ordered list of recurring visual concepts with tags, descriptions,
        reference artwork paths, and scene mappings.
    parts:
        Structured non-scene book parts such as covers and front matter.
    scenes:
        Ordered story scenes to illustrate.
    style_image_path:
        Relative path to the style reference artwork within the story
        directory. Empty until the artwork-generation stage fills it.
    """

    title: str
    author: str
    style: str
    concepts: list[Concept]
    parts: BookParts
    scenes: list[StoryScene]
    constraints: str = field(default="")
    style_image_path: str = field(default="")

    @property
    def concept_map(self) -> dict[str, str]:
        """Mapping from concept anchor tags to their text descriptions.

        Returns
        -------
        dict[str, str]
            Tag-to-description mapping for anchor resolution.
        """

        return {c.tag: c.description for c in self.concepts}

    @property
    def concept_tags(self) -> list[str]:
        """Ordered list of concept anchor tags.

        Returns
        -------
        list[str]
            Tags in concept order.
        """

        return [c.tag for c in self.concepts]


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
