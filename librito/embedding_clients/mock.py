"""Mock embedding client producing deterministic vectors."""

from __future__ import annotations

import hashlib
from typing import Sequence


class MockEmbeddingClient:
    """Embedding client that returns deterministic vectors derived from text."""

    def __init__(self, *, model: str, dimensions: int = 16) -> None:
        """Initialize the mock embedding client.

        Parameters
        ----------
        model:
            Mock model identifier retained for interface compatibility.
        dimensions:
            Number of floats to return per embedding vector.
        """

        self._model = model
        self._dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        """Generate a deterministic embedding vector for one text string.

        Parameters
        ----------
        text:
            Text content to embed.

        Returns
        -------
        list[float]
            Deterministic embedding vector.
        """

        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate deterministic embedding vectors for multiple texts.

        Parameters
        ----------
        texts:
            Text contents to embed in batch order.

        Returns
        -------
        list[list[float]]
            Deterministic embedding vectors in input order.
        """

        return [self._embed_single_text(text) for text in texts]

    def _embed_single_text(self, text: str) -> list[float]:
        """Convert a text string into a deterministic floating-point vector.

        Parameters
        ----------
        text:
            Text content to embed.

        Returns
        -------
        list[float]
            Deterministic embedding vector with the configured dimension.
        """

        vector: list[float] = []
        chunk_index = 0
        while len(vector) < self._dimensions:
            digest = hashlib.sha256(f"{self._model}:{chunk_index}:{text}".encode("utf-8")).digest()
            for offset in range(0, len(digest), 4):
                if len(vector) >= self._dimensions:
                    break
                chunk = digest[offset:offset + 4]
                integer_value = int.from_bytes(chunk, byteorder="big", signed=False)
                vector.append((integer_value / 0xFFFFFFFF) * 2.0 - 1.0)
            chunk_index += 1

        return vector
