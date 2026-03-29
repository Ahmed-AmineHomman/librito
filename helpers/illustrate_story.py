"""Generate illustrations for a segmented storybook."""

from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.io import load_storybook, save_storybook
from librito.logging import add_logging_arguments, configure_logging
from librito.providers import build_image_client
from librito.prompt_builder import build_scene_prompt
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)


def load_parameters(argv: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser(
        description="Generate illustrations for a segmented storybook.",
    )
    add_logging_arguments(parser)
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story identifier stored under ./database/<story>/.",
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
        help="Image aspect ratio (default: 1:1).",
    )
    parser.add_argument(
        "--resolution",
        default="1K",
        help='Overall image resolution: "0.5K", "1K", or "2K" (default: 1K).',
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate images even when a scene already points to an existing file.",
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

    arguments = load_parameters(argv)
    configure_logging(arguments.log_level)
    workspace = StoryWorkspace.from_story(arguments.story)

    logger.info("Starting illustration pipeline for story '%s'.", workspace.story)
    story_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)

    output_directory = workspace.illustrations_dir
    output_directory.mkdir(parents=True, exist_ok=True)

    client = build_image_client(
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        image_size=arguments.resolution,
    )

    total_scenes = len(storybook.scenes)
    logger.info(
        "Starting illustration generation for story '%s' with %d scene(s).",
        workspace.story,
        total_scenes,
    )

    for scene_position, scene in enumerate(storybook.scenes, start=1):
        if not arguments.force and scene.image_path and (workspace.directory / scene.image_path).exists():
            logger.info(
                "Scene %d/%d (%s): skipping (image already exists).",
                scene_position,
                total_scenes,
                scene.label,
            )
            continue

        logger.info(
            "Scene %d/%d (%s): generating illustration...",
            scene_position,
            total_scenes,
            scene.label,
        )

        # Build the final prompt just before generation so the script stays
        # easy to read from top to bottom.
        prompt = build_scene_prompt(storybook, scene)
        generated_image = client.generate_image(prompt)

        output_path = output_directory / f"scene-{scene_position:03d}.png"
        generated_image.save(output_path)
        scene.image_path = output_path.relative_to(workspace.directory).as_posix()
        save_storybook(storybook, story_path)

        logger.info(
            "Scene %d/%d (%s): saved to %s.",
            scene_position,
            total_scenes,
            scene.label,
            scene.image_path,
        )

    logger.info("Illustration generation complete.")
    logger.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
