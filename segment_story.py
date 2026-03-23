"""Run the story-segmentation agent on a filesystem-backed draft.

The ``--storybook`` argument points to a story folder (e.g.
``./database/my-story/``).  The script expects the following convention
inside that folder:

* ``story.md`` — full source story text,
* ``story.json`` — exported storybook (segmentation output),
* ``story.segmentation.draft.json`` — intermediate draft file.

Story loading behavior:

* when ``--story-file`` is provided, its content is copied into
  ``<storybook>/story.md`` before the agent starts, overriding any
  existing file there;
* when ``--story-file`` is omitted, the script expects an existing
  ``<storybook>/story.md`` file and loads the source story from it;
* the script raises if the expected story file is missing, unreadable, or empty.

Provider-specific authentication:

* ``gemini`` reads its API key exclusively from ``GEMINI_API_KEY``;
* ``lms`` reads its API base URL from ``LMS_API_URL`` and its API key from
  ``LMS_API_KEY`` (falling back to ``not-used`` when absent).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from importlib import resources
from pathlib import Path
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.events.event import Event
from google.adk.runners import InMemoryRunner
from google.genai import types

from librito.models import Storybook
from librito.providers import build_segmentation_model
from librito.segmentation.session import SegmentationSession
from librito.segmentation.tools import _STATE_SEGMENTATION_DONE
from librito.segmentation.tools import _STATE_SEGMENTATION_SUMMARY
from librito.segmentation.tools import build_toolset
from librito.story_io import load_storybook
from librito.story_io import save_storybook

logger = logging.getLogger(__name__)

_APP_NAME = "librito_story_segmentation"
_DEFAULT_EXPORT_FILENAME = "story.json"
_DEFAULT_DRAFT_FILENAME = "story.segmentation.draft.json"
_DEFAULT_STORY_FILENAME = "story.md"
_RESOURCE_DIRECTORY = resources.files("librito.resources")
_SEGMENTATION_INSTRUCTION_FILENAME = "segmentation_agent_instruction.txt"


def _parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed CLI arguments.
    """

    parser = argparse.ArgumentParser(description="Run the story-segmentation agent.")
    parser.add_argument(
        "--storybook",
        required=True,
        type=Path,
        help="Path to the story folder (must contain or will receive story.md).",
    )
    parser.add_argument(
        "--story-file",
        type=Path,
        default=None,
        help="Optional source story file. When provided, it overrides <storybook>/story.md before the run.",
    )
    parser.add_argument(
        "--provider",
        choices=("gemini", "lms"),
        required=True,
        help="LLM provider used for the segmentation agent.",
    )
    parser.add_argument("--model", required=True, help="Model identifier used by the selected provider.")
    parser.add_argument("--user-id", default="local_user", help="ADK user identifier for the session.")
    return parser.parse_args()


def _load_segmentation_agent_instruction() -> str:
    """Load the segmentation agent instruction from package resources.

    Returns
    -------
    str
        Instruction text passed to the segmentation agent.
    """

    return _RESOURCE_DIRECTORY.joinpath(_SEGMENTATION_INSTRUCTION_FILENAME).read_text(
        encoding="utf-8"
    ).strip()


def _prepare_session(arguments: argparse.Namespace) -> SegmentationSession:
    """Prepare the filesystem-backed session paths.

    Parameters
    ----------
    arguments:
        Parsed CLI arguments.

    Returns
    -------
    SegmentationSession
        Ready-to-use segmentation session.
    """

    story_directory = arguments.storybook
    story_directory.mkdir(parents=True, exist_ok=True)
    logger.info("Story directory: %s.", story_directory)

    story_path = story_directory / _DEFAULT_STORY_FILENAME
    if arguments.story_file is not None:
        story_text = _read_story_text(arguments.story_file)
        story_path.write_text(story_text, encoding="utf-8")
        logger.info("Copied story text from %s to %s.", arguments.story_file, story_path)
    elif not story_path.exists():
        raise RuntimeError(
            f"Missing source story file: {story_path}. "
            "Provide --story-file for the first run or restore story.md in the story folder."
        )
    else:
        _read_story_text(story_path)
        logger.info("Loaded existing story from %s.", story_path)

    session = SegmentationSession(
        story_path=story_path,
        draft_path=story_directory / _DEFAULT_DRAFT_FILENAME,
        export_path=story_directory / _DEFAULT_EXPORT_FILENAME,
    )
    _prepare_draft(session)
    logger.info("Segmentation session ready (draft: %s, export: %s).", session.draft_path, session.export_path)
    return session


