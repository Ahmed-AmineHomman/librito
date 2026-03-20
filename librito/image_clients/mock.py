"""Mock image generation client producing pixel-noise images."""

from __future__ import annotations

import random
from dataclasses import dataclass

from PIL import Image

_SIZE_MAP: dict[str, int] = {
    "1K": 1024,
    "2K": 2048,
    "512": 512,
}

_ASPECT_RATIO_MAP: dict[str, tuple[int, int]] = {
    "1:1": (1, 1),
    "3:4": (3, 4),
    "4:3": (4, 3),
    "9:16": (9, 16),
    "16:9": (16, 9),
}


def _compute_dimensions(aspect_ratio: str, image_size: str) -> tuple[int, int]:
    """Compute pixel dimensions from an aspect ratio and a size label.

    The ``image_size`` determines the length of the longest side.  The shorter
    side is scaled proportionally to respect the aspect ratio.

    Parameters
    ----------
    aspect_ratio:
        Aspect ratio string such as ``"1:1"`` or ``"16:9"``.
    image_size:
        Size label such as ``"1K"`` or ``"2K"``.

    Returns
    -------
    tuple[int, int]
        ``(width, height)`` in pixels.

    Raises
    ------
    ValueError
        If the aspect ratio or size label is not recognised.
    """

    if aspect_ratio not in _ASPECT_RATIO_MAP:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio!r}.")
    if image_size not in _SIZE_MAP:
        raise ValueError(f"Unsupported image size: {image_size!r}.")

    width_ratio, height_ratio = _ASPECT_RATIO_MAP[aspect_ratio]
    longest_side = _SIZE_MAP[image_size]

    if width_ratio >= height_ratio:
        width = longest_side
        height = int(longest_side * height_ratio / width_ratio)
    else:
        height = longest_side
        width = int(longest_side * width_ratio / height_ratio)

    return width, height


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
        self._width, self._height = _compute_dimensions(
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
