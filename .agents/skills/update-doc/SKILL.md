---
name: update-doc
description: Guidance and instructions to follow when updating or writing user-facing documentation.
---

# Updating User-Facing Documentation

Use this skill when editing, adding, or revising user-facing documentation (e.g., files in `./docs/`). This skill does not apply to code docstrings.

## Reflect the Current State Only

User-facing documentation must always describe the solution in its current state. Do not track functionality history or mention previous implementations.

### Rationale

When a feature is modified or replaced, referencing the old behavior (e.g., *"we no longer do X, but Y"*) confuses new users. New users have no prior knowledge or access to "X", which no longer exists. Documentation is an operational reference for the current system, not a changelog or migration guide.

### Example

- **Incorrect:** *"We no longer use `--legacy-flag` to pass the story path; instead, pass the story label directly."*
- **Correct:** *"Pass the story label directly as an argument."*
