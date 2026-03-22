# AGENTS.md

## Repository overview

This repo contains an embryon of a CLI tool helping users convert natural language stories into illustrated books with the help of AI-powered agents.

The project is in early stages, and the code is expected to be rough and evolving.

Structure:

- `./.agents/`: skills definitions,
- `./database/`: default folder for storing cli-content, splitted per stories (e.g., `./database/my-story/`), not followed by git,
- `./librito/`: main library code,
- `./docs/`: user-facing documentation (sphinx-based),
- `./helpers/`: helper scripts providing useful utilities for story conversion, usable both by users & coding agents,
- `./tests/`: test suite.

## Core rules

- Prefer the smallest safe diff that solves the stated problem.
- Keep one concern per change.
- Do not mix bug fixes, refactors, style churn, and new features in the same change.
- Preserve existing architecture and conventions unless the task explicitly requires a change.
- Prefer editing existing code over introducing new abstraction layers.
- Prefer deletion over addition, and addition over new dependencies.
- Do not "optimize everything". Performance work needs either an explicit request or evidence of a real bottleneck.

## Human in the loop

- For any non-trivial task, briefly state:
  - the intent,
  - the files or areas likely to change,
  - the validation plan.
- Stop and ask for approval before applying modifications to the codebase, unless the task is trivial and self-contained (e.g., fixing a typo in a docstring, or adding a missing type hint).
- Do not create commits, tags, releases, or upstream pull requests unless explicitly asked.

### Coding style

- All source code, identifiers, comments, and docstrings must be written in English.
- User-facing documentation may be written in another language when appropriate.
- All functions, methods, classes, and modules must be documented.
- Use numpydoc-style docstrings.
- Type hints are required for function and method parameters, as well as return values.
- Type hints for global variables are optional but recommended.

## GenAI API safety

- API keys must exclusively be fetched from environment variables. No hardcoded keys, no API keys in parameters nor config files, no secrets in test fixtures or notebooks.
- If existing, the `.env` file in the repository root contains the necessary variables. Load it with `source .env` or a similar mechanism (if in Powershell) if needed.
- Use mock responses for testing and development, and avoir real paid or network-dependent API calls in such cases, unless explicitely requested.