"""LM Studio API client for text embeddings."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Sequence

_API_URL_ENV_VAR = "LMS_API_URL"
_API_KEY_ENV_VAR = "LMS_API_KEY"


class LMStudioEmbeddingClientError(RuntimeError):
    """Raised when LM Studio embedding generation fails."""


class LMStudioEmbeddingClient:
    """Embedding client backed by an OpenAI-compatible LM Studio endpoint."""

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
            HTTP timeout for API requests.

        Raises
        ------
        LMStudioEmbeddingClientError
            If the API base URL is missing.
        """

        api_base = os.getenv(_API_URL_ENV_VAR, "").strip()
        if not api_base:
            raise LMStudioEmbeddingClientError(f"Missing required environment variable: {_API_URL_ENV_VAR}.")

        self._model = model
        self._timeout_seconds = timeout_seconds
        self._api_base = self._normalize_openai_compatible_api_base(api_base)

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Parameters
        ----------
        text:
            Text content to embed.

        Returns
        -------
        list[float]
            Embedding vector returned by LM Studio.
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
        LMStudioEmbeddingClientError
            If the request fails or the response payload is incomplete.
        """

        if not texts:
            return []

        payload = json.dumps(
            {
                "model": self._model,
                "input": list(texts),
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self._api_base}/embeddings",
            data=payload,
            headers=self._request_headers(),
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            raise LMStudioEmbeddingClientError(
                f"LM Studio embedding request failed (HTTP {error.code}): {response_body}"
            ) from error
        except Exception as error:
            raise LMStudioEmbeddingClientError(f"LM Studio embedding request failed: {error}.") from error

        try:
            data = json.loads(body)
        except json.JSONDecodeError as error:
            raise LMStudioEmbeddingClientError(
                f"LM Studio returned invalid JSON for embedding request: {error}."
            ) from error

        return self._parse_embedding_response(data, len(texts))

    @staticmethod
    def _normalize_openai_compatible_api_base(api_base: str) -> str:
        """Normalize an OpenAI-compatible API base URL.

        Parameters
        ----------
        api_base:
            User-provided API base URL.

        Returns
        -------
        str
            API base URL ending with ``/v1``.
        """

        normalized_api_base = api_base.rstrip("/")
        if normalized_api_base.endswith("/v1"):
            return normalized_api_base
        return f"{normalized_api_base}/v1"

    @staticmethod
    def _request_headers() -> dict[str, str]:
        """Build HTTP headers for LM Studio requests.

        Returns
        -------
        dict[str, str]
            Request headers including JSON content type and optional auth.
        """

        headers = {"Content-Type": "application/json"}
        api_key = os.getenv(_API_KEY_ENV_VAR, "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    @staticmethod
    def _parse_embedding_response(data: dict[str, Any], expected_count: int) -> list[list[float]]:
        """Extract vectors from an OpenAI-compatible embedding response.

        Parameters
        ----------
        data:
            Parsed JSON response body.
        expected_count:
            Number of vectors expected from the API.

        Returns
        -------
        list[list[float]]
            Embedding vectors in input order.

        Raises
        ------
        LMStudioEmbeddingClientError
            If the payload is missing or malformed.
        """

        raw_embeddings = data.get("data")
        if not isinstance(raw_embeddings, list):
            raise LMStudioEmbeddingClientError("LM Studio response did not contain a valid 'data' list.")

        try:
            ordered_embeddings = sorted(
                raw_embeddings,
                key=lambda item: int(item.get("index", 0)),
            )
        except Exception as error:
            raise LMStudioEmbeddingClientError(
                f"LM Studio response contained an invalid embedding index: {error}."
            ) from error

        vectors: list[list[float]] = []
        for index, item in enumerate(ordered_embeddings):
            if not isinstance(item, dict):
                raise LMStudioEmbeddingClientError(
                    f"LM Studio response embedding at index {index} was not an object."
                )
            embedding = item.get("embedding")
            if not isinstance(embedding, list):
                raise LMStudioEmbeddingClientError(
                    f"LM Studio response embedding at index {index} did not contain a vector."
                )
            vectors.append([float(value) for value in embedding])

        if len(vectors) != expected_count:
            raise LMStudioEmbeddingClientError(
                "LM Studio embedding response count did not match the number of requested texts."
            )

        return vectors
