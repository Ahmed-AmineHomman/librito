# AGENTS.md

This repository is an agent-native workspace for transforming stories into structured, illustrated storybooks.

## Repository Overview

- `./.agents/`: skills and agent-oriented guidance;
- `./database/`: working area for stories and generated artifacts;
- `./librito/`: reusable source code, schema definitions, workspace structure, etc...;
- `./helpers/`: deterministic helper scripts;

### API keys

The `./.env` file contains the necessary API keys to perform some operations supported by the codebase.
The code should look into the following environment variables when relevant:

- `GEMINI_API_KEY`: API key for the Gemini API.