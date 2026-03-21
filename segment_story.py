"""Run the story-segmentation agent on a filesystem-backed draft.

The script stores each story under ``./database/<label>/`` by default.

Story loading behavior:

* when ``--story-file`` is provided, its content is copied into
  ``./database/<label>/story.md`` before the agent starts, overriding any
  existing file there;
* when ``--story-file`` is omitted, the script expects an existing
  ``./database/<label>/story.md`` file and loads the source story from it;
* the script raises if the expected story file is missing, unreadable, or empty.

Provider-specific authentication:

* ``gemini`` reads its API key exclusively from ``GEMINI_API_KEY``;
* ``lms`` targets LM Studio's OpenAI-style ``/v1`` API, optionally accepts
  ``--api-key``, and otherwise uses the literal placeholder ``not-used``.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

from librito.segmentation.session import SegmentationSession
from librito.segmentation.tools import build_toolset

_APP_NAME = "librito_story_segmentation"
_DEFAULT_DATABASE_ROOT = Path("database")
_DEFAULT_EXPORT_FILENAME = "story.json"
_DEFAULT_DRAFT_FILENAME = "story.segmentation.draft.json"
_DEFAULT_STORY_FILENAME = "story.md"
_DEFAULT_GEMINI_API_ENV_VAR = "GEMINI_API_KEY"

_SEGMENTATION_AGENT_INSTRUCTION = """
You are an agent that segments one story into the Librito storybook standard.

You must work through the available tools.
Use the tools to inspect the full story and the current draft state before changing anything.

Your goal is to produce a complete segmented storybook with:
- a title,
- one global visual style in English,
- optional constraints,
- recurring concepts using strict anchor tags such as <LEO>,
- ordered scenes identified by stable labels,
- scene text in the language of the original story,
- scene prompts in English.

Prompt-consistency rules:
- recurring concepts used in more than one scene should be anchored,
- concepts that appear in a single scene should not remain as recurring concepts,
- every anchor used in a scene prompt must be defined,
- unused recurring concepts must be removed,
- anchors used in only one unique scene must be removed or inlined.

Operational rules:
- the scene list order defines narrative order,
- do not modify image paths,
- use check_prompt_consistency before exporting,
- only call export_storybook when the prompt-consistency report is valid,
- after exporting, respond with a short summary of the resulting segmentation.
""".strip()


def _parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed CLI arguments.
    """

    parser = argparse.ArgumentParser(description="Run the story-segmentation agent.")
    parser.add_argument("--label", required=True, help="Story label used under ./database.")
    parser.add_argument(
        "--story-file",
        type=Path,
        default=None,
        help="Optional source story file. When provided, it overrides ./database/<label>/story.md before the run.",
    )
    parser.add_argument(
        "--database-root",
        type=Path,
        default=_DEFAULT_DATABASE_ROOT,
        help="Database root directory containing story folders. Defaults to ./database.",
    )
    parser.add_argument(
        "--provider",
        choices=("gemini", "lms"),
        required=True,
        help="LLM provider used for the segmentation agent.",
    )
    parser.add_argument("--model", required=True, help="Model identifier used by the selected provider.")
    parser.add_argument(
        "--api-base",
        default=None,
        help="LM Studio API base URL. The script accepts either a server root such as http://127.0.0.1:1234 or a full /v1 base URL.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional explicit API key used only for the lms provider.",
    )
    parser.add_argument("--user-id", default="local_user", help="ADK user identifier for the session.")
    return parser.parse_args()


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

    story_directory = arguments.database_root / arguments.label
    story_directory.mkdir(parents=True, exist_ok=True)

    story_path = story_directory / _DEFAULT_STORY_FILENAME
    if arguments.story_file is not None:
        story_text = _read_story_text(arguments.story_file)
        story_path.write_text(story_text, encoding="utf-8")
    elif not story_path.exists():
        raise RuntimeError(
            f"Missing source story file: {story_path}. "
            "Provide --story-file for the first run or restore story.md in the story folder."
        )
    else:
        _read_story_text(story_path)

    session = SegmentationSession(
        story_path=story_path,
        draft_path=story_directory / _DEFAULT_DRAFT_FILENAME,
        export_path=story_directory / _DEFAULT_EXPORT_FILENAME,
    )
    session.ensure_draft_exists()
    return session


def _build_model(arguments: argparse.Namespace) -> str | LiteLlm:
    """Build the ADK model object for the selected provider.

    Parameters
    ----------
    arguments:
        Parsed CLI arguments.

    Returns
    -------
    str | LiteLlm
        Model configuration accepted by ``LlmAgent``.
    """

    if arguments.provider == "gemini":
        if not os.getenv(_DEFAULT_GEMINI_API_ENV_VAR):
            raise RuntimeError(f"Missing required environment variable: {_DEFAULT_GEMINI_API_ENV_VAR}.")
        return arguments.model

    if not arguments.api_base:
        raise RuntimeError("--api-base is required for the lms provider.")

    api_key = arguments.api_key
    if api_key is None:
        api_key = "not-used"

    return LiteLlm(
        model=arguments.model,
        api_base=_normalize_openai_compatible_api_base(arguments.api_base),
        api_key=api_key,
    )


def _build_prompt(label: str, session: SegmentationSession) -> str:
    """Build the single user prompt used to drive the segmentation run.

    Parameters
    ----------
    label:
        Story label under the database directory.
    session:
        Filesystem-backed segmentation session.

    Returns
    -------
    str
        Initial user prompt sent to the agent.
    """

    return (
        f"Segment the story stored for label '{label}'. "
        f"The source story is at '{session.story_path}'. "
        f"The mutable draft is at '{session.draft_path}'. "
        f"The final export target is '{session.export_path}'. "
        "Inspect the story and current draft with tools, build or refine the segmentation, "
        "validate prompt consistency, export the final storybook, and then summarize the result."
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


def _normalize_openai_compatible_api_base(api_base: str) -> str:
    """Normalize an LM Studio API base URL.

    Parameters
    ----------
    api_base:
        User-provided LM Studio API base URL.

    Returns
    -------
    str
        API base URL ending with ``/v1``.
    """

    normalized_api_base = api_base.rstrip("/")
    if normalized_api_base.endswith("/v1"):
        return normalized_api_base
    return f"{normalized_api_base}/v1"


async def _run() -> int:
    """Run the segmentation agent once and print its final response.

    Returns
    -------
    int
        Process exit status.
    """

    arguments = _parse_arguments()
    session = _prepare_session(arguments)

    agent = LlmAgent(
        name="segment_story_agent",
        model=_build_model(arguments),
        instruction=_SEGMENTATION_AGENT_INSTRUCTION,
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
        },
    )
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=_build_prompt(arguments.label, session))],
    )

    final_text: str | None = None
    async for event in runner.run_async(
        user_id=arguments.user_id,
        session_id=adk_session.id,
        new_message=user_message,
    ):
        if not event.content or not event.content.parts:
            continue
        for part in event.content.parts:
            text = getattr(part, "text", None)
            if text:
                final_text = text

    if final_text is not None:
        print(final_text)
    elif session.export_path.exists():
        print(f"Exported storybook to {session.export_path}.")
    else:
        raise RuntimeError("The agent finished without exporting a storybook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
