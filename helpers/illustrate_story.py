"""Generate illustrations for a storybook."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Sequence

import logging

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.environment import load_repository_environment
from librito.io import load_storybook, save_storybook
from librito.logging import add_logging_arguments, configure_logging
from librito.models import PageSpec, Storybook
from librito.prompt_builder import build_render_prompt, build_render_prompt_from_text, resolve_scene_constraints
from librito.providers import build_image_client
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)

ILLUSTRATED_PARTS_IN_ORDER = [
    "front_cover",
    "front_endpaper",
    "frontispiece",
    "title_page",
    "closing_illustration",
    "back_cover",
]
PART_OUTPUT_NAMES = {
    "front_cover": "front-cover.png",
    "front_endpaper": "front-endpaper.png",
    "frontispiece": "frontispiece.png",
    "title_page": "title-page.png",
    "closing_illustration": "closing-illustration.png",
    "back_cover": "back-cover.png",
}
PART_DISPLAY_NAMES = {
    "front_cover": "Front cover",
    "front_endpaper": "Front endpaper",
    "frontispiece": "Frontispiece",
    "title_page": "Title page",
    "closing_illustration": "Closing illustration",
    "back_cover": "Back cover",
}


@dataclass(slots=True)
class IllustratedPartSelection:
    """Selection metadata for one illustrated non-scene book part.

    Parameters
    ----------
    name:
        Canonical storybook part name.
    page:
        Page specification containing the illustration to generate.
    """

    name: str
    page: PageSpec


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
            Generate illustrations for a storybook.

            Use this after segmentation to turn ``story.json`` scene prompts and
            any configured non-scene page prompts into image files under
            ``illustrations/``. By default the script skips items whose
            ``image_path`` already points to an existing file, so runs are
            resumable.
            """
        ).strip(),
        epilog=dedent(
            """
            Behavior:
              - reads ``database/<story>/story.json``
              - builds one render prompt per generated scene or book part
              - writes images to ``database/<story>/illustrations/``
              - updates each generated ``image_path`` in place

            Selection:
              - omit both --scenes and --parts to process all scenes and all illustrated book parts
              - pass --scenes to generate only selected scene labels
              - pass --parts to generate only selected illustrated book parts
              - use --force to regenerate items even when the image already exists

            Examples:
              python helpers/illustrate_story.py --story leo --provider gemini --model gemini-3.1-flash-image-preview
              python helpers/illustrate_story.py --story leo --provider mock --model mock --scenes scene-01 scene-04
              python helpers/illustrate_story.py --story leo --provider mock --model mock --parts front_cover back_cover
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
        help="Regenerate images even when an item already points to an existing file.",
    )
    parser.add_argument(
        "--scenes",
        action="extend",
        nargs="+",
        type=str,
        help="Optional scene labels to generate.",
    )
    parser.add_argument(
        "--parts",
        action="extend",
        nargs="+",
        type=str,
        help="Optional illustrated book-part names to generate.",
    )
    parser.add_argument(
        "--constraints",
        type=str,
        default=None,
        help="Optional constraints overriding storybook constraints and default prompt constraints.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the illustration generation entrypoint.

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

    logger.info("Starting illustration pipeline for story '%s'.", workspace.story)
    story_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)

    selected_scene_positions = resolve_scene_positions(
        storybook=storybook,
        requested_labels=arguments.scenes,
        requested_parts=arguments.parts,
    )
    selected_parts = resolve_illustrated_parts(
        storybook=storybook,
        requested_parts=arguments.parts,
        requested_scenes=arguments.scenes,
    )

    output_directory = workspace.illustrations_dir
    output_directory.mkdir(parents=True, exist_ok=True)

    client = build_image_client(
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        image_size=arguments.resolution,
    )

    total_items = len(selected_scene_positions) + len(selected_parts)
    logger.info(
        "Starting illustration generation for story '%s' with %d item(s).",
        workspace.story,
        total_items,
    )

    scene_constraints = resolve_scene_constraints(
        storybook=storybook,
        override=arguments.constraints,
    )

    completed_index = 0
    for selection_position, scene_position in enumerate(selected_scene_positions, start=1):
        scene = storybook.scenes[scene_position - 1]
        completed_index = selection_position
        if not arguments.force and scene.image_path and (workspace.directory / scene.image_path).exists():
            logger.info(
                "Item %d/%d: scene %s skipped (image already exists).",
                completed_index,
                total_items,
                scene.label,
            )
            continue

        logger.info(
            "Item %d/%d: generating scene %s...",
            completed_index,
            total_items,
            scene.label,
        )

        render_prompt = build_render_prompt(
            storybook=storybook,
            scene=scene,
            constraints=scene_constraints,
            workspace_dir=workspace.directory,
        )
        generated_image = client.generate_image(
            prompt=render_prompt.text,
            images=render_prompt.image_paths,
        )

        output_path = output_directory / f"scene-{scene_position:03d}.png"
        generated_image.save(output_path)
        scene.image_path = output_path.relative_to(workspace.directory).as_posix()
        save_storybook(storybook, story_path)

        logger.info(
            "Item %d/%d: scene %s saved to %s.",
            completed_index,
            total_items,
            scene.label,
            scene.image_path,
        )

    for part_index, selection in enumerate(selected_parts, start=1):
        completed_index = len(selected_scene_positions) + part_index
        illustration = selection.page.illustration
        if illustration is None:
            continue

        if not arguments.force and illustration.image_path and (workspace.directory / illustration.image_path).exists():
            logger.info(
                "Item %d/%d: %s skipped (image already exists).",
                completed_index,
                total_items,
                PART_DISPLAY_NAMES[selection.name],
            )
            continue

        logger.info(
            "Item %d/%d: generating %s...",
            completed_index,
            total_items,
            PART_DISPLAY_NAMES[selection.name],
        )

        render_prompt = build_render_prompt_from_text(
            storybook=storybook,
            prompt=illustration.prompt,
            constraints=scene_constraints,
            workspace_dir=workspace.directory,
        )
        generated_image = client.generate_image(
            prompt=render_prompt.text,
            images=render_prompt.image_paths,
        )

        output_path = output_directory / PART_OUTPUT_NAMES[selection.name]
        generated_image.save(output_path)
        illustration.image_path = output_path.relative_to(workspace.directory).as_posix()
        save_storybook(storybook, story_path)

        logger.info(
            "Item %d/%d: %s saved to %s.",
            completed_index,
            total_items,
            PART_DISPLAY_NAMES[selection.name],
            illustration.image_path,
        )

    logger.info("Illustration generation complete.")
    logger.info("Done.")
    return 0


def resolve_scene_positions(
    storybook: Storybook,
    requested_labels: Sequence[str] | None,
    requested_parts: Sequence[str] | None,
) -> list[int]:
    """Resolve selected scene labels to 1-based scene positions."""

    available_labels = [scene.label for scene in storybook.scenes]
    if requested_labels is None:
        if requested_parts is not None:
            return []
        return list(range(1, len(available_labels) + 1))

    deduplicated_labels = deduplicate(requested_labels)
    available_label_set = set(available_labels)
    unknown_labels = [label for label in deduplicated_labels if label not in available_label_set]
    if unknown_labels:
        raise SystemExit(f"Unknown scene label(s): {', '.join(unknown_labels)}")

    requested_label_set = set(deduplicated_labels)
    return [
        position
        for position, label in enumerate(available_labels, start=1)
        if label in requested_label_set
    ]


def resolve_illustrated_parts(
    storybook: Storybook,
    requested_parts: Sequence[str] | None,
    requested_scenes: Sequence[str] | None,
) -> list[IllustratedPartSelection]:
    """Resolve illustrated book parts to generate."""

    available_parts = {
        name: page
        for name, page in _iter_available_illustrated_parts(storybook)
    }
    if requested_parts is None:
        if requested_scenes is not None:
            return []
        return [
            IllustratedPartSelection(name=name, page=page)
            for name, page in _iter_available_illustrated_parts(storybook)
        ]

    deduplicated_parts = deduplicate(requested_parts)
    unknown_parts = [name for name in deduplicated_parts if name not in available_parts]
    if unknown_parts:
        available_names = ", ".join(available_parts) or "none"
        raise SystemExit(
            "Unknown or unavailable illustrated part(s): "
            f"{', '.join(unknown_parts)}. Available illustrated parts: {available_names}."
        )

    return [
        IllustratedPartSelection(name=name, page=available_parts[name])
        for name in deduplicated_parts
    ]


def _iter_available_illustrated_parts(storybook: Storybook) -> list[tuple[str, PageSpec]]:
    """Return illustrated book parts in canonical order."""

    selections: list[tuple[str, PageSpec]] = []
    for name in ILLUSTRATED_PARTS_IN_ORDER:
        page = getattr(storybook.parts, name)
        if page is None or page.illustration is None:
            continue
        selections.append((name, page))
    return selections


def deduplicate(values: Sequence[str]) -> list[str]:
    """Return values without duplicates while preserving first-seen order."""

    ordered_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            continue
        seen_values.add(value)
        ordered_values.append(value)
    return ordered_values


if __name__ == "__main__":
    raise SystemExit(main())
