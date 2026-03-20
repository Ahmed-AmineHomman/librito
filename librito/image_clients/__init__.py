"""Image generation client abstractions and implementations."""

from __future__ import annotations

from typing import Protocol

from PIL import Image


class ImageClient(Protocol):
    """Protocol for image generation clients."""

    def generate_image(self, prompt: str) -> Image.Image:
        """Generate a single image from a text prompt.

        Parameters
        ----------
        prompt:
            Fully assembled prompt to send to the image generation backend.

        Returns
        -------
        Image.Image
            Generated image.
        """
        ...
