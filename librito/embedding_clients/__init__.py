"""Embedding client abstractions and implementations."""

from __future__ import annotations

from typing import Protocol, Sequence


class EmbeddingClient(Protocol):
    """Protocol for text embedding clients."""

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Parameters
        ----------
        text:
            Text content to embed.

        Returns
        -------
        list[float]
            Embedding vector returned by the backend.
        """
        ...

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
        """
        ...
