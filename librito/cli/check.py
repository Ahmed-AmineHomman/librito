"""CLI subcommand group: ``librito check``."""

from __future__ import annotations

import logging
import sys
from argparse import Namespace, RawDescriptionHelpFormatter, _SubParsersAction
from textwrap import dedent

from librito.reporting.anchoring import build_anchor_report
from librito.reporting.semantic import build_semantic_report

logger = logging.getLogger(__name__)


def register(subparsers: _SubParsersAction) -> None:
    """Register the ``check`` subcommand group.

    Parameters
    ----------
    subparsers:
        Parent subparsers action to attach to.
    """

    group_parser = subparsers.add_parser(
        "check",
        help="Run consistency checks on a storybook.",
        description="Run consistency checks on a segmented storybook.",
        formatter_class=RawDescriptionHelpFormatter,
    )
    group_subparsers = group_parser.add_subparsers(
        dest="check_subcommand",
        title="subcommands",
    )
    group_parser.set_defaults(handler=lambda _args: (group_parser.print_help(), 2)[1])

    _register_anchoring(group_subparsers)
    _register_semantic(group_subparsers)


# ── anchoring ────────────────────────────────────────────────────────────────


def _register_anchoring(subparsers: _SubParsersAction) -> None:
    """Register the ``check anchoring`` subcommand."""

    parser = subparsers.add_parser(
        "anchoring",
        help="Check concept anchor usage consistency.",
        description=dedent(
            """\
            Check whether concept anchors are used consistently.

            Validates the relationship between defined concepts and the anchor
            tags referenced inside scene prompts.
            """
        ).strip(),
        epilog=dedent(
            """\
            Detail modes:
              summary   Global counts and pass/fail checks only.
              selected  Global summary plus the anchors listed with --anchors.
              all       Global summary plus every anchor.
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
        "--details",
        default="summary",
        choices=["summary", "selected", "all"],
        help="Report detail level (default: summary).",
    )
    parser.add_argument(
        "--anchors",
        action="extend",
        nargs="+",
        type=str,
        help="Anchor tags to expand when --details selected is used.",
    )
    parser.set_defaults(handler=_handle_anchoring)


def _handle_anchoring(arguments: Namespace) -> int:
    """Handle the ``check anchoring`` subcommand."""

    if arguments.details == "selected" and not arguments.anchors:
        raise SystemExit("--anchors is required when --details selected is used.")
    if arguments.details != "selected" and arguments.anchors:
        raise SystemExit("--anchors can only be used with --details selected.")

    report = build_anchor_report(
        story=arguments.story,
        details=arguments.details,
        anchors=arguments.anchors,
    )
    sys.stdout.write(report + "\n")
    return 0


# ── semantic ─────────────────────────────────────────────────────────────────


def _register_semantic(subparsers: _SubParsersAction) -> None:
    """Register the ``check semantic`` subcommand."""

    parser = subparsers.add_parser(
        "semantic",
        help="Check semantic consistency between scenes and units.",
        description=dedent(
            """\
            Check how well storybook scenes align with units.

            Computes global scores across the full story, then optionally
            expands selected scenes for closer inspection.
            """
        ).strip(),
        epilog=dedent(
            """\
            Detail modes:
              summary   Global score summary only.
              selected  Global summary plus the scenes listed with --scenes.
              all       Global summary plus every scene.
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
        "--provider",
        required=True,
        choices=["gemini", "lms", "mock"],
        help="Embedding provider for computing scene and unit embeddings.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Embedding model identifier for the selected provider.",
    )
    parser.add_argument(
        "--details",
        default="summary",
        choices=["summary", "selected", "all"],
        help="Report detail level (default: summary).",
    )
    parser.add_argument(
        "--scenes",
        action="extend",
        nargs="+",
        type=str,
        help="Scene labels to expand when --details selected is used.",
    )
    parser.set_defaults(handler=_handle_semantic)


def _handle_semantic(arguments: Namespace) -> int:
    """Handle the ``check semantic`` subcommand."""

    if arguments.details == "selected" and not arguments.scenes:
        raise SystemExit("--scenes is required when --details selected is used.")
    if arguments.details != "selected" and arguments.scenes:
        raise SystemExit("--scenes can only be used with --details selected.")

    report = build_semantic_report(
        story=arguments.story,
        provider=arguments.provider,
        model=arguments.model,
        details=arguments.details,
        scenes=arguments.scenes,
    )
    sys.stdout.write(report + "\n")
    return 0
