# AGENTS.md

This repository is an agent-native workspace for transforming stories into structured, illustrated storybooks.

The coding agent is expected to perform the necessary operation for the above transformation, using the repository itself as a modular system:

- these instructions for the global core logic;
- skills for task-specific instructions;
- helper scripts for deterministic operations.
- 
Follow this principle throughout the repository:

- Agents handle semantic and judgment-based work.
- Scripts handle strict, deterministic, and reproducible work.

Note: the agent can also be required by the user to work on the codebase, like in the standard workflow for coding agents. Corresponding instructions are given below.

## General Workflow

When requested to perform a non-trivial operation, follow the general workflow below:

- State your understanding of the problem, the plan you intend to follow, the areas likely to change, and the validation plan.
- Request user approval interactively (without yielding control back).
- Apply planned modifications & validations.
- Yield control back to the user when finished.

Do not create commits, tags, releases, or pull requests unless explicitly asked.
Rely on the user for configuring the working environment (deps, virtual env, API keys, etc...).

## Repository Overview

- `./.agents/`: skills and agent-oriented guidance
- `./database/`: working area for stories and generated artifacts
- `./librito/`: reusable source code, schema definitions, workspace structure, etc..
- `./docs/`: user-facing documentation
- `./helpers/`: deterministic helper scripts
- `./tests/`: automated tests (NOT CURRENTLY USED)

## Coding Principles

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
- `./.env` should contain the environment variables needed by local helpers, and helper scripts load it automatically at startup.
- Never inspect `./.env` directly. If something goes wrong with environment variables, ask the user to provide or correct the necessary information.
- Do not hardcode API keys, tokens, or endpoints.
- Use mocks in tests and development whenever possible.
- Avoid real paid or network-dependent API calls in tests unless explicitly requested.
