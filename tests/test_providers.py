"""Tests for shared generative provider helpers."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from librito.embedding_clients.mock import MockEmbeddingClient
from librito.image_clients.gemini import GeminiImageClientError
from librito.image_clients.mock import MockImageClient
from librito.providers import (
    build_embedding_client,
    build_image_client,
    build_segmentation_model,
    normalize_openai_compatible_api_base,
)


class SegmentationProviderTests(unittest.TestCase):
    """Validate segmentation provider selection."""

    def test_build_segmentation_model_returns_model_name_for_gemini(self) -> None:
        """Gemini segmentation should pass through the selected model name."""

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False):
            result = build_segmentation_model(provider="gemini", model="gemini-2.0-flash")

        self.assertEqual(result, "gemini-2.0-flash")

    def test_build_segmentation_model_requires_api_url_env_var_for_lms(self) -> None:
        """LM Studio should require its API URL environment variable."""

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "LMS_API_URL"):
                build_segmentation_model(provider="lms", model="local-model")

    @patch("librito.providers.LiteLlm")
    def test_build_segmentation_model_reads_lms_configuration_from_env(
        self,
        lite_llm_class: unittest.mock.Mock,
    ) -> None:
        """LM Studio should source its URL and key from environment variables."""

        sentinel_model = object()
        lite_llm_class.return_value = sentinel_model

        with patch.dict(
            os.environ,
            {
                "LMS_API_URL": "http://127.0.0.1:1234",
                "LMS_API_KEY": "local-key",
            },
            clear=True,
        ):
            result = build_segmentation_model(provider="lms", model="local-model")

        self.assertIs(result, sentinel_model)
        lite_llm_class.assert_called_once_with(
            model="local-model",
            api_base="http://127.0.0.1:1234/v1",
            api_key="local-key",
        )

    @patch("librito.providers.LiteLlm")
    def test_build_segmentation_model_uses_placeholder_key_when_lms_key_missing(
        self,
        lite_llm_class: unittest.mock.Mock,
    ) -> None:
        """LM Studio should keep the existing placeholder fallback when needed."""

        sentinel_model = object()
        lite_llm_class.return_value = sentinel_model

        with patch.dict(os.environ, {"LMS_API_URL": "http://127.0.0.1:1234"}, clear=True):
            build_segmentation_model(provider="lms", model="local-model")

        lite_llm_class.assert_called_once_with(
            model="local-model",
            api_base="http://127.0.0.1:1234/v1",
            api_key="not-used",
        )


class ImageProviderTests(unittest.TestCase):
    """Validate image provider selection."""

    def test_build_image_client_returns_mock_client(self) -> None:
        """Mock provider should bypass real provider setup."""

        client = build_image_client(provider="mock")

        self.assertIsInstance(client, MockImageClient)

    def test_build_image_client_requires_gemini_api_key(self) -> None:
        """Gemini image generation should require an API key."""

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(GeminiImageClientError, "GEMINI_API_KEY"):
                build_image_client(provider="gemini")

    @patch("librito.providers.GeminiImageClient")
    def test_build_image_client_returns_gemini_client(self, gemini_client_class: unittest.mock.Mock) -> None:
        """Gemini image generation should build the SDK-backed client."""

        sentinel_client = object()
        gemini_client_class.return_value = sentinel_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False):
            client = build_image_client(provider="gemini")

        self.assertIs(client, sentinel_client)
        gemini_client_class.assert_called_once()

    @patch("librito.providers.ComfyUIImageClient")
    def test_build_image_client_returns_comfyui_client(self, comfyui_client_class: unittest.mock.Mock) -> None:
        """ComfyUI image generation should build the REST-backed client."""

        sentinel_client = object()
        comfyui_client_class.return_value = sentinel_client

        client = build_image_client(
            provider="comfyui",
            checkpoint="model.safetensors",
        )

        self.assertIs(client, sentinel_client)
        comfyui_client_class.assert_called_once()


class EmbeddingProviderTests(unittest.TestCase):
    """Validate embedding provider selection."""

    def test_build_embedding_client_returns_mock_client(self) -> None:
        """Mock provider should build the deterministic embedding client."""

        client = build_embedding_client(provider="mock", model="mock-embedding")

        self.assertIsInstance(client, MockEmbeddingClient)


class ProviderUtilityTests(unittest.TestCase):
    """Validate shared provider utilities."""

    def test_normalize_openai_compatible_api_base_appends_v1(self) -> None:
        """Root LM Studio URLs should gain the ``/v1`` suffix."""

        result = normalize_openai_compatible_api_base("http://127.0.0.1:1234/")

        self.assertEqual(result, "http://127.0.0.1:1234/v1")

    def test_normalize_openai_compatible_api_base_keeps_existing_v1(self) -> None:
        """Already-normalized URLs should be returned unchanged."""

        result = normalize_openai_compatible_api_base("http://127.0.0.1:1234/v1")

        self.assertEqual(result, "http://127.0.0.1:1234/v1")
