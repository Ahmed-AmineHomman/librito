"""Initialize a canonical story workspace under ``database/``."""

from __future__ import annotations

import shutil
import sys
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from textwrap import dedent
from typing import Sequence

import logging

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.environment import load_repository_environment
from librito.io import save_storybook, save_units
from librito.logging import add_logging_arguments, configure_logging
from librito.models import BookParts, IllustrationSpec, PageSpec, Storybook, Units
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
            Initialize a canonical story workspace from a source story file.

            The initializer creates ``database/<story>/``, copies the source
            story into the canonical story filename, seeds empty ``story.json``
            and ``units.json`` artifacts, and creates the ``illustrations/``
            directory so the agent can start from a known-good workspace.
            """
        ).strip(),
        epilog=dedent(
            """
            Behavior:
              - validates that the story name is available
              - copies the provided source file into the canonical story path
              - writes schema-valid empty storybook and units files
              - creates the illustrations directory

            Examples:
              python helpers/initialize.py --story absurd_dog --filepath story.md
              .\\.venv\\Scripts\\python.exe helpers/initialize.py --story absurd_dog --filepath story.md
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
        "--filepath",
        required=True,
        type=str,
        help="Path to the source story file to copy into the workspace.",
    )
    return parser.parse_args(argv)


def initialize_story_workspace(story: str, filepath: str) -> StoryWorkspace:
    """Create a canonical workspace for a new story.

    Parameters
    ----------
    story:
        Story identifier used under ``database/``.
    filepath:
        Source story file path.

    Returns
    -------
    StoryWorkspace
        Initialized story workspace.

    Raises
    ------
    SystemExit
        If the story already exists or the source story path is invalid.
    """

    workspace = StoryWorkspace.from_story(story)
    source_path = Path(filepath).expanduser().resolve()

    if workspace.directory.exists():
        raise SystemExit(f"Story directory already exists: {workspace.directory}")
    if not source_path.exists():
        raise SystemExit(f"Source story file does not exist: {source_path}")
    if not source_path.is_file():
        raise SystemExit(f"Source story path is not a file: {source_path}")

    logger.info("Initializing story workspace '%s' in %s.", workspace.story, workspace.directory)
    workspace.ensure_directory()

    try:
        shutil.copy2(source_path, workspace.story_file)
        save_storybook(
            Storybook(
                title="",
                author="",
                style="",
                constraints="",
                concepts=[],
                parts=BookParts(
                    front_cover=PageSpec(
                        illustration=IllustrationSpec(
                            prompt="",
                            image_path="",
                            text_mode="overlay",
                        )
                    ),
                    title_page=PageSpec(),
                    back_cover=PageSpec(),
                ),
                scenes=[],
            ),
            workspace.storybook_file,
        )
        save_units(
            Units(units=[]),
            workspace.units_file,
        )
        workspace.illustrations_dir.mkdir(parents=True, exist_ok=True)
        workspace.artworks_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        shutil.rmtree(workspace.directory, ignore_errors=True)
        raise

    logger.info("Copied source story to %s.", workspace.story_file)
    logger.info("Created empty storybook at %s.", workspace.storybook_file)
    logger.info("Created empty units file at %s.", workspace.units_file)
    logger.info("Created illustrations directory at %s.", workspace.illustrations_dir)
    logger.info("Created artworks directory at %s.", workspace.artworks_dir)
    return workspace


def main(argv: Sequence[str] | None = None) -> int:
    """Run the workspace initialization entrypoint.

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
    workspace = initialize_story_workspace(
        story=arguments.story,
        filepath=arguments.filepath,
    )
    logger.info("Initialization complete for story '%s'.", workspace.story)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
