"""Generate concept and style reference artworks for a storybook."""

from __future__ import annotations

import re
import sys
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from textwrap import dedent
from typing import Sequence

import logging

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.environment import load_repository_environment
from librito.io import load_storybook, save_storybook
from librito.logging import add_logging_arguments, configure_logging
from librito.models import Concept, Storybook
from librito.prompt_builder import build_concept_artwork_prompt, build_style_artwork_prompt
from librito.providers import build_image_client
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)

STYLE_ARTWORK_FILENAME = "style-reference.png"


def load_parameters(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command-line arguments.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    Namespace
        Parsed command-line arguments.
    """

    parser = ArgumentParser(
        description=dedent(
            """
            Generate concept and style reference artworks for a storybook.

            Artworks are a mandatory preliminary step before scene illustration.
            They provide concrete visual references (image anchors) for recurring
            concepts and the global artistic style.

            By default, this script generates reference artworks for all concepts
            defined in story.json and saves them under database/<story>/artworks/.
            """
        ).strip(),
        epilog=dedent(
            """
            Examples:
              python helpers/illustrate_artworks.py --story leo --provider gemini --model gemini-3.1-flash-image-preview
              python helpers/illustrate_artworks.py --story leo --provider mock --model mock
              python helpers/illustrate_artworks.py --story leo --provider mock --model mock --concepts "<LEO>" "<TOY_CAR>"
              python helpers/illustrate_artworks.py --story leo --provider mock --model mock --style
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    add_logging_arguments(parser)
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story folder name under ./database/<story>/.",
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["gemini", "comfyui", "mock"],
        help="Image generation provider.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Image model identifier. For ComfyUI, this is the checkpoint filename.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        help="Requested image aspect ratio.",
    )
    parser.add_argument(
        "--resolution",
        default="1K",
        help='Requested image resolution: "0.5K", "1K", or "2K".',
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate artworks even when an image file already exists.",
    )
    parser.add_argument(
        "--concepts",
        action="extend",
        nargs="+",
        type=str,
        help="Optional concept tags to generate (e.g. '<LEO>' or 'LEO').",
    )
    parser.add_argument(
        "--style",
        action="store_true",
        help="Also generate the global style reference artwork.",
    )
    parser.add_argument(
        "--constraints",
        type=str,
        default=None,
        help="Optional constraints overriding storybook artworks_constraints and default concept artwork constraints.",
    )
    return parser.parse_args(argv)


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


def main(argv: Sequence[str] | None = None) -> int:
    """Run the artwork generation entrypoint.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    int
        Process exit status.
    """

    load_repository_environment()
    arguments = load_parameters(argv)
    configure_logging(arguments.log_level)
    workspace = StoryWorkspace.from_story(arguments.story)

    logger.info("Starting artwork generation for story '%s'.", workspace.story)
    story_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)

    target_concepts = resolve_target_concepts(
        storybook=storybook,
        requested_tags=arguments.concepts,
    )

    artworks_directory = workspace.artworks_dir
    artworks_directory.mkdir(parents=True, exist_ok=True)

    client = build_image_client(
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        image_size=arguments.resolution,
    )

    total_items = len(target_concepts) + (1 if arguments.style else 0)
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

        if not arguments.force and output_path.exists():
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

        prompt = build_concept_artwork_prompt(
            storybook=storybook,
            concept=concept,
            constraints=arguments.constraints,
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

    if arguments.style:
        completed_index += 1
        if storybook.style_image_path.strip():
            output_path = workspace.directory / storybook.style_image_path.strip()
        else:
            output_path = artworks_directory / STYLE_ARTWORK_FILENAME

        if not arguments.force and output_path.exists():
            logger.info(
                "Item %d/%d: style artwork skipped (already exists at %s).",
                completed_index,
                total_items,
                storybook.style_image_path or output_path.relative_to(workspace.directory).as_posix(),
            )
        else:
            logger.info(
                "Item %d/%d: generating style reference artwork...",
                completed_index,
                total_items,
            )
            prompt = build_style_artwork_prompt(storybook)
            generated_image = client.generate_image(prompt)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            generated_image.save(output_path)

            storybook.style_image_path = output_path.relative_to(workspace.directory).as_posix()
            save_storybook(storybook, story_path)

            logger.info(
                "Item %d/%d: style reference artwork saved to %s.",
                completed_index,
                total_items,
                storybook.style_image_path,
            )

    logger.info("Artwork generation complete.")
    logger.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
