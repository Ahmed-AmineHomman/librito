"""CLI subcommand group: ``librito illustrate``."""

from __future__ import annotations

import logging
from argparse import Namespace, RawDescriptionHelpFormatter, _SubParsersAction
from textwrap import dedent

from librito.illustration.artworks import generate_artworks
from librito.illustration.scenes import illustrate_scenes
from librito.illustration.trial import generate_trial

logger = logging.getLogger(__name__)


def register(subparsers: _SubParsersAction) -> None:
    """Register the ``illustrate`` subcommand group.

    Parameters
    ----------
    subparsers:
        Parent subparsers action to attach to.
    """

    group_parser = subparsers.add_parser(
        "illustrate",
        help="Generate illustrations (scenes, artworks, or trial).",
        description="Generate illustrations for a storybook.",
        formatter_class=RawDescriptionHelpFormatter,
    )
    group_subparsers = group_parser.add_subparsers(
        dest="illustrate_subcommand",
        title="subcommands",
    )
    group_parser.set_defaults(handler=lambda _args: (group_parser.print_help(), 2)[1])

    _register_scenes(group_subparsers)
    _register_artworks(group_subparsers)
    _register_trial(group_subparsers)


# ── scenes ───────────────────────────────────────────────────────────────────


def _register_scenes(subparsers: _SubParsersAction) -> None:
    """Register the ``illustrate scenes`` subcommand."""

    parser = subparsers.add_parser(
        "scenes",
        help="Generate scene and book-part illustrations.",
        description=dedent(
            """\
            Generate illustrations for storybook scenes and book parts.

            Turns scene prompts and configured non-scene page prompts into
            image files under ``illustrations/``.  Runs are resumable: items
            whose ``image_path`` already points to an existing file are skipped
            unless ``--force`` is used.
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    _add_common_image_arguments(parser)
    parser.add_argument(
        "--scenes",
        action="extend",
        nargs="+",
        type=str,
        help="Optional scene labels to generate.",
    )
    parser.add_argument(
        "--parts",
        action="extend",
        nargs="+",
        type=str,
        help="Optional illustrated book-part names to generate.",
    )
    parser.add_argument(
        "--constraints",
        type=str,
        default=None,
        help="Optional constraints overriding storybook constraints.",
    )
    parser.set_defaults(handler=_handle_scenes)


def _handle_scenes(arguments: Namespace) -> int:
    """Handle the ``illustrate scenes`` subcommand."""

    illustrate_scenes(
        story=arguments.story,
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        resolution=arguments.resolution,
        force=arguments.force,
        scenes=arguments.scenes,
        parts=arguments.parts,
        constraints=arguments.constraints,
    )
    return 0


# ── artworks ─────────────────────────────────────────────────────────────────


def _register_artworks(subparsers: _SubParsersAction) -> None:
    """Register the ``illustrate artworks`` subcommand."""

    parser = subparsers.add_parser(
        "artworks",
        help="Generate concept reference artworks.",
        description=dedent(
            """\
            Generate concept reference artworks for a storybook.

            Artworks provide concrete visual references (image anchors) for
            recurring concepts.  They are a mandatory preliminary step before
            scene illustration.
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    _add_common_image_arguments(parser)
    parser.add_argument(
        "--concepts",
        action="extend",
        nargs="+",
        type=str,
        help="Optional concept tags to generate (e.g. '<LEO>' or 'LEO').",
    )
    parser.add_argument(
        "--subject-constraints",
        type=str,
        default=None,
        help="Optional constraints overriding storybook subject artwork constraints.",
    )
    parser.add_argument(
        "--environment-constraints",
        type=str,
        default=None,
        help="Optional constraints overriding storybook environment artwork constraints.",
    )
    parser.set_defaults(handler=_handle_artworks)


def _handle_artworks(arguments: Namespace) -> int:
    """Handle the ``illustrate artworks`` subcommand."""

    generate_artworks(
        story=arguments.story,
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        resolution=arguments.resolution,
        force=arguments.force,
        concepts=arguments.concepts,
        subject_constraints=arguments.subject_constraints,
        environment_constraints=arguments.environment_constraints,
    )
    return 0


# ── trial ────────────────────────────────────────────────────────────────────


def _register_trial(subparsers: _SubParsersAction) -> None:
    """Register the ``illustrate trial`` subcommand."""

    parser = subparsers.add_parser(
        "trial",
        help="Generate one trial illustration without mutating the storybook.",
        description=dedent(
            """\
            Generate one trial illustration for a storybook.

            Uses the same prompt-building flow as the canonical illustration
            pipeline, but writes a standalone PNG into ``trials/`` and never
            updates ``story.json``.
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story folder name under ./database/<story>/.",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "comfyui", "mock"],
        help="Image generation provider. Required unless --dry-run is used.",
    )
    parser.add_argument(
        "--model",
        help="Image model identifier. Required unless --dry-run is used.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        help="Requested image aspect ratio (default: 1:1).",
    )
    parser.add_argument(
        "--resolution",
        default="1K",
        help='Requested image resolution: "0.5K", "1K", or "2K" (default: 1K).',
    )
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--scene",
        type=str,
        help="Single scene label to generate.",
    )
    target_group.add_argument(
        "--part",
        type=str,
        help="Single illustrated book-part name to generate.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Optional prompt override. Anchors are resolved as usual.",
    )
    parser.add_argument(
        "--style",
        type=str,
        help="Optional style override for this run only.",
    )
    parser.add_argument(
        "--constraints",
        type=str,
        help="Optional constraints override for this run only.",
    )
    parser.add_argument(
        "--output-name",
        dest="output_name",
        type=str,
        help="Optional PNG basename to use inside the trials directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve and log prompts without generating an image file.",
    )
    parser.set_defaults(handler=_handle_trial)


def _handle_trial(arguments: Namespace) -> int:
    """Handle the ``illustrate trial`` subcommand."""

    if not arguments.dry_run:
        if arguments.provider is None or arguments.model is None:
            raise SystemExit("--provider and --model are required unless --dry-run is used.")
    else:
        if (arguments.provider is None) != (arguments.model is None):
            raise SystemExit("--provider and --model must be provided together when specified.")

    generate_trial(
        story=arguments.story,
        scene=arguments.scene,
        part=arguments.part,
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        resolution=arguments.resolution,
        prompt=arguments.prompt,
        style=arguments.style,
        constraints=arguments.constraints,
        output_name=arguments.output_name,
        dry_run=arguments.dry_run,
    )
    return 0


# ── shared ───────────────────────────────────────────────────────────────────


def _add_common_image_arguments(parser) -> None:
    """Add arguments shared by ``scenes`` and ``artworks`` subcommands."""

    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story folder name under ./database/<story>/.",
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["gemini", "comfyui", "mock"],
        help="Image generation provider.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Image model identifier.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        help="Requested image aspect ratio (default: 1:1).",
    )
    parser.add_argument(
        "--resolution",
        default="1K",
        help='Requested image resolution: "0.5K", "1K", or "2K" (default: 1K).',
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate images even when the file already exists.",
    )
