"""Generate one trial illustration without mutating the canonical storybook."""

from __future__ import annotations

import re
import sys
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Sequence

import logging

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.environment import load_repository_environment
from librito.io import load_storybook
from librito.logging import add_logging_arguments, configure_logging
from librito.models import PageSpec, Storybook
from librito.prompt_builder import build_render_prompt_from_text, resolve_prompt
from librito.providers import build_image_client
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)

ILLUSTRATED_PARTS_IN_ORDER = [
    "front_cover",
    "front_endpaper",
    "frontispiece",
    "title_page",
    "closing_illustration",
    "back_cover",
]
PART_DISPLAY_NAMES = {
    "front_cover": "Front cover",
    "front_endpaper": "Front endpaper",
    "frontispiece": "Frontispiece",
    "title_page": "Title page",
    "closing_illustration": "Closing illustration",
    "back_cover": "Back cover",
}
TRIALS_DIRECTORY_NAME = "trials"
_SAFE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class TargetSelection:
    """Single trial-generation target resolved from the storybook.

    Parameters
    ----------
    kind:
        Target kind, either ``"scene"`` or ``"part"``.
    identifier:
        Stable scene label or canonical part name.
    display_name:
        Human-readable target name for logging.
    prompt:
        Raw prompt text stored in the storybook for the selected target.
    """

    kind: str
    identifier: str
    display_name: str
    prompt: str


def load_parameters(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command-line arguments.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    Namespace
        Parsed and validated command-line arguments.
    """

    parser = ArgumentParser(
        description=dedent(
            """
            Generate one trial illustration for a storybook.

            This helper reuses the same prompt-building flow as the canonical
            illustration pipeline, but writes a standalone PNG into
            ``database/<story>/trials/`` and never updates ``story.json``.
            """
        ).strip(),
        epilog=dedent(
            """
            Target selection:
              - pass exactly one of --scene or --part
              - scene targets use the scene label from story.json
              - part targets use illustrated book-part names such as front_cover

            Overrides:
              - --prompt replaces the selected target prompt before anchor resolution
              - --style replaces the global storybook style for this run only
              - --constraints replaces the storybook constraints for this run only
              - --output-name names the PNG file inside the trials directory

            Examples:
              python helpers/illustrate_trial.py --story sir_turnip --provider mock --model mock --scene scene-001
              python helpers/illustrate_trial.py --story sir_turnip --provider mock --model mock --part front_cover --output-name cover-v2
              python helpers/illustrate_trial.py --story sir_turnip --scene scene-001 --prompt "<TURNIP> under moonlight" --dry-run
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    add_logging_arguments(parser)
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
        help="Requested image aspect ratio.",
    )
    parser.add_argument(
        "--resolution",
        default="1K",
        help='Requested image resolution: "0.5K", "1K", or "2K".',
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
    arguments = parser.parse_args(argv)

    if arguments.dry_run:
        if arguments.provider is None and arguments.model is None:
            return arguments
        if arguments.provider is None or arguments.model is None:
            parser.error("--provider and --model must be provided together when specified.")
        return arguments

    if arguments.provider is None or arguments.model is None:
        parser.error("--provider and --model are required unless --dry-run is used.")

    return arguments


def main(argv: Sequence[str] | None = None) -> int:
    """Run the trial illustration entrypoint.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    int
        Process exit status.
    """

    load_repository_environment()
    arguments = load_parameters(argv)
    configure_logging(arguments.log_level)
    workspace = StoryWorkspace.from_story(arguments.story)

    logger.info("Starting trial illustration workflow for story '%s'.", workspace.story)
    story_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)

    selection = resolve_target_selection(storybook, scene_label=arguments.scene, part_name=arguments.part)
    prompt_text = arguments.prompt if arguments.prompt is not None else selection.prompt
    effective_storybook = build_effective_storybook(
        storybook=storybook,
        style_override=arguments.style,
        constraints_override=arguments.constraints,
    )
    resolved_prompt = resolve_prompt(prompt_text, effective_storybook.concepts).strip()
    render_prompt = build_render_prompt_from_text(effective_storybook, prompt_text)

    output_directory = workspace.directory / TRIALS_DIRECTORY_NAME
    output_name = resolve_output_name(
        requested_name=arguments.output_name,
        target_identifier=selection.identifier,
    )
    output_path = output_directory / f"{output_name}.png"

    logger.info("Selected target: %s (%s).", selection.display_name, selection.kind)
    logger.info("Output path: %s", output_path)
    logger.info("Prompt source: %s", "override" if arguments.prompt is not None else "storybook")
    logger.info("Raw prompt: %s", prompt_text)
    logger.info("Resolved prompt: %s", resolved_prompt)
    logger.info("Final render prompt:\n%s", render_prompt)

    if arguments.dry_run:
        logger.info("Dry run enabled; skipping image generation and file creation.")
        logger.info("Done.")
        return 0

    output_directory.mkdir(parents=True, exist_ok=True)
    client = build_image_client(
        provider=arguments.provider,
        model=arguments.model,
        aspect_ratio=arguments.aspect_ratio,
        image_size=arguments.resolution,
    )
    generated_image = client.generate_image(render_prompt)
    generated_image.save(output_path)

    logger.info("Trial illustration saved to %s.", output_path)
    logger.info("Done.")
    return 0


