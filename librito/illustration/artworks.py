"""Concept reference artwork generation."""

from __future__ import annotations

import logging
import re
from typing import Sequence

from librito.io import load_storybook, save_storybook
from librito.models import Concept, Storybook
from librito.prompt_builder import (
    build_concept_artwork_prompt,
    resolve_concept_artwork_constraints,
)
from librito.providers import build_image_client
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)


def slugify_tag(tag: str) -> str:
    """Convert a concept tag to a filesystem-safe basename fragment.

    Parameters
    ----------
    tag:
        Concept anchor tag, e.g. ``"<TOY_CAR>"`` or ``"LEO"``.

    Returns
    -------
    str
        Filesystem-safe lowercase slug (e.g. ``"toy-car"``).
    """

    cleaned = tag.strip("<>").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    return slug or "concept"


def resolve_target_concepts(
        storybook: Storybook,
        requested_tags: Sequence[str] | None,
) -> list[Concept]:
    """Filter concepts based on optional command-line tag filters.

    Parameters
    ----------
    storybook:
        Storybook containing defined concepts.
    requested_tags:
        Optional sequence of concept tags requested by the user.

    Returns
    -------
    list[Concept]
        Selected concept objects to generate.

    Raises
    ------
    SystemExit
        If any requested tag does not match a defined concept.
    """

    if not requested_tags:
        return list(storybook.concepts)

    normalized_requested = {
        tag.strip().upper() if tag.startswith("<") else f"<{tag.strip().upper()}>"
        for tag in requested_tags
    }
    concept_map = {c.tag: c for c in storybook.concepts}
    unknown_tags = [tag for tag in normalized_requested if tag not in concept_map]
    if unknown_tags:
        available = ", ".join(storybook.concept_tags) or "none"
        raise SystemExit(f"Unknown concept tag(s): {', '.join(unknown_tags)}. Available: {available}")

    return [concept_map[tag] for tag in sorted(normalized_requested) if tag in concept_map]


def generate_artworks(
    story: str,
    provider: str,
    model: str,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    force: bool = False,
    concepts: Sequence[str] | None = None,
    subject_constraints: str | None = None,
    environment_constraints: str | None = None,
) -> None:
    """Generate concept reference artworks for a storybook."""
    workspace = StoryWorkspace.from_story(story)

    logger.info("Starting artwork generation for story '%s'.", workspace.story)
    story_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)

    target_concepts = resolve_target_concepts(
        storybook=storybook,
        requested_tags=concepts,
    )

    artworks_directory = workspace.artworks_dir
    artworks_directory.mkdir(parents=True, exist_ok=True)

    client = build_image_client(
        provider=provider,
        model=model,
        aspect_ratio=aspect_ratio,
        image_size=resolution,
    )

    total_items = len(target_concepts)
    logger.info(
        "Starting generation for story '%s' with %d artwork(s).",
        workspace.story,
        total_items,
    )

    completed_index = 0
    for concept_index, concept in enumerate(target_concepts, start=1):
        completed_index = concept_index
        if concept.image_path.strip():
            output_path = workspace.directory / concept.image_path.strip()
        else:
            slug = slugify_tag(concept.tag)
            output_path = artworks_directory / f"{slug}.png"

        if not force and output_path.exists():
            logger.info(
                "Item %d/%d: concept %s skipped (artwork already exists at %s).",
                completed_index,
                total_items,
                concept.tag,
                concept.image_path or output_path.relative_to(workspace.directory).as_posix(),
            )
            continue

        logger.info(
            "Item %d/%d: generating artwork for concept %s...",
            completed_index,
            total_items,
            concept.tag,
        )

        concept_constraints = (
            environment_constraints
            if concept.is_environment
            else subject_constraints
        )
        resolved_constraints = resolve_concept_artwork_constraints(
            storybook=storybook,
            concept=concept,
            override=concept_constraints,
        )
        prompt = build_concept_artwork_prompt(
            storybook=storybook,
            concept=concept,
            constraints=resolved_constraints,
        )
        generated_image = client.generate_image(prompt)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generated_image.save(output_path)

        concept.image_path = output_path.relative_to(workspace.directory).as_posix()
        save_storybook(storybook, story_path)

        logger.info(
            "Item %d/%d: concept %s artwork saved to %s.",
            completed_index,
            total_items,
            concept.tag,
            concept.image_path,
        )

    logger.info("Artwork generation complete.")
