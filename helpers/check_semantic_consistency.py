"""Analyse the semantic consistency of a segmented storybook."""

from __future__ import annotations

import math
import statistics
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence

from librito.io import load_normalized_story, load_storybook
from librito.providers import build_embedding_client

_DATABASE_DIRECTORY = Path(__file__).resolve().parent.parent / "database"
_STORYBOOK_FILENAME = "story.json"
_UNITS_FILENAME = "units.json"


def load_parameters(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command-line arguments."""

    parser = ArgumentParser(
        description="Analyse semantic consistency between scene texts and normalized story units.",
    )
    parser.add_argument(
        "--storybook",
        required=True,
        type=str,
        help="Storybook label. Files are resolved from ./database/<label>/.",
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
    story_directory = _DATABASE_DIRECTORY / arguments.storybook
    storybook_path = story_directory / _STORYBOOK_FILENAME
    units_path = story_directory / _UNITS_FILENAME
    if not story_directory.is_dir():
        raise SystemExit(f"Missing story directory: {story_directory}")
    if not storybook_path.is_file():
        raise SystemExit(f"Missing required file: {storybook_path}")
    if not units_path.is_file():
        raise SystemExit(f"Missing required file: {units_path}")

    storybook = load_storybook(storybook_path)
    normalized_story = load_normalized_story(units_path)
    client = build_embedding_client(provider=arguments.provider, model=arguments.model)

    if not storybook.scenes:
        raise ValueError("The storybook does not contain any scenes to evaluate.")
    if not normalized_story.units:
        raise ValueError("The normalized story does not contain any units to evaluate.")

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
        "Semantic consistency report",
        f"Title: {storybook.title}",
        f"Provider: {arguments.provider}",
        f"Model: {arguments.model}",
        f"Scenes: {len(storybook.scenes)}",
        f"Story units: {len(normalized_story.units)}",
        "",
        "Score summary:",
        f"- count: {len(scores)}",
        f"- mean: {statistics.fmean(scores):.4f}",
        f"- std: {statistics.pstdev(scores) if len(scores) > 1 else 0.0:.4f}",
        f"- min: {min(scores):.4f}",
        f"- median: {statistics.median(scores):.4f}",
        f"- max: {max(scores):.4f}",
        "",
        "Scene breakdown:",
    ]

    for item in scene_scores:
        lines.extend(
            [
                f"- {item['scene_label']}: {float(item['score']):.4f}",
                f"  best unit: {item['unit_label']} ({item['unit_type']})",
                f"  scene: {_shorten(str(item['scene_text']))}",
                f"  match: {_shorten(str(item['unit_text']))}",
            ]
        )

    sys.stdout.write("\n".join(lines) + "\n")
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
