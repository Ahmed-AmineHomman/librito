"""Tests for the Gemini SDK wrapper."""

from __future__ import annotations

import unittest
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image

from librito.image_clients.gemini import (
    GeminiImageClient,
    GeminiImageClientError,
)


class GeminiImageClientTests(unittest.TestCase):
    """Validate SDK-backed image generation."""

    @patch("librito.image_clients.gemini.types.ImageConfig")
    @patch("librito.image_clients.gemini.types.GenerateContentConfig")
    @patch("librito.image_clients.gemini.types.HttpOptions")
    @patch("librito.image_clients.gemini.genai.Client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
    def test_generate_image_returns_first_inline_image(
        self,
        client_class: Mock,
        http_options_class: Mock,
        generate_content_config_class: Mock,
        image_config_class: Mock,
    ) -> None:
        """The client should return binary data from the first inline image part."""

        fake_response = SimpleNamespace(
            parts=[
                SimpleNamespace(text="caption", inline_data=None),
                SimpleNamespace(
                    text=None,
                    inline_data=SimpleNamespace(),
                    as_image=Mock(return_value=Image.new("RGB", (2, 2), color="red")),
                ),
            ]
        )
        fake_models = SimpleNamespace(generate_content=Mock(return_value=fake_response))
        client_class.return_value = SimpleNamespace(models=fake_models)
        http_options_class.side_effect = lambda **kwargs: kwargs
        generate_content_config_class.side_effect = lambda **kwargs: kwargs
        image_config_class.side_effect = lambda **kwargs: kwargs

        client = GeminiImageClient()
        generated_image = client.generate_image("draw a dog")

        self.assertIsInstance(generated_image, Image.Image)
        self.assertEqual(generated_image.size, (2, 2))
        fake_models.generate_content.assert_called_once()
        http_options_class.assert_called_once_with(timeout=60000)

    @patch("librito.image_clients.gemini.genai.Client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
    def test_sdk_client_errors_are_wrapped(self, client_class: Mock) -> None:
        """SDK initialization failures should surface as client errors."""

        client_class.side_effect = RuntimeError("boom")

        with self.assertRaisesRegex(GeminiImageClientError, "Failed to initialize"):
            GeminiImageClient()

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_raises_client_error(self) -> None:
        """Gemini should fail fast when its API key is absent."""

        with self.assertRaisesRegex(GeminiImageClientError, "GEMINI_API_KEY"):
            GeminiImageClient()
