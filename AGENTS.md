# AGENTS.md

## Purpose

This repository is an agent-native workspace for transforming stories into structured, illustrated storybooks.

It is designed to be used with coding agents. The repository itself provides the operating environment:

- skills define how to perform specific tasks,
- helper scripts perform deterministic checks and transformations,
- `database/` stores source material, intermediate artifacts, generated outputs, and evaluation results.

This repository is not primarily a traditional end-user app. Its main runtime is an agent working inside the repo.

Note: the agent can also be required by the user to work on the codebase, like in the standard workflow for coding agents. Corresponding instructions are given below.

## Operating Principle

Use the repository as a modular system.

- Use `AGENTS.md` for the global logic of the repository.
- Use skills for task-specific instructions.
- Use helper scripts for deterministic operations.
- Use documented artifact formats and storage conventions so outputs remain inspectable and reusable.

Do not place detailed task procedures in this file when they belong in a skill or script interface.

## Agent Role

The agent is expected to orchestrate the workflow end-to-end.

This includes:

- understanding the user request,
- selecting the relevant skills,
- producing the required artifacts,
- running the appropriate helper scripts,
- interpreting validation results,
- iterating when needed.

The agent should rely on existing skills and scripts whenever available rather than improvising the workflow from
scratch.

## Responsibility Split

Follow this principle throughout the repository:

- Agents handle semantic and judgment-based work.
- Scripts handle strict, deterministic, and reproducible work.

In practice:

- segmentation, prompt writing, arbitration, and revision belong to the agent,
- validation, scoring, storage setup, format checks, and consistency checks belong to code.

## Repository Areas

- `./.agents/`: skills and agent-oriented guidance
- `./database/`: working area for stories and generated artifacts
- `./librito/`: reusable source code
- `./docs/`: documentation
- `./helpers/`: deterministic helper scripts
- `./tests/`: automated tests (NOT CURRENTLY USED)

## Core Constraints

- Prefer clear code over clever code.
- Keep scaffolding simple unless stronger structure is required.
- Preserve existing architecture unless a change is necessary.
- All source code, identifiers, comments, and docstrings must be written in English.
- All functions, methods, classes, and modules must be documented.
- Use numpydoc-style docstrings.
- Type hints are required for function and method parameters and return values.
- Refrain from creating tests: scope and maturity of the solution do not justify testing yet.

## API Rules

- API-related configuration must be read from environment variables only.
- Do not hardcode API keys, tokens, or endpoints.
- Use mocks in tests and development whenever possible.
- Avoid real paid or network-dependent API calls in tests unless explicitly requested.

## Human in the Loop

For non-trivial code changes, briefly state:

- the intent,
- the areas likely to change,
- the validation plan.

Ask for approval before applying non-trivial modifications, unless the task is clearly small and self-contained.

Do not create commits, tags, releases, or pull requests unless explicitly asked.
