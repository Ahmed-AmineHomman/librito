"""Shared environment-loading helpers for repository entrypoints."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DOTENV_FILE = REPOSITORY_ROOT / ".env"


def load_repository_environment() -> bool:
    """Load the repository ``.env`` file into the current process.

    Returns
    -------
    bool
        ``True`` when the dotenv file is found and loaded, ``False`` otherwise.

    Notes
    -----
    Existing process environment variables are preserved. This allows callers
    to override values explicitly while still benefiting from repository-local
    defaults stored in ``.env``.
    """

    return load_dotenv(dotenv_path=DOTENV_FILE, override=False)
