"""ADK tool wrappers for story segmentation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.adk.tools import ToolContext

from librito.segmentation.editor import StorybookEditor
from librito.segmentation.session import SegmentationSession
from librito.segmentation.validators import normalize_anchor_tag

_STATE_STORY_PATH = "story_path"
_STATE_DRAFT_PATH = "draft_path"
_STATE_EXPORT_PATH = "export_path"
_STATE_SEGMENTATION_DONE = "segmentation_done"
_STATE_SEGMENTATION_SUMMARY = "segmentation_summary"


def get_full_story(tool_context: ToolContext) -> dict[str, str]:
    """Return the full raw story text loaded for the current session."""

    return _execute_tool_action(
        lambda: {"full_story": _build_editor(tool_context).get_full_story()},
    )


def get_title(tool_context: ToolContext) -> dict[str, str]:
    """Return the current draft title."""

    return _execute_tool_action(
        lambda: {"title": _build_editor(tool_context).get_title()},
    )


def set_title(title: str, tool_context: ToolContext) -> dict[str, str]:
    """Set the current draft title."""

    return _execute_tool_action(lambda: (_build_editor(tool_context).set_title(title), {"title": title.strip()})[1])


def get_style(tool_context: ToolContext) -> dict[str, str]:
    """Return the current draft style."""

    return _execute_tool_action(
        lambda: {"style": _build_editor(tool_context).get_style()},
    )


def set_style(style: str, tool_context: ToolContext) -> dict[str, str]:
    """Set the current draft style."""

    return _execute_tool_action(lambda: (_build_editor(tool_context).set_style(style), {"style": style.strip()})[1])


def get_constraints(tool_context: ToolContext) -> dict[str, str]:
    """Return the current draft constraints string."""

    return _execute_tool_action(
        lambda: {"constraints": _build_editor(tool_context).get_constraints()},
    )


def set_constraints(constraints: str, tool_context: ToolContext) -> dict[str, str]:
    """Set the current draft constraints string."""

    return _execute_tool_action(
        lambda: (_build_editor(tool_context).set_constraints(constraints), {"constraints": constraints.strip()})[1]
    )


def list_concepts(tool_context: ToolContext) -> dict[str, dict[str, str]]:
    """Return all currently defined recurring concepts."""

    return _execute_tool_action(
        lambda: {"recurring_concepts": _build_editor(tool_context).list_concepts()},
    )


def add_concept(name: str, value: str, tool_context: ToolContext) -> dict[str, str]:
    """Add a recurring concept definition from a plain concept name."""

    return _execute_tool_action(
        lambda: (_build_editor(tool_context).add_concept(name, value), {"tag": normalize_anchor_tag(name)})[1],
    )


def remove_concept(name: str, tool_context: ToolContext) -> dict[str, str]:
    """Remove a recurring concept definition using a plain concept name."""

    return _execute_tool_action(
        lambda: (_build_editor(tool_context).remove_concept(name), {"tag": normalize_anchor_tag(name)})[1],
    )


def rename_concept(old_name: str, new_name: str, tool_context: ToolContext) -> dict[str, str]:
    """Rename a recurring concept and update prompts that reference it."""

    return _execute_tool_action(
        lambda: (
            _build_editor(tool_context).rename_concept(old_name, new_name),
            {
                "old_tag": normalize_anchor_tag(old_name),
                "new_tag": normalize_anchor_tag(new_name),
            },
        )[1],
    )


def list_scenes(tool_context: ToolContext) -> dict[str, list[dict[str, str]]]:
    """Return the ordered draft scenes."""

    return _execute_tool_action(
        lambda: {"scenes": _build_editor(tool_context).list_scenes()},
    )


def add_scene(
    text: str,
    prompt: str,
    label: str | None = None,
    position: int | None = None,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Add a new scene to the current draft."""

    return _execute_tool_action(
        lambda: {
            "label": _build_editor(_require_tool_context(tool_context)).add_scene(
                text=text,
                prompt=prompt,
                label=label,
                position=position,
            )
        },
    )


