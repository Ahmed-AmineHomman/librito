"""Prompt construction helpers for illustration generation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Sequence

from librito.models import Concept, StoryScene, Storybook

_ANCHOR_PATTERN = re.compile(r"<[A-Z0-9_]+>")
_RESOURCE_DIRECTORY = resources.files("librito.resources")


class MissingArtworkError(RuntimeError):
    """Raised when a required concept reference artwork is missing."""


@dataclass(slots=True)
class RenderPrompt:
    """Render prompt details for illustration generation.

    Parameters
    ----------
    text:
        Assembled prompt text to send to the image generation backend.
    image_paths:
        Ordered list of concept reference artwork paths corresponding to
        concepts referenced in the prompt.
    concepts:
        Ordered list of concept objects referenced in the prompt.
    """

    text: str
    image_paths: list[Path] = field(default_factory=list)
    concepts: list[Concept] = field(default_factory=list)

    def __str__(self) -> str:
        """Return the assembled prompt string.

        Returns
        -------
        str
            Assembled prompt text.
        """

        return self.text


def clean_anchor_tags(prompt: str) -> str:
    """Strip angle brackets from concept anchor tags within a prompt string.

    Parameters
    ----------
    prompt:
        Prompt string containing anchor tags in the ``<NAME>`` format.

    Returns
    -------
    str
        Prompt string with anchor tags converted to bare names (e.g. ``NAME``).
    """

    return _ANCHOR_PATTERN.sub(lambda match: match.group(0)[1:-1], prompt)


def extract_prompt_anchors(prompt: str) -> list[str]:
    """Extract distinct concept anchor tags from a prompt in order of appearance.

    Parameters
    ----------
    prompt:
        Prompt string that may contain concept anchor tags.

    Returns
    -------
    list[str]
        Ordered list of distinct anchor tags (e.g. ``["<LEO>", "<TOY_CAR>"]``).
    """

    ordered_anchors: list[str] = []
    seen: set[str] = set()
    for anchor in _ANCHOR_PATTERN.findall(prompt):
        if anchor not in seen:
            seen.add(anchor)
            ordered_anchors.append(anchor)
    return ordered_anchors


def resolve_prompt(
        prompt: str,
        concepts: dict[str, str],
) -> str:
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


def load_default_scene_constraints() -> str:
    """Load default scene illustration constraints from bundled resources.

    Returns
    -------
    str
        Default scene prompt constraints.
    """

    return _RESOURCE_DIRECTORY.joinpath("prompt_constraints.txt").read_text(encoding="utf-8").strip()


def load_default_subject_artworks_constraints() -> str:
    """Load default subject artwork constraints from bundled resources.

    Returns
    -------
    str
        Default subject artwork constraints.
    """

    return _RESOURCE_DIRECTORY.joinpath("subject_artworks_constraints.txt").read_text(encoding="utf-8").strip()


def load_default_environment_artworks_constraints() -> str:
    """Load default environment artwork constraints from bundled resources.

    Returns
    -------
    str
        Default environment artwork constraints.
    """

    return _RESOURCE_DIRECTORY.joinpath("environment_artworks_constraints.txt").read_text(encoding="utf-8").strip()


def resolve_scene_constraints(
        storybook: Storybook,
        override: str | None = None,
) -> str:
    """Resolve effective scene constraints for illustration generation.

    Parameters
    ----------
    storybook:
        Storybook containing story data and optional custom constraints.
    override:
        Optional constraints override (e.g. from helper CLI argument).

    Returns
    -------
    str
        Effective non-empty scene constraints.
    """

    if override is not None and override.strip():
        return override.strip()
    if storybook.constraints.strip():
        return storybook.constraints.strip()
    return load_default_scene_constraints()


def resolve_concept_artwork_constraints(
        storybook: Storybook,
        concept: Concept,
        override: str | None = None,
) -> str:
    """Resolve effective constraints for concept reference artwork generation.

    Parameters
    ----------
    storybook:
        Storybook containing story data and optional custom constraints.
    concept:
        Concept being illustrated.
    override:
        Optional constraints override (e.g. from helper CLI argument).

    Returns
    -------
    str
        Effective non-empty artwork constraints.
    """

    if override is not None and override.strip():
        return override.strip()
    if concept.is_environment:
        if storybook.environment_artworks_constraints.strip():
            return storybook.environment_artworks_constraints.strip()
        return load_default_environment_artworks_constraints()
    if storybook.subject_artworks_constraints.strip():
        return storybook.subject_artworks_constraints.strip()
    return load_default_subject_artworks_constraints()


def build_render_prompt(
        storybook: Storybook,
        scene: StoryScene,
        constraints: str,
        workspace_dir: Path | None = None,
        require_artworks: bool = True,
) -> RenderPrompt:
    """Build the render prompt and resolve reference artworks for one scene.

    Parameters
    ----------
    storybook:
        Storybook containing the global style and recurring concepts.
    scene:
        Scene to render.
    constraints:
        Generation constraints to apply to the scene.
    workspace_dir:
        Optional story workspace directory used to validate artwork file
        existence on disk.
    require_artworks:
        Whether to require that referenced concept reference artworks exist.

    Returns
    -------
    RenderPrompt
        Structured render prompt containing the formatted text, reference
        artwork paths, and referenced concepts.
    """

    return build_render_prompt_from_text(
        storybook=storybook,
        prompt=scene.prompt,
        constraints=constraints,
        workspace_dir=workspace_dir,
        require_artworks=require_artworks,
    )


def build_render_prompt_from_text(
        storybook: Storybook,
        prompt: str,
        constraints: str,
        workspace_dir: Path | None = None,
        require_artworks: bool = True,
) -> RenderPrompt:
    """Build the render prompt and resolve reference artworks for a prompt string.

    Parameters
    ----------
    storybook:
        Storybook containing the global style and recurring concepts.
    prompt:
        Illustration prompt to resolve and package for generation.
    constraints:
        Generation constraints to apply to the prompt.
    workspace_dir:
        Optional story workspace directory used to validate artwork file
        existence on disk.
    require_artworks:
        Whether to require that referenced concept reference artworks exist.

    Returns
    -------
    RenderPrompt
        Structured render prompt containing the formatted text, reference
        artwork paths, and referenced concepts.

    Raises
    ------
    ValueError
        If an anchor in the prompt is not declared in the storybook concepts.
    MissingArtworkError
        If a concept referenced in the prompt is missing its reference artwork
        and ``require_artworks`` is ``True``.
    """

    concept_lookup: dict[str, Concept] = {concept.tag: concept for concept in storybook.concepts}
    referenced_anchors = extract_prompt_anchors(prompt)

    scene_concepts: list[Concept] = []
    artwork_paths: list[Path] = []
    for anchor in referenced_anchors:
        if anchor not in concept_lookup:
            raise ValueError(f"Undefined concept anchor: {anchor}.")
        concept = concept_lookup[anchor]
        if require_artworks:
            if not concept.image_path.strip():
                raise MissingArtworkError(
                    f"Missing reference artwork for concept '{concept.tag}'. "
                    "Concept artworks must be generated before illustrating scenes."
                )
            if workspace_dir is not None:
                artwork_file = workspace_dir / concept.image_path
                if not artwork_file.is_file():
                    raise MissingArtworkError(
                        f"Missing reference artwork file for concept '{concept.tag}'. "
                        f"Expected file at: {artwork_file}. "
                        "Concept artworks must be generated before illustrating scenes."
                    )
            else:
                artwork_file = Path(concept.image_path)
            artwork_paths.append(artwork_file)
        elif concept.image_path.strip():
            artwork_file = (workspace_dir / concept.image_path) if workspace_dir else Path(concept.image_path)
            artwork_paths.append(artwork_file)

        scene_concepts.append(concept)

    scene_prompt = clean_anchor_tags(prompt).strip()

    if scene_concepts:
        lines = [
            "",
            "## Concepts",
            "",
            "The provided images correspond to the following concepts involved in the scene in this exact order:",
            "",
        ]
        for index, concept in enumerate(scene_concepts, start=1):
            tag_name = concept.tag.strip("<>")
            lines.append(f"{index}. {tag_name}: {concept.description};")
        concepts_section = "\n" + "\n".join(lines)
        instructions = (
            "Generate a brand-new, original illustration from scratch based on the scene description and visual style below.\n"
            "The attached reference images are visual anchors for specific recurring concepts (characters, objects, or settings). "
            "Use them strictly to maintain character and visual consistency across illustrations.\n"
            "Do NOT treat this as an image editing, modification, or inpainting task. Do NOT alter, crop, or composite the reference images. "
            "Create a completely new scene composition featuring these concepts."
        )
    else:
        concepts_section = ""
        instructions = (
            "Generate a brand-new, original illustration from scratch based on the scene description and visual style below."
        )

    template = _RESOURCE_DIRECTORY.joinpath("image_prompt_template.txt").read_text(encoding="utf-8")
    text = template.format(
        instructions=instructions,
        style=storybook.style.strip(),
        concepts_section=concepts_section,
        scene_prompt=scene_prompt,
        constraints=constraints.strip(),
    ).strip()

    return RenderPrompt(
        text=text,
        image_paths=artwork_paths,
        concepts=scene_concepts,
    )


def build_concept_artwork_prompt(
        storybook: Storybook,
        concept: Concept,
        constraints: str,
) -> str:
    """Build the prompt to generate a reference artwork for a concept.

    Parameters
    ----------
    storybook:
        Storybook containing the global style definition.
    concept:
        Concept to illustrate as a reference artwork.
    constraints:
        Generation constraints to apply to the concept reference artwork.

    Returns
    -------
    str
        Prompt string for generating the concept artwork.
    """

    if concept.is_environment:
        header = "Environment"
        instructions = (
            "Generate a clean reference artwork of the environment in the specified style. "
            "Focus solely on depicting the architecture, landscape, spatial layout, lighting, "
            "and characteristic atmosphere of the setting clearly for use as a visual anchor."
        )
    else:
        header = "Subject"
        instructions = (
            "Generate a clean reference artwork of the subject on a neutral background in the specified style. "
            "Focus solely on depicting the visual features and characteristic appearance of the subject "
            "clearly for use as a visual anchor."
        )

    return (
        f"Style: {storybook.style.strip()}\n\n"
        f"{header}: {concept.description.strip()}\n\n"
        "Instructions:\n"
        f"{instructions}\n\n"
        f"Constraints:\n{constraints.strip()}"
    )