def _build_prompt(story_directory: Path) -> str:
    """Build the single user prompt used to drive the segmentation run.

    Parameters
    ----------
    story_directory:
        Story folder path.

    Returns
    -------
    str
        Initial user prompt sent to the agent.
    """

    label = story_directory.name
    return (
        f"Segment the story stored for label '{label}'. "
        "Inspect the story and current state with tools, build or refine the segmentation, "
        "export only if needed, and call finish_segmentation when the work is complete."
    )


def _read_story_text(path: Path) -> str:
    """Read and validate a source story file.

    Parameters
    ----------
    path:
        Story text file to load.

    Returns
    -------
    str
        Non-empty story text.

    Raises
    ------
    RuntimeError
        If the file cannot be read or contains only whitespace.
    """

    try:
        story_text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"Failed to read story text from {path}: {error}.") from error
    if not story_text.strip():
        raise RuntimeError(f"Story text file is empty: {path}.")
    return story_text


def _prepare_draft(session: SegmentationSession) -> None:
    """Validate an existing draft or create an empty one when missing.

    Parameters
    ----------
    session:
        Filesystem-backed segmentation session.
    """

    if session.draft_path.exists():
        load_storybook(session.draft_path)
        logger.info("Loaded existing draft from %s.", session.draft_path)
        return

    save_storybook(
        Storybook(
            title="",
            style="",
            constraints="",
            recurring_concepts={},
            scenes=[],
        ),
        session.draft_path,
    )
    logger.info("Initialized empty draft at %s.", session.draft_path)


def _log_agent_event(event: Event) -> None:
    """Log the visible content produced during one agent event.

    Parameters
    ----------
    event:
        Streamed ADK event emitted during the agent run.
    """

    logger.info(
        "Agent event from %s (partial=%s, turn_complete=%s, finish_reason=%s).",
        event.author,
        event.partial,
        event.turn_complete,
        event.finish_reason,
    )
    if event.error_code or event.error_message:
        logger.warning(
            "Agent event error: code=%s message=%s.",
            event.error_code,
            event.error_message,
        )
    if not event.content or not event.content.parts:
        return

    for part in event.content.parts:
        if part.function_call is not None:
            logger.info(
                "Tool call: %s(%s)",
                part.function_call.name,
                _format_tool_arguments(part.function_call.args),
            )
        if part.text:
            if part.thought:
                logger.info("Model thought: %s", part.text.strip())
            else:
                logger.info("Assistant response: %s", part.text.strip())


def _format_tool_arguments(arguments: dict[str, Any] | None) -> str:
    """Format tool-call arguments for logging.

    Parameters
    ----------
    arguments:
        Tool-call arguments to render.

    Returns
    -------
    str
        Human-readable string representation of the arguments.
    """

    if not arguments:
        return "{}"
    return repr(arguments)


async def _run() -> int:
    """Run the segmentation agent once and print its final response.

    Returns
    -------
    int
        Process exit status.
    """

    arguments = _parse_arguments()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    logger.info("Starting segmentation for '%s' (provider: %s, model: %s).",
                arguments.storybook, arguments.provider, arguments.model)
    session = _prepare_session(arguments)

    logger.info("Building segmentation agent...")
    agent = LlmAgent(
        name="segment_story_agent",
        model=build_segmentation_model(
            provider=arguments.provider,
            model=arguments.model,
        ),
        instruction=_load_segmentation_agent_instruction(),
        tools=build_toolset(),
    )
    runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
    adk_session = await runner.session_service.create_session(
        app_name=_APP_NAME,
        user_id=arguments.user_id,
        state={
            "story_path": str(session.story_path),
            "draft_path": str(session.draft_path),
            "export_path": str(session.export_path),
            _STATE_SEGMENTATION_DONE: False,
            _STATE_SEGMENTATION_SUMMARY: "",
        },
    )
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=_build_prompt(arguments.storybook))],
    )

    logger.info("Running segmentation agent...")
    async for event in runner.run_async(
        user_id=arguments.user_id,
        session_id=adk_session.id,
        new_message=user_message,
    ):
        _log_agent_event(event)
        if event.actions.state_delta.get(_STATE_SEGMENTATION_DONE) is True:
            logger.info("Segmentation agent explicitly marked the run as complete.")

    completed_session = await runner.session_service.get_session(
        app_name=_APP_NAME,
        user_id=arguments.user_id,
        session_id=adk_session.id,
    )
    if completed_session is None:
        raise RuntimeError("Failed to reload the ADK session after the segmentation run.")

    if completed_session.state.get(_STATE_SEGMENTATION_DONE) is not True:
        raise RuntimeError("The agent finished without calling finish_segmentation().")

    summary = str(completed_session.state.get(_STATE_SEGMENTATION_SUMMARY, "")).strip()
    if not summary:
        raise RuntimeError("The agent called finish_segmentation() without a final summary.")

    print(summary)
    logger.info("Segmentation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
