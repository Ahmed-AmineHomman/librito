"""Tests for the mock embedding client."""

from __future__ import annotations

import unittest

from librito.embedding_clients.mock import MockEmbeddingClient


class MockEmbeddingClientTests(unittest.TestCase):
    """Validate deterministic mock embedding behavior."""

    def test_embed_text_returns_fixed_length_vector(self) -> None:
        """Single-text embeddings should match the configured dimensions."""

        client = MockEmbeddingClient(model="mock-embedding", dimensions=8)

        vector = client.embed_text("calm river")

        self.assertEqual(len(vector), 8)

    def test_embed_text_is_deterministic_for_same_input(self) -> None:
        """Repeated calls with the same input should produce identical vectors."""

        client = MockEmbeddingClient(model="mock-embedding")

        first_vector = client.embed_text("calm river")
        second_vector = client.embed_text("calm river")

        self.assertEqual(first_vector, second_vector)

    def test_embed_texts_preserves_input_order(self) -> None:
        """Batch embeddings should remain aligned with the input sequence."""

        client = MockEmbeddingClient(model="mock-embedding", dimensions=4)

        vectors = client.embed_texts(["alpha", "beta"])

        self.assertEqual(len(vectors), 2)
        self.assertNotEqual(vectors[0], vectors[1])
        self.assertEqual(vectors[0], client.embed_text("alpha"))
        self.assertEqual(vectors[1], client.embed_text("beta"))


if __name__ == "__main__":
    unittest.main()
