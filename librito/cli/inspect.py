"""CLI subcommand group: ``librito inspect``."""

from __future__ import annotations

import logging
import sys
from argparse import Namespace, RawDescriptionHelpFormatter, _SubParsersAction
from textwrap import dedent

from librito.reporting.scene import build_scene_report

logger = logging.getLogger(__name__)


def register(subparsers: _SubParsersAction) -> None:
    """Register the ``inspect`` subcommand group.

    Parameters
    ----------
    subparsers:
        Parent subparsers action to attach to.
    """

    group_parser = subparsers.add_parser(
        "inspect",
        help="Inspect story data.",
        description="Inspect storybook scenes and their attributes.",
        formatter_class=RawDescriptionHelpFormatter,
    )
    group_subparsers = group_parser.add_subparsers(
        dest="inspect_subcommand",
        title="subcommands",
    )
    group_parser.set_defaults(handler=lambda _args: (group_parser.print_help(), 2)[1])

    _register_scene(group_subparsers)


# ── scene ────────────────────────────────────────────────────────────────────


def _register_scene(subparsers: _SubParsersAction) -> None:
    """Register the ``inspect scene`` subcommand."""

    parser = subparsers.add_parser(
        "scene",
        help="Inspect scene text and prompts.",
        description=dedent(
            """\
            Inspect one or more scenes from a segmented storybook.

            Prints the scene text, the raw prompt, or the resolved prompt
            with anchors expanded to their descriptions.
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
        "--scenes",
        required=True,
        action="extend",
        nargs="+",
        type=str,
        help="Scene labels to inspect.",
    )
    parser.add_argument(
        "--attributes",
        required=True,
        action="extend",
        nargs="+",
        choices=["text", "prompt"],
        type=str,
        help="Scene attributes to print for each selected scene.",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Resolve prompt anchors before printing. Only valid with 'prompt'.",
    )
    parser.set_defaults(handler=_handle_scene)


def _handle_scene(arguments: Namespace) -> int:
    """Handle the ``inspect scene`` subcommand."""

    report = build_scene_report(
        story=arguments.story,
        scenes=arguments.scenes,
        attributes=arguments.attributes,
        expand_prompts=arguments.expand,
    )
    sys.stdout.write(report + "\n")
    return 0