def update_scene(
    label: str,
    text: str | None = None,
    prompt: str | None = None,
    new_label: str | None = None,
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Update a scene's content and optionally rename its label."""

    return _execute_tool_action(
        lambda: (
            _build_editor(_require_tool_context(tool_context)).update_scene(
                label,
                text=text,
                prompt=prompt,
                new_label=new_label,
            ),
            {"label": new_label.strip() if new_label is not None else label},
        )[1],
    )


def move_scene(label: str, position: int, tool_context: ToolContext) -> dict[str, Any]:
    """Move an existing scene to another position."""

    return _execute_tool_action(
        lambda: (_build_editor(tool_context).move_scene(label, position), {"label": label, "position": position})[1],
    )


def delete_scene(label: str, tool_context: ToolContext) -> dict[str, str]:
    """Delete a scene from the current draft."""

    return _execute_tool_action(
        lambda: (_build_editor(tool_context).delete_scene(label), {"label": label})[1],
    )


def count_concept_occurrences(tool_context: ToolContext) -> dict[str, dict[str, object]]:
    """Count recurring concept usage across the current draft."""

    return _execute_tool_action(
        lambda: {"occurrences": _build_editor(tool_context).count_concept_occurrences()},
    )


def check_prompt_consistency(tool_context: ToolContext) -> dict[str, object]:
    """Return the current prompt-consistency report."""

    return _execute_tool_action(
        lambda: {"report": _build_editor(tool_context).check_prompt_consistency()},
    )


def expand_prompt(
    label: str | None = None,
    labels: list[str] | None = None,
    full: bool = False,
    tool_context: ToolContext | None = None,
) -> dict[str, object]:
    """Expand one or more scene prompts."""

    selection = _normalize_scene_selection(label, labels)
    return _execute_tool_action(
        lambda: {
            "expanded_prompts": _build_editor(_require_tool_context(tool_context)).expand_prompt(
                selection,
                full=full,
            )
        },
    )


def expand_scene(
    label: str | None = None,
    labels: list[str] | None = None,
    expand: bool = False,
    tool_context: ToolContext | None = None,
) -> dict[str, object]:
    """Return one or more scene payloads."""

    selection = _normalize_scene_selection(label, labels)
    return _execute_tool_action(
        lambda: {
            "scenes": _build_editor(_require_tool_context(tool_context)).expand_scene(
                selection,
                expand=expand,
            )
        },
    )


def export_storybook(tool_context: ToolContext) -> dict[str, str]:
    """Validate the current draft and export the final storybook JSON."""

    return _execute_tool_action(
        lambda: {"export_path": str(_build_editor(tool_context).export_storybook())},
    )


def finish_segmentation(summary: str, tool_context: ToolContext) -> dict[str, str]:
    """Mark the current segmentation run as complete and stop the invocation.

    Parameters
    ----------
    summary:
        Short final summary describing the resulting segmentation.
    tool_context:
        ADK tool context for the current invocation.

    Returns
    -------
    dict[str, str]
        Stored final summary.
    """

    def _finish() -> dict[str, str]:
        normalized_summary = summary.strip()
        if not normalized_summary:
            raise ValueError("Summary must not be empty.")
        tool_context.state[_STATE_SEGMENTATION_DONE] = True
        tool_context.state[_STATE_SEGMENTATION_SUMMARY] = normalized_summary
        tool_context.actions.skip_summarization = True
        tool_context._invocation_context.end_invocation = True
        return {"summary": normalized_summary}

    return _execute_tool_action(_finish)


def build_toolset() -> list[Any]:
    """Build the raw function tool list for the segmentation agent.

    Returns
    -------
    list[Any]
        Plain Python callables ready to pass to ADK.
    """

    return [
        get_full_story,
        get_title,
        set_title,
        get_style,
        set_style,
        get_constraints,
        set_constraints,
        list_concepts,
        add_concept,
        remove_concept,
        rename_concept,
        list_scenes,
        add_scene,
        update_scene,
        move_scene,
        delete_scene,
        count_concept_occurrences,
        check_prompt_consistency,
        expand_prompt,
        expand_scene,
        export_storybook,
        finish_segmentation,
    ]


def _build_editor(tool_context: ToolContext) -> StorybookEditor:
    """Instantiate an editor from the current ADK session state.

    Parameters
    ----------
    tool_context:
        ADK tool context containing the session state.

    Returns
    -------
    StorybookEditor
        Filesystem-backed draft editor.
    """

    state = tool_context.state
    session = SegmentationSession(
        story_path=Path(str(state[_STATE_STORY_PATH])),
        draft_path=Path(str(state[_STATE_DRAFT_PATH])),
        export_path=Path(str(state[_STATE_EXPORT_PATH])),
    )
    return StorybookEditor(session)


def _require_tool_context(tool_context: ToolContext | None) -> ToolContext:
    """Require a non-null ADK tool context.

    Parameters
    ----------
    tool_context:
        Optional ADK tool context.

    Returns
    -------
    ToolContext
        Validated tool context.
    """

    if tool_context is None:
        raise ValueError("ADK tool context is required.")
    return tool_context


def _execute_tool_action(action: Any) -> dict[str, Any]:
    """Run a tool action and convert recoverable failures into tool responses.

    Parameters
    ----------
    action:
        Zero-argument callable performing the tool side effect.
    Returns
    -------
    dict[str, Any]
        Structured tool response.
    """

    try:
        payload = action()
    except (RuntimeError, ValueError, OSError) as error:
        return {
            "status": "error",
            "error": str(error),
        }
    return _success(**payload)


def _success(**payload: Any) -> dict[str, Any]:
    """Build a successful structured tool response.

    Parameters
    ----------
    payload:
        Response payload fields.

    Returns
    -------
    dict[str, Any]
        Structured success response.
    """

    return {
        "status": "success",
        **payload,
    }


def _normalize_scene_selection(
    label: str | None,
    labels: list[str] | None,
) -> str | list[str] | None:
    """Normalize mutually exclusive scene-selection parameters.

    Parameters
    ----------
    label:
        Optional single scene label.
    labels:
        Optional multiple scene labels.

    Returns
    -------
    str | list[str] | None
        Normalized scene selection.
    """

    if label is not None and labels is not None:
        raise ValueError("Use either 'label' or 'labels', not both.")
    if label is not None:
        return label
    if labels is not None:
        return labels
    return None
