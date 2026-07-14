# AGENTS.md

This repository is an agent-native workspace for transforming stories into structured, illustrated storybooks.

The coding agent is expected to perform the necessary operation for the above transformation, using the repository
itself as a modular system:

- these instructions for the global core logic;
- skills for task-specific instructions;
- helper scripts for deterministic operations.

Follow this principle throughout the repository:

- Agents handle semantic and judgment-based work.
- Scripts handle strict, deterministic, and reproducible work.

Note: the agent can also be required by the user to work on the codebase, like in the standard workflow for coding
agents. Corresponding instructions are given below.

## General Workflow

When requested to perform a non-trivial operation, follow the general workflow below:

1. State your understanding of the problem, the plan you intend to follow, the areas likely to change, and the
   validation plan;
2. Wait for the user approval;
3. Apply planned modifications & validations;
4. If applicable, check that code (or whatever you produced) compiles (no automated testing needed);
5. Explain what you did to the user;
6. If user requests changes, go back to step 3. if changes are trivial and step 1. if they are not.

## Scope & Responsibilities

- Do not create commits, tags, releases, or pull requests unless explicitly asked.
- Rely on the user for configuring the working environment (deps, virtual env, API keys, etc...).
- Never edit nor look at environment files (`./.env`).

## Repository Overview

- `./.agents/`: skills and agent-oriented guidance;
- `./database/`: working area for stories and generated artifacts;
- `./librito/`: reusable source code, schema definitions, workspace structure, etc...;
- `./docs/`: user-facing documentation;
- `./helpers/`: deterministic helper scripts;
- `./.venv/`: python virtual environment associated with the project;
- `./.env`: configuration file containing API keys & other environment variables.

## Coding Principles

- Keep it Simple, Stupid and Boring;
- Prefer clear code over clever code;
- Documentation:
    - numpydoc docstrings for all public methods & classes,
    - ReST files for user-facing docs,
    - class constructors are documented in class docstring,
    - modules also have their own docstring;
- Language: english everywhere.
- Formatting:
    - one parameter per line in method signatures,
    - type hints for method parameters, module & class variables;
- No automated testing.

## Environment Variables

All environment variables are defined in a `.env` file at the root of the repo. Always satisfy the conditions below when
dealing with environment variables:

- Do not read nor edit the `.env` file, never;
- At the beginning of the session, ensure that all variables contained in `.env` are loaded in the sandbox.