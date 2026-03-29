"""Analyse the semantic consistency of a segmented storybook."""

from __future__ import annotations

import logging
import math
import statistics
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.logging import add_logging_arguments, configure_logging
from librito.io import load_normalized_story, load_storybook
from librito.providers import build_embedding_client
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)


def load_parameters(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command-line arguments."""

    parser = ArgumentParser(
        description="Analyse semantic consistency between scene texts and normalized story units.",
    )
    add_logging_arguments(parser)
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story identifier stored under ./database/<story>/.",
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=["gemini", "lms", "mock"],
        help="Embedding provider.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Embedding model.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the semantic consistency helper."""

    arguments = load_parameters(argv)
    configure_logging(arguments.log_level)
    logger.info("Starting semantic consistency check for story '%s'.", arguments.story)
    workspace = StoryWorkspace.from_story(arguments.story)
    workspace.require_directory()
    storybook_path = workspace.require_storybook_file()
    units_path = workspace.require_units_file()
    logger.info("Loading storybook from %s.", storybook_path)
    storybook = load_storybook(storybook_path)
    logger.info("Loading normalized story from %s.", units_path)
    normalized_story = load_normalized_story(units_path)
    logger.info("Building embedding client (provider=%s, model=%s).", arguments.provider, arguments.model)
    client = build_embedding_client(provider=arguments.provider, model=arguments.model)

    if not storybook.scenes:
        raise ValueError("The storybook does not contain any scenes to evaluate.")
    if not normalized_story.units:
        raise ValueError("The normalized story does not contain any units to evaluate.")

    logger.info(
        "Computing semantic similarity for %d scene(s) against %d unit(s).",
        len(storybook.scenes),
        len(normalized_story.units),
    )
    unit_embeddings = client.embed_texts([unit.text for unit in normalized_story.units])
    scene_embeddings = client.embed_texts([scene.text for scene in storybook.scenes])

    scene_scores: list[dict[str, object]] = []
    for scene, scene_embedding in zip(storybook.scenes, scene_embeddings):
        best_score = _cosine_similarity(scene_embedding, unit_embeddings[0])
        best_unit = normalized_story.units[0]
        for unit, unit_embedding in zip(normalized_story.units[1:], unit_embeddings[1:]):
            score = _cosine_similarity(scene_embedding, unit_embedding)
            if score > best_score:
                best_score = score
                best_unit = unit

        scene_scores.append(
            {
                "scene_label": scene.label,
                "scene_text": scene.text,
                "score": best_score,
                "unit_label": best_unit.label,
                "unit_type": best_unit.type,
                "unit_text": best_unit.text,
            }
        )

    scores = [float(item["score"]) for item in scene_scores]
    lines = [
        "# Semantic Consistency Report",
        "",
        f"- **Story:** {workspace.story}",
        f"- **Title:** {storybook.title}",
        f"- **Provider:** {arguments.provider}",
        f"- **Model:** {arguments.model}",
        f"- **Scenes:** {len(storybook.scenes)}",
        f"- **Story units:** {len(normalized_story.units)}",
        "",
        "## Score Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Count | {len(scores)} |",
        f"| Mean | {statistics.fmean(scores):.4f} |",
        f"| Standard deviation | {statistics.pstdev(scores) if len(scores) > 1 else 0.0:.4f} |",
        f"| Minimum | {min(scores):.4f} |",
        f"| Median | {statistics.median(scores):.4f} |",
        f"| Maximum | {max(scores):.4f} |",
        "",
        "## Scene Breakdown",
    ]

    for item in scene_scores:
        lines.extend(
            [
                "",
                f"### {item['scene_label']}",
                "",
                f"- **Score:** {float(item['score']):.4f}",
                f"- **Best unit:** {item['unit_label']} ({item['unit_type']})",
                f"- **Scene excerpt:** {_shorten(str(item['scene_text']))}",
                f"- **Best-match excerpt:** {_shorten(str(item['unit_text']))}",
            ]
        )

    sys.stdout.write("\n".join(lines) + "\n")
    logger.info("Semantic consistency check complete.")
    return 0


def _cosine_similarity(first: Sequence[float], second: Sequence[float]) -> float:
    """Return the cosine similarity between two vectors."""

    if len(first) != len(second):
        raise ValueError("Embedding vectors must have the same dimensionality.")

    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    if first_norm == 0.0 or second_norm == 0.0:
        return 0.0

    return sum(left * right for left, right in zip(first, second)) / (first_norm * second_norm)


def _shorten(text: str, max_length: int = 96) -> str:
    """Collapse whitespace and trim long text for compact output."""

    collapsed = " ".join(text.split())
    if len(collapsed) <= max_length:
        return collapsed
    return f"{collapsed[: max_length - 3]}..."


if __name__ == "__main__":
    raise SystemExit(main())
