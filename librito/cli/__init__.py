"""Unified command-line interface for librito.

This package defines the argument parsers, subcommand routing, and handler
functions for the ``librito.py`` entrypoint.  Business logic lives in sibling
library modules; CLI modules are thin routing layers only.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from textwrap import dedent
from typing import Sequence

from librito.environment import load_repository_environment
from librito.logging import configure_logging

from librito.cli import init as _init
from librito.cli import assemble as _assemble
from librito.cli import illustrate as _illustrate
from librito.cli import check as _check
from librito.cli import inspect as _inspect

_LOG_LEVEL_NAMES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def build_parser() -> ArgumentParser:
    """Build the top-level argument parser with all subcommands.

    Returns
    -------
    ArgumentParser
        Fully configured argument parser.
    """

    parser = ArgumentParser(
        prog="librito",
        description=dedent(
            """\
            Librito — transform stories into structured, illustrated storybooks.

            Use one of the subcommands below to initialize a story workspace,
            generate illustrations, run consistency checks, inspect story data,
            or assemble the final EPUB book.
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--log-level",
        choices=_LOG_LEVEL_NAMES,
        default="INFO",
        help="Logging verbosity (default: INFO).",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
    )

    _init.register(subparsers)
    _illustrate.register(subparsers)
    _assemble.register(subparsers)
    _check.register(subparsers)
    _inspect.register(subparsers)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the librito CLI entrypoint.

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
    parser = build_parser()
    arguments = parser.parse_args(argv)
    configure_logging(arguments.log_level)

    handler = getattr(arguments, "handler", None)
    if handler is None:
        parser.print_help()
        return 2

    return handler(arguments)
