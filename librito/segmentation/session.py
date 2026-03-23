"""Filesystem-backed segmentation session management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
