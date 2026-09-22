"""CLI subcommand: ``librito assemble``."""

from __future__ import annotations

import logging
from argparse import Namespace, RawDescriptionHelpFormatter, _SubParsersAction
from textwrap import dedent

from librito.assembly import DEFAULT_BACKGROUND_COLOR, DEFAULT_TEXT_COLOR, assemble_book

logger = logging.getLogger(__name__)


def register(subparsers: _SubParsersAction) -> None:
    """Register the ``assemble`` subcommand.

    Parameters
    ----------
    subparsers:
        Parent subparsers action to attach to.
    """

    parser = subparsers.add_parser(
        "assemble",
        help="Assemble a storybook into a fixed-layout EPUB.",
        description=dedent(
            """\
            Assemble a fixed-layout EPUB book from a storybook.

            Validates the required book parts, scene material, and referenced
            illustration files, then renders front matter, scene spreads,
            optional closing pages, and the back cover.
            """
        ).strip(),
        epilog=dedent(
            """\
            Layout:
              - front cover: full-page illustration with optional overlaid title and author
              - front matter: paired spreads with blank filler pages when needed
              - each scene: exactly 2 pages (text left, illustration right)
              - closing matter: optional paired spread before the back cover
              - back cover: teaser page with optional full-page illustration
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
        "--aspect-ratio",
        default="1:1",
        help="Requested image aspect ratio (default: 1:1).",
    )
    parser.add_argument(
        "--background-color",
        default=DEFAULT_BACKGROUND_COLOR,
        help=f"Solid background color for text and blank pages (default: {DEFAULT_BACKGROUND_COLOR}).",
    )
    parser.add_argument(
        "--text-color",
        default=DEFAULT_TEXT_COLOR,
        help=f"Text color for rendered text overlays and text pages (default: {DEFAULT_TEXT_COLOR}).",
    )
    parser.add_argument(
        "--resolution",
        choices=["512", "1k", "2k", "1K", "2K"],
        help="Resolution preset for the generated EPUB images.",
    )
    parser.set_defaults(handler=_handle)


def _handle(arguments: Namespace) -> int:
    """Handle the ``assemble`` subcommand.

    Parameters
    ----------
    arguments:
        Parsed command-line arguments.

    Returns
    -------
    int
        Process exit status.
    """

    assemble_book(
        story=arguments.story,
        aspect_ratio=arguments.aspect_ratio,
        background_color=arguments.background_color,
        text_color=arguments.text_color,
        resolution=arguments.resolution,
    )
    return 0
