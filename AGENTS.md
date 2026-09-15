# AGENTS.md

This repository is an agent-native workspace for transforming stories into structured, illustrated storybooks.

## Repository Overview

- `./.agents/`: skills and agent-oriented guidance;
- `./database/`: working area for stories and generated artifacts;
- `./librito/`: reusable source code, schema definitions, workspace structure, etc...;
- `./helpers/`: deterministic helper scripts;
- ` ./docs/`: user-facing documentation.

### API keys

The `./.env` file contains the necessary API keys to perform some operations supported by the codebase.
The code should look into the following environment variables when relevant:

- `GEMINI_API_KEY`: API key for the Gemini API.

## CI

This solution has no test suite. It has however GitHub Action scripts that run in the following cases:

- when a PR proposes modification to the `main` branch;
- when committing to the `main` branch.

The CI consists in the following scripts:

- `docs`: builds & publish the documentation.

## Documentation

The user-facing documentation (usually referred to as "documentation") lives in `./docs/`. It is written in French and helps users understand the solution. It is built with `sphinx`, using the `furo` theme.

The documentation is not here to give an understanding of the API. It is targeted at repo users only, and should onboard them in using the solution.

Do not update the documentation until explicitely asked by the developer.