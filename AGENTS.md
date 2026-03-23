# AGENTS.md

This repo aims to be an app (either CLI or GUI) helping users convert natural language stories into illustrated books with the help of AI-powered agents.

The project is in its early stages, and the code is expected to be rough and evolving. In particular, many structuring decisions have not yet been made (choice between CLI or GUI, API support, etc...). While a stable version has not been reached, aim for simple code without too elaborated scaffolding.

## Repository overview

- `./.agents/`: skills definitions (editable if requested),
- `./database/`: default app working folder,
- `./librito/`: main source code,
- `./docs/`: user-facing documentation (sphinx-based),
- `./helpers/`: helper scripts providing useful utilities for story conversion, usable both by users & coding agents,
- `./tests/`: test suite (unittest).

## Core rules

- Prefer clear to clever code.
- Preserve existing architecture and conventions unless the task explicitly requires a change.
- Aim for the simplest scaffolding: linear code is OK as long as there is no code duplication.

### Human in the loop

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

### API Management

- API-related data (urls, keys, tokens, etc.) must **exclusively be fetched from environment variables**. This means that code should not pass such variables as parameters whatsoever.
- Providing the necessary environment variables is the **responsibility of the user**. Code should assume that they are already defined and available, and raise gracefully if not.
- If existing, the `.env` file in the repository root contains the necessary variables. You can source it for debugging and test purposes when relevant.
- Use mock responses for testing and development, and avoir real paid or network-dependent API calls in such cases, unless explicitly requested.