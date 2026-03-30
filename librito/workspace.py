"""Workspace resolution for canonical story artifacts stored in ``database/``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DATABASE_ROOT = Path(__file__).resolve().parent.parent / "database"
STORY_FILE_NAME = "story.md"
STORYBOOK_FILE_NAME = "story.json"
BOOK_FILE_NAME = "story.epub"
UNITS_FILE_NAME = "units.json"
ILLUSTRATIONS_DIRECTORY_NAME = "illustrations"


@dataclass(frozen=True, slots=True)
class StoryWorkspace:
    """Filesystem workspace for one canonical story entry.

    Parameters
    ----------
    story:
        Story identifier used as the directory name under ``database/``.
    directory:
        Root directory for the story workspace.
    story_file:
        Canonical source story file path.
    storybook_file:
        Canonical storybook export path.
    book_file:
        Canonical assembled book output path.
    units_file:
        Canonical units path.
    illustrations_dir:
        Canonical illustration output directory.
    """

    story: str
    directory: Path
    story_file: Path
    storybook_file: Path
    book_file: Path
    units_file: Path
    illustrations_dir: Path

    @classmethod
    def from_story(cls, story: str) -> StoryWorkspace:
        """Build the canonical workspace for a story identifier.

        Parameters
        ----------
        story:
            Story identifier, for example ``"calmio"``.

        Returns
        -------
        StoryWorkspace
            Resolved workspace paths for the story.

        Raises
        ------
        SystemExit
            If the provided story identifier looks like a filesystem path
            instead of a story name.
        """

        story_name = _validate_story_name(story)
        directory = DATABASE_ROOT / story_name
        return cls(
            story=story_name,
            directory=directory,
            story_file=directory / STORY_FILE_NAME,
            storybook_file=directory / STORYBOOK_FILE_NAME,
            book_file=directory / BOOK_FILE_NAME,
            units_file=directory / UNITS_FILE_NAME,
            illustrations_dir=directory / ILLUSTRATIONS_DIRECTORY_NAME,
        )

    def ensure_directory(self) -> None:
        """Create the story directory when it does not already exist."""

        self.directory.mkdir(parents=True, exist_ok=True)

    def require_directory(self) -> Path:
        """Return the story directory if it exists.

        Returns
        -------
        Path
            Existing story directory path.

        Raises
        ------
        SystemExit
            If the story directory is missing.
        """

        if not self.directory.is_dir():
            raise SystemExit(f"Missing story directory: {self.directory}")
        return self.directory

    def require_story_file(self) -> Path:
        """Return the canonical source story file if it exists."""

        return _require_file(self.story_file)

    def require_storybook_file(self) -> Path:
        """Return the canonical storybook file if it exists."""

        return _require_file(self.storybook_file)

    def require_book_file(self) -> Path:
        """Return the canonical book file if it exists."""

        return _require_file(self.book_file)

    def require_units_file(self) -> Path:
        """Return the canonical units file if it exists."""

        return _require_file(self.units_file)


def _validate_story_name(story: str) -> str:
    """Validate a story identifier used under ``database/``.

    Parameters
    ----------
    story:
        User-provided story identifier.

    Returns
    -------
    str
        Normalized story identifier.

    Raises
    ------
    SystemExit
        If the input is empty or looks like a filesystem path.
    """

    story_name = story.strip()
    if not story_name:
        raise SystemExit("Story identifier must be a non-empty string.")
    if story_name in {".", ".."}:
        raise SystemExit(f"Invalid story identifier: {story!r}.")
    if Path(story_name).name != story_name:
        raise SystemExit(
            f"Expected a story identifier such as 'calmio', not a path like {story!r}."
        )
    return story_name


def _require_file(path: Path) -> Path:
    """Return an existing file path or abort with a clear message.

    Parameters
    ----------
    path:
        Expected file path.

    Returns
    -------
    Path
        Existing file path.

    Raises
    ------
    SystemExit
        If the file is missing.
    """

    if not path.is_file():
        raise SystemExit(f"Missing required file: {path}")
    return path