def build_effective_storybook(
    storybook: Storybook,
    style_override: str | None,
    constraints_override: str | None,
) -> Storybook:
    """Return a storybook view with run-local prompt overrides applied.

    Parameters
    ----------
    storybook:
        Canonical storybook loaded from disk.
    style_override:
        Optional style override for this run.
    constraints_override:
        Optional constraints override for this run.

    Returns
    -------
    Storybook
        Storybook copy with the effective style and constraints.
    """

    style = style_override if style_override is not None else storybook.style
    constraints = constraints_override if constraints_override is not None else storybook.constraints
    return replace(storybook, style=style, constraints=constraints)


def resolve_target_selection(
    storybook: Storybook,
    scene_label: str | None,
    part_name: str | None,
) -> TargetSelection:
    """Resolve the single selected target from the storybook.

    Parameters
    ----------
    storybook:
        Storybook containing the available scenes and illustrated parts.
    scene_label:
        Optional scene label requested by the caller.
    part_name:
        Optional illustrated part name requested by the caller.

    Returns
    -------
    TargetSelection
        Resolved target metadata.

    Raises
    ------
    SystemExit
        If the requested scene or part is unknown or unavailable.
    """

    if scene_label is not None:
        for scene in storybook.scenes:
            if scene.label == scene_label:
                return TargetSelection(
                    kind="scene",
                    identifier=scene.label,
                    display_name=f"Scene {scene.label}",
                    prompt=scene.prompt,
                )
        available_labels = ", ".join(scene.label for scene in storybook.scenes) or "none"
        raise SystemExit(f"Unknown scene label: {scene_label}. Available scenes: {available_labels}.")

    if part_name is None:
        raise SystemExit("Expected exactly one target: --scene or --part.")

    available_parts = {
        name: page
        for name, page in iter_available_illustrated_parts(storybook)
    }
    if part_name not in available_parts:
        available_names = ", ".join(available_parts) or "none"
        raise SystemExit(
            f"Unknown or unavailable illustrated part: {part_name}. "
            f"Available illustrated parts: {available_names}."
        )

    illustration = available_parts[part_name].illustration
    if illustration is None:
        raise SystemExit(f"Illustrated part {part_name} is missing its illustration definition.")

    return TargetSelection(
        kind="part",
        identifier=part_name,
        display_name=PART_DISPLAY_NAMES.get(part_name, part_name),
        prompt=illustration.prompt,
    )


def iter_available_illustrated_parts(storybook: Storybook) -> list[tuple[str, PageSpec]]:
    """Return available illustrated book parts in canonical order.

    Parameters
    ----------
    storybook:
        Storybook containing the non-scene page definitions.

    Returns
    -------
    list[tuple[str, PageSpec]]
        Available illustrated parts paired with their page specs.
    """

    selections: list[tuple[str, PageSpec]] = []
    for name in ILLUSTRATED_PARTS_IN_ORDER:
        page = getattr(storybook.parts, name)
        if page is None or page.illustration is None:
            continue
        selections.append((name, page))
    return selections


def resolve_output_name(requested_name: str | None, target_identifier: str) -> str:
    """Resolve a safe PNG basename for the generated trial output.

    Parameters
    ----------
    requested_name:
        Optional user-provided basename.
    target_identifier:
        Scene label or part name used to build the fallback name.

    Returns
    -------
    str
        Safe output basename without file extension.
    """

    if requested_name is not None:
        return validate_output_name(requested_name)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    target_slug = slugify_name(target_identifier)
    return f"{target_slug}-{timestamp}"


def validate_output_name(output_name: str) -> str:
    """Validate a user-provided output basename.

    Parameters
    ----------
    output_name:
        User-provided basename that should not include directories or an
        extension.

    Returns
    -------
    str
        Validated basename.

    Raises
    ------
    SystemExit
        If the provided name is empty, unsafe, or includes an extension.
    """

    trimmed_name = output_name.strip()
    if not trimmed_name:
        raise SystemExit("Output name must be a non-empty string.")
    if trimmed_name in {".", ".."}:
        raise SystemExit(f"Invalid output name: {output_name!r}.")
    if Path(trimmed_name).name != trimmed_name:
        raise SystemExit(
            f"Expected an output basename like 'cover-v2', not a path like {output_name!r}."
        )
    if Path(trimmed_name).suffix:
        raise SystemExit("Output name must not include a file extension; PNG is always used.")
    return trimmed_name


def slugify_name(value: str) -> str:
    """Convert a target identifier into a filesystem-safe basename fragment.

    Parameters
    ----------
    value:
        Raw identifier to normalize.

    Returns
    -------
    str
        Filesystem-safe lowercase basename fragment.
    """

    stripped_value = value.strip().lower()
    normalized_value = _SAFE_NAME_PATTERN.sub("-", stripped_value)
    collapsed_value = re.sub(r"-{2,}", "-", normalized_value).strip("-.")
    if not collapsed_value:
        return "trial"
    return collapsed_value


if __name__ == "__main__":
    raise SystemExit(main())
