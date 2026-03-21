"""Mutable storybook editor used by the segmentation agent tools."""

from __future__ import annotations

import re
from pathlib import Path

from librito.models import StoryScene, Storybook
from librito.segmentation.session import SegmentationSession
from librito.segmentation.validators import (
    check_prompt_consistency,
    count_concept_occurrences,
    expand_prompt_for_scene,
    is_valid_anchor_tag,
)
from librito.story_io import save_storybook

_GENERATED_SCENE_LABEL_PATTERN = re.compile(r"^scene-(\d{3})$")


class StorybookEditor:
    """Edit a draft storybook stored on disk."""

    def __init__(self, session: SegmentationSession) -> None:
        """Store the backing session and ensure the draft exists.

        Parameters
        ----------
        session:
            Filesystem-backed segmentation session.
        """

        self._session = session
        self._session.ensure_draft_exists()

    def get_full_story(self) -> str:
        """Return the source story text.

        Returns
        -------
        str
            Raw source story.
        """

        return self._session.load_full_story()

    def get_title(self) -> str:
        """Return the current draft title.

        Returns
        -------
        str
            Draft title.
        """

        return self._load().title

    def set_title(self, title: str) -> None:
        """Set the draft title.

        Parameters
        ----------
        title:
            New title value.
        """

        storybook = self._load()
        storybook.title = title.strip()
        self._save(storybook)

    def get_style(self) -> str:
        """Return the current global style.

        Returns
        -------
        str
            Draft style description.
        """

        return self._load().style

    def set_style(self, style: str) -> None:
        """Set the draft style.

        Parameters
        ----------
        style:
            New global style description.
        """

        storybook = self._load()
        storybook.style = style.strip()
        self._save(storybook)

    def get_constraints(self) -> str:
        """Return the current global constraints string.

        Returns
        -------
        str
            Draft constraints string.
        """

        return self._load().constraints

    def set_constraints(self, constraints: str) -> None:
        """Set the draft constraints string.

        Parameters
        ----------
        constraints:
            New constraints text.
        """

        storybook = self._load()
        storybook.constraints = constraints.strip()
        self._save(storybook)

    def list_concepts(self) -> dict[str, str]:
        """Return the currently defined recurring concepts.

        Returns
        -------
        dict[str, str]
            Copy of the concept mapping.
        """

        return dict(self._load().recurring_concepts)

    def add_concept(self, tag: str, value: str) -> None:
        """Add a recurring concept definition.

        Parameters
        ----------
        tag:
            Anchor tag to define.
        value:
            Concept description.

        Raises
        ------
        ValueError
            If the tag format is invalid or already exists.
        """

        normalized_tag = tag.strip()
        if not is_valid_anchor_tag(normalized_tag):
            raise ValueError("Anchor tags must match the strict format <NAME>.")

        storybook = self._load()
        if normalized_tag in storybook.recurring_concepts:
            raise ValueError(f"Recurring concept already exists: {normalized_tag}.")

        storybook.recurring_concepts[normalized_tag] = value.strip()
        self._save(storybook)

    def remove_concept(self, tag: str) -> None:
        """Remove a recurring concept definition.

        Parameters
        ----------
        tag:
            Anchor tag to remove.

        Raises
        ------
        ValueError
            If the concept does not exist.
        """

        storybook = self._load()
        try:
            del storybook.recurring_concepts[tag]
        except KeyError as error:
            raise ValueError(f"Unknown recurring concept: {tag}.") from error
        self._save(storybook)

    def rename_concept(self, old_tag: str, new_tag: str) -> None:
        """Rename a recurring concept and update scene prompts accordingly.

        Parameters
        ----------
        old_tag:
            Existing anchor tag.
        new_tag:
            Replacement anchor tag.
        """

        normalized_new_tag = new_tag.strip()
        if not is_valid_anchor_tag(normalized_new_tag):
            raise ValueError("Anchor tags must match the strict format <NAME>.")

        storybook = self._load()
        if old_tag not in storybook.recurring_concepts:
            raise ValueError(f"Unknown recurring concept: {old_tag}.")
        if normalized_new_tag != old_tag and normalized_new_tag in storybook.recurring_concepts:
            raise ValueError(f"Recurring concept already exists: {normalized_new_tag}.")

        concept_value = storybook.recurring_concepts.pop(old_tag)
        storybook.recurring_concepts[normalized_new_tag] = concept_value
        for scene in storybook.scenes:
            scene.prompt = scene.prompt.replace(old_tag, normalized_new_tag)
        self._save(storybook)

    def list_scenes(self) -> list[dict[str, str]]:
        """Return a summary of existing scenes.

        Returns
        -------
        list[dict[str, str]]
            Ordered scene summaries.
        """

        return [
            {
                "label": scene.label,
                "text": scene.text,
                "prompt": scene.prompt,
            }
            for scene in self._load().scenes
        ]

    def add_scene(
        self,
        text: str,
        prompt: str,
        *,
        label: str | None = None,
        position: int | None = None,
    ) -> str:
        """Add a new scene to the draft.

        Parameters
        ----------
        text:
            Reader-facing scene text.
        prompt:
            Illustration prompt.
        label:
            Optional stable scene identifier.
        position:
            Optional 1-based insertion position. Appends when omitted.

        Returns
        -------
        str
            Label assigned to the new scene.
        """

        storybook = self._load()
        assigned_label = label.strip() if label is not None else self._generate_scene_label(storybook)
        self._validate_scene_label(storybook, assigned_label)
        scene = StoryScene(
            label=assigned_label,
            text=text.strip(),
            prompt=prompt.strip(),
            image_path="",
        )
        insertion_index = self._resolve_insert_index(position, len(storybook.scenes))
        storybook.scenes.insert(insertion_index, scene)
        self._save(storybook)
        return assigned_label

    def update_scene(
        self,
        label: str,
        *,
        text: str | None = None,
        prompt: str | None = None,
        new_label: str | None = None,
    ) -> None:
        """Update an existing scene.

        Parameters
        ----------
        label:
            Current scene label.
        text:
            Optional replacement scene text.
        prompt:
            Optional replacement prompt.
        new_label:
            Optional replacement label.
        """

        storybook = self._load()
        scene = self._get_scene(storybook, label)
        if text is not None:
            scene.text = text.strip()
        if prompt is not None:
            scene.prompt = prompt.strip()
        if new_label is not None:
            normalized_new_label = new_label.strip()
            self._validate_scene_label(storybook, normalized_new_label, current_label=scene.label)
            scene.label = normalized_new_label
        self._save(storybook)

    def move_scene(self, label: str, position: int) -> None:
        """Move a scene to another position in the ordered scene list.

        Parameters
        ----------
        label:
            Scene label to move.
        position:
            Target 1-based position.
        """

        storybook = self._load()
        for scene_index, scene in enumerate(storybook.scenes):
            if scene.label == label:
                moved_scene = storybook.scenes.pop(scene_index)
                insertion_index = self._resolve_insert_index(position, len(storybook.scenes))
                storybook.scenes.insert(insertion_index, moved_scene)
                self._save(storybook)
                return
        raise ValueError(f"Unknown scene label: {label}.")

    def delete_scene(self, label: str) -> None:
        """Delete a scene from the draft.

        Parameters
        ----------
        label:
            Scene label to remove.
        """

        storybook = self._load()
        for scene_index, scene in enumerate(storybook.scenes):
            if scene.label == label:
                del storybook.scenes[scene_index]
                self._save(storybook)
                return
        raise ValueError(f"Unknown scene label: {label}.")

    def count_concept_occurrences(self) -> dict[str, dict[str, object]]:
        """Count concept occurrences across the current draft.

        Returns
        -------
        dict[str, dict[str, object]]
            Usage statistics keyed by anchor tag.
        """

        return count_concept_occurrences(self._load())

    def check_prompt_consistency(self) -> dict[str, object]:
        """Check prompt-consistency rules on the current draft.

        Returns
        -------
        dict[str, object]
            Prompt-consistency report.
        """

        return check_prompt_consistency(self._load())

    def expand_prompt(
        self,
        labels: str | list[str] | None = None,
        *,
        full: bool = False,
    ) -> str | dict[str, str]:
        """Expand one or more scene prompts.

        Parameters
        ----------
        labels:
            Optional single label or list of labels. Expands every scene when
            omitted.
        full:
            When ``True``, include global style and constraints.

        Returns
        -------
        str | dict[str, str]
            Expanded prompt string for a single label, or a mapping for several
            scenes.
        """

        storybook = self._load()
        selected_scenes = self._select_scenes(storybook, labels)
        expanded = {
            scene.label: expand_prompt_for_scene(storybook, scene, full=full)
            for scene in selected_scenes
        }
        if isinstance(labels, str):
            return expanded[labels]
        return expanded

    def expand_scene(
        self,
        labels: str | list[str] | None = None,
        *,
        expand: bool = False,
    ) -> dict[str, str] | list[dict[str, str]]:
        """Return one or more scene payloads.

        Parameters
        ----------
        labels:
            Optional single label or list of labels. Returns every scene when
            omitted.
        expand:
            When ``True``, expand anchors in the returned prompt field.

        Returns
        -------
        dict[str, str] | list[dict[str, str]]
            Scene payload for a single label, or ordered scene payloads for
            several scenes.
        """

        storybook = self._load()
        selected_scenes = self._select_scenes(storybook, labels)
        payload = [
            {
                "label": scene.label,
                "text": scene.text,
                "prompt": expand_prompt_for_scene(storybook, scene, full=False) if expand else scene.prompt,
            }
            for scene in selected_scenes
        ]
        if isinstance(labels, str):
            return payload[0]
        return payload

    def export_storybook(self) -> Path:
        """Validate and export the current draft to the final storybook path.

        Returns
        -------
        Path
            Exported storybook path.

        Raises
        ------
        ValueError
            If prompt-consistency validation fails.
        """

        storybook = self._load()
        report = check_prompt_consistency(storybook)
        if not bool(report["is_valid"]):
            raise ValueError(f"Prompt consistency validation failed: {report}.")
        save_storybook(storybook, self._session.export_path)
        return self._session.export_path

    def _load(self) -> Storybook:
        """Load the current draft storybook.

        Returns
        -------
        Storybook
            Current draft storybook.
        """

        return self._session.load_storybook()

    def _save(self, storybook: Storybook) -> None:
        """Persist the updated draft storybook.

        Parameters
        ----------
        storybook:
            Draft storybook to persist.
        """

        self._session.save_storybook(storybook)

    def _get_scene(self, storybook: Storybook, label: str) -> StoryScene:
        """Resolve a scene by label.

        Parameters
        ----------
        storybook:
            Storybook to search.
        label:
            Requested scene label.

        Returns
        -------
        StoryScene
            Matching scene.
        """

        for scene in storybook.scenes:
            if scene.label == label:
                return scene
        raise ValueError(f"Unknown scene label: {label}.")

    def _select_scenes(
        self,
        storybook: Storybook,
        labels: str | list[str] | None,
    ) -> list[StoryScene]:
        """Resolve one or more scenes preserving story order.

        Parameters
        ----------
        storybook:
            Storybook to inspect.
        labels:
            Optional scene selection.

        Returns
        -------
        list[StoryScene]
            Matching ordered scenes.
        """

        if labels is None:
            return list(storybook.scenes)
        if isinstance(labels, str):
            return [self._get_scene(storybook, labels)]
        requested_labels = set(labels)
        selected = [scene for scene in storybook.scenes if scene.label in requested_labels]
        if len(selected) != len(requested_labels):
            missing = sorted(requested_labels - {scene.label for scene in selected})
            raise ValueError(f"Unknown scene labels: {missing!r}.")
        return selected

    def _validate_scene_label(
        self,
        storybook: Storybook,
        label: str,
        *,
        current_label: str | None = None,
    ) -> None:
        """Validate a scene label against uniqueness and basic shape rules.

        Parameters
        ----------
        storybook:
            Storybook receiving the label.
        label:
            Candidate scene label.
        current_label:
            Existing scene label when updating in place.
        """

        if not label or label != label.strip():
            raise ValueError("Scene labels must be non-empty trimmed strings.")
        for scene in storybook.scenes:
            if scene.label == label and scene.label != current_label:
                raise ValueError(f"Scene label already exists: {label}.")

    def _generate_scene_label(self, storybook: Storybook) -> str:
        """Generate the next default scene label.

        Parameters
        ----------
        storybook:
            Storybook receiving the new scene.

        Returns
        -------
        str
            Fresh default label following the ``scene-001`` convention.
        """

        next_index = 1
        for scene in storybook.scenes:
            match = _GENERATED_SCENE_LABEL_PATTERN.fullmatch(scene.label)
            if match is None:
                continue
            next_index = max(next_index, int(match.group(1)) + 1)
        return f"scene-{next_index:03d}"

    def _resolve_insert_index(self, position: int | None, scene_count: int) -> int:
        """Convert a 1-based insertion position to a Python list index.

        Parameters
        ----------
        position:
            Optional 1-based position.
        scene_count:
            Current number of scenes.

        Returns
        -------
        int
            Zero-based insertion index.
        """

        if position is None:
            return scene_count
        if position < 1 or position > scene_count + 1:
            raise ValueError(f"Scene position must be between 1 and {scene_count + 1}.")
        return position - 1
