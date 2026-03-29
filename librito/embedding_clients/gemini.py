"""Gemini API client for text embeddings."""

from __future__ import annotations

import os
from typing import Sequence

from google import genai
from google.genai import types

_API_KEY_ENV_VAR = "GEMINI_API_KEY"


class GeminiEmbeddingClientError(RuntimeError):
    """Raised when Gemini embedding generation fails."""


class GeminiEmbeddingClient:
    """Gemini embedding client backed by the official SDK."""

    def __init__(
            self,
            *,
            model: str,
            timeout_seconds: float = 60.0,
    ) -> None:
        """Initialize the client.

        Parameters
        ----------
        model:
            Embedding model identifier.
        timeout_seconds:
            Request timeout passed to the SDK HTTP layer.

        Raises
        ------
        GeminiEmbeddingClientError
            If the SDK client cannot be initialized or the API key is missing.
        """

        api_key = os.getenv(_API_KEY_ENV_VAR, "").strip()
        if not api_key:
            raise GeminiEmbeddingClientError(f"Missing required environment variable: {_API_KEY_ENV_VAR}.")

        self._model = model
        try:
            self._sdk_client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=max(int(timeout_seconds * 1000), 10_000),
                ),
            )
        except Exception as error:
            raise GeminiEmbeddingClientError(f"Failed to initialize Google GenAI SDK client: {error}.") from error

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Parameters
        ----------
        text:
            Text content to embed.

        Returns
        -------
        list[float]
            Embedding vector returned by Gemini.
        """

        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple text strings.

        Parameters
        ----------
        texts:
            Text contents to embed in batch order.

        Returns
        -------
        list[list[float]]
            Embedding vectors in the same order as the inputs.

        Raises
        ------
        GeminiEmbeddingClientError
            If the request fails or the response payload is incomplete.
        """

        if not texts:
            return []

        try:
            response = self._sdk_client.models.embed_content(
                model=self._model,
                contents=list(texts),
            )
        except Exception as error:
            raise GeminiEmbeddingClientError(f"Gemini SDK embedding request failed: {error}.") from error

        if not response.embeddings:
            raise GeminiEmbeddingClientError("Gemini response did not contain embedding payloads.")

        vectors: list[list[float]] = []
        for index, embedding in enumerate(response.embeddings):
            values = embedding.values
            if values is None:
                raise GeminiEmbeddingClientError(
                    f"Gemini embedding response at index {index} did not contain numeric values."
                )
            vectors.append(list(values))

        if len(vectors) != len(texts):
            raise GeminiEmbeddingClientError(
                "Gemini embedding response count did not match the number of requested texts."
            )

        return vectors
