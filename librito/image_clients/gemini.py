"""Gemini API client for image generation."""

from __future__ import annotations

import os

from google import genai
from google.genai import types
from PIL import Image

_API_KEY_ENV_VAR = "GEMINI_API_KEY"


class GeminiImageClientError(RuntimeError):
    """Raised when Gemini image generation fails."""


class GeminiImageClient:
    """Gemini image-generation client backed by the official SDK."""

    def __init__(
        self,
        *,
        model: str = "gemini-3.1-flash-image-preview",
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
        timeout_seconds: float = 60.0,
    ) -> None:
        """Initialize the client.

        Parameters
        ----------
        model:
            Image generation model identifier.
        aspect_ratio:
            Requested image aspect ratio.
        image_size:
            Requested image size.
        timeout_seconds:
            Request timeout passed to the SDK HTTP layer.

        Raises
        ------
        GeminiImageClientError
            If the SDK client cannot be initialized or the API key is missing.
        """

        api_key = os.getenv(_API_KEY_ENV_VAR, "").strip()
        if not api_key:
            raise GeminiImageClientError(f"Missing required environment variable: {_API_KEY_ENV_VAR}.")

        self._model = model
        self._aspect_ratio = aspect_ratio
        self._image_size = image_size
        try:
            self._sdk_client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=max(int(timeout_seconds * 1000), 10_000),
                ),
            )
        except Exception as error:
            raise GeminiImageClientError(f"Failed to initialize Google GenAI SDK client: {error}.") from error

    def generate_image(self, prompt: str) -> Image.Image:
        """Generate a single image for a prompt.

        Parameters
        ----------
        prompt:
            Fully assembled prompt to send to Gemini.

        Returns
        -------
        Image.Image
            Generated image.

        Raises
        ------
        GeminiImageClientError
            If the request fails or no image is returned.
        """

        request_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=self._aspect_ratio,
                image_size=self._image_size,
            ),
        )

        try:
            response = self._sdk_client.models.generate_content(
                model=self._model,
                contents=[prompt],
                config=request_config,
            )
        except Exception as error:
            raise GeminiImageClientError(f"Gemini SDK request failed: {error}.") from error

        for part in response.parts:
            inline_data = part.inline_data
            if inline_data is None:
                continue

            try:
                return part.as_image()
            except Exception as error:
                raise GeminiImageClientError(
                    f"Gemini response image payload could not be decoded: {error}."
                ) from error

        raise GeminiImageClientError("Gemini response did not contain an image payload.")
