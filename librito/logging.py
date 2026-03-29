"""Shared logging helpers for command-line entrypoints."""

from __future__ import annotations

import sys
from argparse import ArgumentParser

import logging

_LOG_LEVEL_NAMES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def add_logging_arguments(parser: ArgumentParser) -> None:
    """Register standard logging-related CLI arguments.

    Parameters
    ----------
    parser:
        Argument parser to extend in-place.
    """

    parser.add_argument(
        "--log-level",
        choices=_LOG_LEVEL_NAMES,
        default="INFO",
        help="Logging verbosity (default: INFO).",
    )


def configure_logging(log_level: str) -> None:
    """Configure the root logger for CLI usage.

    Parameters
    ----------
    log_level:
        Logging verbosity name accepted by :mod:`logging`.
    """

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
