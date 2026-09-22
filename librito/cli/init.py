"""CLI subcommand: ``librito init``."""

from __future__ import annotations

import logging
from argparse import Namespace, RawDescriptionHelpFormatter, _SubParsersAction
from textwrap import dedent

from librito.initialization import initialize_story_workspace

logger = logging.getLogger(__name__)


def register(subparsers: _SubParsersAction) -> None:
    """Register the ``init`` subcommand.

    Parameters
    ----------
    subparsers:
        Parent subparsers action to attach to.
    """

    parser = subparsers.add_parser(
        "init",
        help="Initialize a new story workspace.",
        description=dedent(
            """\
            Initialize a canonical story workspace from a source story file.

            Creates ``database/<story>/``, copies the source story into the
            canonical location, seeds empty ``story.json`` and ``units.json``
            artifacts, and creates the ``illustrations/`` and ``artworks/``
            directories.
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
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
    parser.set_defaults(handler=_handle)


def _handle(arguments: Namespace) -> int:
    """Handle the ``init`` subcommand.

    Parameters
    ----------
    arguments:
        Parsed command-line arguments.

    Returns
    -------
    int
        Process exit status.
    """

    workspace = initialize_story_workspace(
        story=arguments.story,
        filepath=arguments.filepath,
    )
    logger.info("Initialization complete for story '%s'.", workspace.story)
    return 0
