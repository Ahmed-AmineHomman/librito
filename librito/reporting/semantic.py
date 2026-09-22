"""Semantic consistency analysis for storybooks."""

from __future__ import annotations

import math
import statistics
from typing import Sequence

import logging

from librito.io import load_storybook, load_units
from librito.providers import build_embedding_client
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)


def build_semantic_report(
        story: str,
        provider: str,
        model: str,
        details: str,
        scenes: Sequence[str] | None = None,
) -> str:
    """Build a Markdown semantic consistency report.

    Parameters
    ----------
    story:
        Story identifier stored under ``database/``.
    provider:
        Embedding provider name.
    model:
        Embedding model name.
    details:
        Detail level for the report.
    scenes:
        Optional scene labels to expand when ``details`` is ``selected``.

    Returns
    -------
    str
        Markdown report suitable for stdout.
    """

    requested_scenes = _deduplicate(scenes or [])
    workspace = StoryWorkspace.from_story(story)
    workspace.require_directory()
    storybook_path = workspace.require_storybook_file()
    units_path = workspace.require_units_file()
    logger.info("Loading storybook from %s.", storybook_path)
    storybook = load_storybook(storybook_path)
    logger.info("Loading units from %s.", units_path)
    units = load_units(units_path)

    if not storybook.scenes:
        raise ValueError("The storybook does not contain any scenes to evaluate.")
    if not units.units:
        raise ValueError("The units file does not contain any units to evaluate.")

    selected_scene_labels = _resolve_scene_labels(
        available_labels=[scene.label for scene in storybook.scenes],
        details=details,
        requested_labels=requested_scenes,
    )
    logger.info("Building embedding client (provider=%s, model=%s).", provider, model)
    client = build_embedding_client(provider=provider, model=model)

    logger.info(
        "Computing semantic similarity for %d scene(s) against %d unit(s).",
        len(storybook.scenes),
        len(units.units),
    )
    unit_embeddings = client.embed_texts([unit.text for unit in units.units])
    scene_embeddings = client.embed_texts([scene.text for scene in storybook.scenes])

    scene_scores: list[dict[str, object]] = []
    for scene, scene_embedding in zip(storybook.scenes, scene_embeddings):
        best_score = _cosine_similarity(scene_embedding, unit_embeddings[0])
        best_unit = units.units[0]
        for unit, unit_embedding in zip(units.units[1:], unit_embeddings[1:]):
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

    scene_scores_by_label = {
        str(item["scene_label"]): item
        for item in scene_scores
    }
    scores = [float(item["score"]) for item in scene_scores]
    lines = [
        "# Semantic Consistency Report",
        "",
        f"- **Story:** {workspace.story}",
        f"- **Title:** {storybook.title}",
        f"- **Provider:** {provider}",
        f"- **Model:** {model}",
        f"- **Scenes:** {len(storybook.scenes)}",
        f"- **Units:** {len(units.units)}",
        f"- **Detail mode:** {details}",
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
    ]

    if details != "summary":
        lines.extend(
            [
                "",
                "## Scene Breakdown",
                "",
                f"- **Scenes detailed:** {len(selected_scene_labels)}",
            ]
        )
        for label in selected_scene_labels:
            item = scene_scores_by_label[label]
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

    logger.info("Semantic consistency check complete.")
    return "\n".join(lines)


def _resolve_scene_labels(
        available_labels: Sequence[str],
        details: str,
        requested_labels: Sequence[str],
) -> list[str]:
    """Resolve which scene labels should receive detailed output.

    Parameters
    ----------
    available_labels:
        Scene labels present in the storybook, in story order.
    details:
        Requested detail level.
    requested_labels:
        Scene labels explicitly requested by the caller.

    Returns
    -------
    list[str]
        Scene labels to expand in the report.

    Raises
    ------
    SystemExit
        If the requested labels include unknown scenes.
    """

    if details == "summary":
        return []
    if details == "all":
        return list(available_labels)

    unknown_labels = [label for label in requested_labels if label not in set(available_labels)]
    if unknown_labels:
        raise SystemExit(f"Unknown scene label(s): {', '.join(unknown_labels)}")
    return list(requested_labels)


def _deduplicate(values: Sequence[str]) -> list[str]:
    """Return values without duplicates while preserving their first-seen order.

    Parameters
    ----------
    values:
        Input strings in arbitrary order.

    Returns
    -------
    list[str]
        Deduplicated values.
    """

    ordered_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            continue
        seen_values.add(value)
        ordered_values.append(value)
    return ordered_values


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
