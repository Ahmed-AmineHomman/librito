"""Shared provider-selection helpers for generative backends."""

from __future__ import annotations

import logging
import os

from google.adk.models.lite_llm import LiteLlm

from librito.embedding_clients import EmbeddingClient
from librito.embedding_clients.gemini import GeminiEmbeddingClient
from librito.embedding_clients.lms import LMStudioEmbeddingClient
from librito.embedding_clients.mock import MockEmbeddingClient
from librito.image_clients import ImageClient
from librito.image_clients.comfyui import ComfyUIImageClient
from librito.image_clients.gemini import GeminiImageClient
from librito.image_clients.mock import MockImageClient, MockImageClientConfig

logger = logging.getLogger(__name__)

_GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
_LMS_API_URL_ENV_VAR = "LMS_API_URL"
_LMS_API_KEY_ENV_VAR = "LMS_API_KEY"


def build_segmentation_model(
    *,
    provider: str,
    model: str,
) -> str | LiteLlm:
    """Build the model configuration used by the segmentation agent.

    Parameters
    ----------
    provider:
        Text-generation provider name.
    model:
        Model identifier understood by the selected provider.

    Returns
    -------
    str | LiteLlm
        Model configuration accepted by ``google.adk.agents.LlmAgent``.

    Raises
    ------
    RuntimeError
        If the selected provider is missing required configuration.
    ValueError
        If the provider is unknown.
    """

    if provider == "gemini":
        if not os.getenv(_GEMINI_API_KEY_ENV_VAR):
            raise RuntimeError(f"Missing required environment variable: {_GEMINI_API_KEY_ENV_VAR}.")
        logger.info("Using Gemini text provider.")
        return model

    if provider == "lms":
        api_base = os.getenv(_LMS_API_URL_ENV_VAR)
        if not api_base:
            raise RuntimeError(f"Missing required environment variable: {_LMS_API_URL_ENV_VAR}.")

        logger.info("Using LM Studio text provider.")
        return LiteLlm(
            model=model,
            api_base=normalize_openai_compatible_api_base(api_base),
            api_key=os.getenv(_LMS_API_KEY_ENV_VAR, "not-used"),
        )

    raise ValueError(f"Unsupported text provider: {provider}.")


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
        logger.info("Using mock image client.")
        return MockImageClient(MockImageClientConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ))

    if provider == "comfyui":
        logger.info("Using ComfyUI image provider.")
        return ComfyUIImageClient(
            checkpoint=model,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )

    if provider == "gemini":
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
        logger.info("Using Gemini embedding provider.")
        return GeminiEmbeddingClient(model=model)

    if provider == "lms":
        logger.info("Using LM Studio embedding provider.")
        return LMStudioEmbeddingClient(model=model)

    if provider == "mock":
        logger.info("Using mock embedding provider.")
        return MockEmbeddingClient(model=model)

    raise ValueError(f"Unsupported embedding provider: {provider}.")


def normalize_openai_compatible_api_base(api_base: str) -> str:
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
