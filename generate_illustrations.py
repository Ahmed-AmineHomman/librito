"""Generate illustrations for a segmented storybook."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from librito.generate_illustrations import generate_story_illustrations


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

    parser = argparse.ArgumentParser(
        description="Generate illustrations for a segmented storybook.",
    )
    parser.add_argument(
        "story_path",
        type=Path,
        help="Path to the story JSON file.",
    )
    arguments = parser.parse_args(argv)
    generate_story_illustrations(arguments.story_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
