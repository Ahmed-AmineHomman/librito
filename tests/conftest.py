"""Shared test helpers for the librito test suite."""

from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import uuid4


@contextmanager
def workspace_temporary_directory() -> Iterator[Path]:
    """Create a temporary directory inside the repository workspace.

    Yields
    ------
    Path
        Temporary directory rooted in the current workspace.
    """

    base_directory = Path.cwd() / ".tmp-tests"
    temporary_directory = base_directory / uuid4().hex
    temporary_directory.mkdir(parents=True, exist_ok=False)
    try:
        yield temporary_directory
    finally:
        shutil.rmtree(temporary_directory, ignore_errors=True)
