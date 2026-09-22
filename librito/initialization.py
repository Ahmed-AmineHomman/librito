"""Story workspace initialization."""

from __future__ import annotations

import shutil
from pathlib import Path

import logging

from librito.io import save_storybook, save_units
from librito.models import BookParts, IllustrationSpec, PageSpec, Storybook, Units
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)


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
                subject_artworks_constraints="",
                environment_artworks_constraints="",
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
