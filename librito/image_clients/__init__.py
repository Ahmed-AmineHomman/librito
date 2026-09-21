"""Image generation client abstractions and implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence

from PIL import Image


class ImageClient(Protocol):
    """Protocol for image generation clients."""

    def generate_image(
            self,
            prompt: str,
            images: Sequence[Path | str | Image.Image] = (),
    ) -> Image.Image:
        """Generate a single image from a prompt and optional reference images.

        Parameters
        ----------
        prompt:
            Fully assembled prompt to send to the image generation backend.
        images:
            Optional reference artwork images to guide concept consistency.

        Returns
        -------
        Image.Image
            Generated image.
        """
        ...
