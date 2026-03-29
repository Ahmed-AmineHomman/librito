"""Generate illustrations for a segmented storybook."""

from __future__ import annotations

import logging
import sys
import warnings
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from librito.generate_illustrations import generate_story_illustrations

logger = logging.getLogger(__name__)


def load_parameters() -> Namespace:
    parser = ArgumentParser(
        description="Generate illustrations for a segmented storybook.",
    )
    parser.add_argument(
        "--storybook",
        required=True,
        type=Path,
        help="Path to the story folder (must contain story.json).",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "comfyui", "mock"],
        default="gemini",
        help="Image generation provider (default: gemini).",
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help=(
            "Checkpoint filename for the ComfyUI checkpoint workflow. "
            "Optional model override for gemini."
        ),
    )
    parser.add_argument(
        "--diffusion-model",
        default=None,
        help="UNET model filename for the ComfyUI diffusion workflow.",
    )
    parser.add_argument(
        "--clip",
        default=None,
        help="CLIP model filename for the ComfyUI diffusion workflow.",
    )
    parser.add_argument(
        "--vae",
        default=None,
        help="VAE model filename for the ComfyUI diffusion workflow.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        help="Image aspect ratio (default: 1:1).",
    )
    parser.add_argument(
        "--resolution",
        default="1K",
        help='Overall image resolution: "0.5K", "1K", or "2K" (default: 1K).',
    )
    return parser.parse_args()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the illustration generation entrypoint.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    int
        Process exit status.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    arguments = load_parameters()
    _validate_comfyui_model_arguments(arguments)

    logger.info("Starting illustration pipeline for %s.", arguments.storybook)
    generate_story_illustrations(
        arguments.storybook,
        provider=arguments.provider,
        checkpoint=arguments.checkpoint,
        diffusion_model=arguments.diffusion_model,
        clip=arguments.clip,
        vae=arguments.vae,
        aspect_ratio=arguments.aspect_ratio,
        image_size=arguments.resolution,
    )
    logger.info("Done.")
    return 0


def _validate_comfyui_model_arguments(arguments: Namespace) -> None:
    """Validate and resolve model-related arguments for the ComfyUI provider.

    When ``--checkpoint`` is provided alongside diffusion parameters, a
    warning is emitted and the checkpoint workflow takes precedence.  When
    no ``--checkpoint`` is given, all three diffusion parameters must be
    present.

    Parameters
    ----------
    arguments:
        Parsed CLI arguments (modified in-place when needed).
    """

    if arguments.provider != "comfyui":
        return

    has_checkpoint = bool(arguments.checkpoint)
    has_diffusion = bool(arguments.diffusion_model and arguments.clip and arguments.vae)
    has_any_diffusion = bool(arguments.diffusion_model or arguments.clip or arguments.vae)

    if has_checkpoint and has_any_diffusion:
        warnings.warn(
            "Both --checkpoint and diffusion model parameters provided. "
            "Using the checkpoint workflow; diffusion parameters are ignored.",
            stacklevel=2,
        )
        arguments.diffusion_model = None
        arguments.clip = None
        arguments.vae = None
        return

    if not has_checkpoint and not has_diffusion:
        missing = [
            name
            for name, value in [
                ("--diffusion-model", arguments.diffusion_model),
                ("--clip", arguments.clip),
                ("--vae", arguments.vae),
            ]
            if not value
        ]
        if missing:
            raise SystemExit(
                f"ComfyUI provider requires either --checkpoint or all three of "
                f"--diffusion-model, --clip, and --vae. Missing: {', '.join(missing)}."
            )


if __name__ == "__main__":
    raise SystemExit(main())
