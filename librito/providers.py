"""Shared provider-selection helpers for generative backends."""

from __future__ import annotations

import logging
from librito.embedding_clients import EmbeddingClient
from librito.image_clients import ImageClient

logger = logging.getLogger(__name__)


def build_image_client(
        *,
        provider: str,
        model: str,
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
) -> ImageClient:
    """Build the image-generation client used by the illustration pipeline.

    Parameters
    ----------
    provider:
        Image-generation provider name.
    model:
        Image model identifier. For ComfyUI, this is the checkpoint filename.
    aspect_ratio:
        Requested image aspect ratio.
    image_size:
        Requested overall image resolution.

    Returns
    -------
    ImageClient
        Ready-to-use image client for the selected backend.

    Raises
    ------
    RuntimeError
        If the selected provider is missing required configuration.
    ValueError
        If the provider is unknown.
    """

    if provider == "mock":
        from librito.image_clients.mock import MockImageClient, MockImageClientConfig

        logger.info("Using mock image client.")
        return MockImageClient(MockImageClientConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ))

    if provider == "comfyui":
        from librito.image_clients.comfyui import ComfyUIImageClient

        logger.info("Using ComfyUI image provider.")
        return ComfyUIImageClient(
            checkpoint=model,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )

    if provider == "gemini":
        from librito.image_clients.gemini import GeminiImageClient

        logger.info("Using Gemini image provider.")
        return GeminiImageClient(
            model=model,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )

    raise ValueError(f"Unsupported image provider: {provider}.")


def build_embedding_client(
        *,
        provider: str,
        model: str,
) -> EmbeddingClient:
    """Build the embedding client used by evaluation and helper workflows.

    Parameters
    ----------
    provider:
        Embedding provider name.
    model:
        Model identifier understood by the selected provider.

    Returns
    -------
    EmbeddingClient
        Ready-to-use embedding client for the selected backend.

    Raises
    ------
    ValueError
        If the provider is unknown.
    """

    if provider == "gemini":
        from librito.embedding_clients.gemini import GeminiEmbeddingClient

        logger.info("Using Gemini embedding provider.")
        return GeminiEmbeddingClient(model=model)

    if provider == "lms":
        from librito.embedding_clients.lms import LMStudioEmbeddingClient

        logger.info("Using LM Studio embedding provider.")
        return LMStudioEmbeddingClient(model=model)

    if provider == "mock":
        from librito.embedding_clients.mock import MockEmbeddingClient

        logger.info("Using mock embedding provider.")
        return MockEmbeddingClient(model=model)

    raise ValueError(f"Unsupported embedding provider: {provider}.")
