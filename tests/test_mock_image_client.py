"""Tests for the mock image generation client."""

from __future__ import annotations

import unittest

from librito.image_clients.mock import MockImageClient, MockImageClientConfig
from librito.image_clients.utils import compute_dimensions


class ComputeDimensionsTests(unittest.TestCase):
    """Validate dimension computation from aspect ratio and size."""

    def test_square_1k(self) -> None:
        """1:1 at 1K should yield 1024×1024."""

        self.assertEqual(compute_dimensions("1:1", "1K"), (1024, 1024))

    def test_landscape_16_9_1k(self) -> None:
        """16:9 at 1K should yield 1024×576."""

        width, height = compute_dimensions("16:9", "1K")
        self.assertEqual(width, 1024)
        self.assertEqual(height, 576)

    def test_portrait_9_16_1k(self) -> None:
        """9:16 at 1K should yield 576×1024."""

        width, height = compute_dimensions("9:16", "1K")
        self.assertEqual(width, 576)
        self.assertEqual(height, 1024)

    def test_3_4_2k(self) -> None:
        """3:4 at 2K should yield 1536×2048."""

        width, height = compute_dimensions("3:4", "2K")
        self.assertEqual(width, 1536)
        self.assertEqual(height, 2048)

    def test_unsupported_aspect_ratio_raises(self) -> None:
        """An unknown aspect ratio should raise ValueError."""

        with self.assertRaisesRegex(ValueError, "Unsupported aspect ratio"):
            compute_dimensions("5:3", "1K")

    def test_unsupported_image_size_raises(self) -> None:
        """An unknown size label should raise ValueError."""

        with self.assertRaisesRegex(ValueError, "Unsupported image size"):
            compute_dimensions("1:1", "4K")


class MockImageClientTests(unittest.TestCase):
    """Validate mock client image output."""

    def test_generate_image_returns_correct_dimensions(self) -> None:
        """The generated image should match the configured size and ratio."""

        client = MockImageClient(MockImageClientConfig(aspect_ratio="16:9", image_size="512"))
        image = client.generate_image("any prompt")

        self.assertEqual(image.size, (512, 288))
        self.assertEqual(image.mode, "RGB")

    def test_generate_image_default_config(self) -> None:
        """The default config should produce a 1024×1024 image."""

        client = MockImageClient()
        image = client.generate_image("test")

        self.assertEqual(image.size, (1024, 1024))

    def test_generate_image_produces_non_uniform_pixels(self) -> None:
        """The noise image should not be a solid color."""

        client = MockImageClient(MockImageClientConfig(image_size="512"))
        image = client.generate_image("test")
        raw = image.tobytes()

        first_pixel = raw[:3]
        has_variation = any(raw[i:i + 3] != first_pixel for i in range(3, min(len(raw), 300), 3))
        self.assertTrue(has_variation)


if __name__ == "__main__":
    unittest.main()
