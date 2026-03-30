"""Generate illustrations for a segmented storybook."""

from __future__ import annotations

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
from librito.providers import build_image_client
from librito.prompt_builder import build_render_prompt
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)


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
            Generate illustrations for a segmented storybook.

            Use this after segmentation to turn ``story.json`` scenes into image
            files under ``illustrations/``. By default the script skips scenes
            whose ``image_path`` already points to an existing file, so runs are
            resumable. You can also restrict generation to selected scenes.
            """
        ).strip(),
        epilog=dedent(
            """
            Behavior:
              - reads ``database/<story>/story.json``
              - builds one final prompt per generated scene
              - writes images to ``database/<story>/illustrations/``
              - updates each generated scene's ``image_path`` in place

            Selection:
              - omit --scenes to process the full storybook
              - pass --scenes to generate only selected labels
              - use --force to regenerate scenes even when the image already exists

            Examples:
              python helpers/illustrate_story.py --story leo --provider gemini --model gemini-3.1-flash-image-preview
              python helpers/illustrate_story.py --story leo --provider mock --model mock --scenes scene-01 scene-04
              python helpers/illustrate_story.py --story leo --provider comfyui --model flux1-dev.safetensors --scenes scene-03 --force
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
        help="Regenerate images even when a scene already points to an existing file.",
    )
    parser.add_argument(
        "--scenes",
        action="extend",
        nargs="+",
        type=str,
        help="Optional scene labels to generate. Defaults to all storybook scenes.",
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
    selected_scene_positions = _resolve_scene_positions(
        available_labels=[scene.label for scene in storybook.scenes],
        requested_labels=arguments.scenes,
    )

    output_directory = workspace.illustrations_dir
    output_directory.mkdir(parents=True, exist_ok=True)

    client = build_image_client(
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        image_size=arguments.resolution,
    )

    total_scenes = len(selected_scene_positions)
    logger.info(
        "Starting illustration generation for story '%s' with %d scene(s).",
        workspace.story,
        total_scenes,
    )

    for selection_position, scene_position in enumerate(selected_scene_positions, start=1):
        scene = storybook.scenes[scene_position - 1]
        if not arguments.force and scene.image_path and (workspace.directory / scene.image_path).exists():
            logger.info(
                "Scene %d/%d (%s): skipping (image already exists).",
                selection_position,
                total_scenes,
                scene.label,
            )
            continue

        logger.info(
            "Scene %d/%d (%s): generating illustration...",
            selection_position,
            total_scenes,
            scene.label,
        )

        # Build the final prompt just before generation so the script stays
        # easy to read from top to bottom.
        prompt = build_render_prompt(storybook, scene)
        generated_image = client.generate_image(prompt)

        output_path = output_directory / f"scene-{scene_position:03d}.png"
        generated_image.save(output_path)
        scene.image_path = output_path.relative_to(workspace.directory).as_posix()
        save_storybook(storybook, story_path)

        logger.info(
            "Scene %d/%d (%s): saved to %s.",
            selection_position,
            total_scenes,
            scene.label,
            scene.image_path,
        )

    logger.info("Illustration generation complete.")
    logger.info("Done.")
    return 0


def _resolve_scene_positions(
        available_labels: Sequence[str],
        requested_labels: Sequence[str] | None,
) -> list[int]:
    """Resolve selected scene labels to 1-based scene positions.

    Parameters
    ----------
    available_labels:
        Scene labels present in the storybook, in story order.
    requested_labels:
        Optional scene labels explicitly requested by the caller.

    Returns
    -------
    list[int]
        Selected 1-based scene positions in story order.

    Raises
    ------
    SystemExit
        If any requested scene labels are unknown.
    """

    if not requested_labels:
        return list(range(1, len(available_labels) + 1))

    deduplicated_labels = _deduplicate(requested_labels)
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


def _deduplicate(values: Sequence[str]) -> list[str]:
    """Return values without duplicates while preserving first-seen order.

    Parameters
    ----------
    values:
        Input strings in arbitrary order.

    Returns
    -------
    list[str]
        Deduplicated values.
    """

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
