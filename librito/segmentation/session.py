"""Filesystem-backed segmentation session management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from librito.models import Storybook
from librito.story_io import load_storybook, save_storybook


@dataclass(frozen=True, slots=True)
class SegmentationSession:
    """Paths used by the segmentation agent during one run.

    Parameters
    ----------
    story_path:
        Path to the source story text file.
    draft_path:
        Path to the mutable segmentation draft JSON file.
    export_path:
        Path to the validated final segmentation JSON file.
    """

    story_path: Path
    draft_path: Path
    export_path: Path

    def load_full_story(self) -> str:
        """Load the raw source story text.

        Returns
        -------
        str
            Story text read from disk.
        """

        return self.story_path.read_text(encoding="utf-8")

    def load_storybook(self) -> Storybook:
        """Load the current draft storybook from disk.

        Returns
        -------
        Storybook
            Parsed draft storybook.
        """

        return load_storybook(self.draft_path)

    def save_storybook(self, storybook: Storybook) -> None:
        """Persist the current draft storybook to disk.

        Parameters
        ----------
        storybook:
            Storybook draft to persist.
        """

        save_storybook(storybook, self.draft_path)

    def ensure_draft_exists(self) -> Storybook:
        """Create an empty draft if none exists yet.

        Returns
        -------
        Storybook
            Existing or newly created draft storybook.
        """

        if self.draft_path.exists():
            return self.load_storybook()

        storybook = Storybook(
            title="",
            style="",
            constraints="",
            recurring_concepts={},
            scenes=[],
        )
        self.save_storybook(storybook)
        return storybook
