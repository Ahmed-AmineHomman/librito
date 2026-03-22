"""Mock image generation client producing pixel-noise images."""

from __future__ import annotations

import random
from dataclasses import dataclass

from PIL import Image

from librito.image_clients.utils import compute_dimensions


@dataclass(frozen=True, slots=True)
class MockImageClientConfig:
    """Configuration for the mock image generation client.

    Parameters
    ----------
    aspect_ratio:
        Target image aspect ratio.
    image_size:
        Target image size label determining the longest side in pixels.
    """

    aspect_ratio: str = "1:1"
    image_size: str = "1K"


class MockImageClient:
    """Image client that returns random pixel-noise images.

    Useful for testing the illustration pipeline without calling a real API.
    """

    def __init__(self, config: MockImageClientConfig | None = None) -> None:
        """Initialize the mock client.

        Parameters
        ----------
        config:
            Optional configuration overriding default aspect ratio and size.
        """

        self._config = config or MockImageClientConfig()
        self._width, self._height = compute_dimensions(
            self._config.aspect_ratio,
            self._config.image_size,
        )

    def generate_image(self, prompt: str) -> Image.Image:
        """Generate a random pixel-noise image.

        Parameters
        ----------
        prompt:
            Prompt string (ignored; present for interface compatibility).

        Returns
        -------
        Image.Image
            Random noise image with the configured dimensions.
        """

        pixels = bytes(random.randint(0, 255) for _ in range(self._width * self._height * 3))
        return Image.frombytes("RGB", (self._width, self._height), pixels)
