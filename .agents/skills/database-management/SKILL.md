---
name: database-management
description: Manage story workspaces inside `./database/` using the repository's strict label-based storage convention. Use when Codex must create, locate, read, or update story artifacts by label, initialize a new story workspace, or store outputs so helper scripts can discover them reliably.
---

# Database Management

Use this skill to manage story artifacts in `./database/`.

## Core Rule

Each story is identified by a unique label.

All artifacts for a story must live inside:

`./database/<label>/`

Use strict filenames so helper scripts can resolve artifacts from the label alone.

## Canonical Layout

For a story labeled `<label>`, the canonical workspace is:

- `./database/<label>/story.md`
- `./database/<label>/story.json`
- `./database/<label>/units.json`
- `./database/<label>/story.epub`
- `./database/<label>/illustrations/`
- `./database/<label>/artworks/`

Interpret these paths as follows:

- `story.md`: full source story
- `story.json`: storybook / segmentation artifact
- `units.json`: units artifact
- `story.epub`: assembled book
- `illustrations/`: generated scene and book-part illustrations
- `artworks/`: concept reference artworks and style reference artwork

Do not invent alternate filenames for these canonical artifacts.

## Operating Instructions

When asked to work on a story:

1. Resolve the story label.
2. Locate or create `./database/<label>/`.
3. Read or write artifacts using the canonical filenames only.
4. Store every generated artifact inside the story folder unless another skill or script explicitly requires otherwise.

When initializing a new story workspace:

1. Ensure the label is unique.
2. Create `./database/<label>/`.
3. Create or place the relevant canonical files there.
4. Create `./database/<label>/illustrations/` when illustration outputs are expected or required by the workflow.
5. Create `./database/<label>/artworks/` when artwork outputs are expected or required by the workflow.

## Naming Discipline

Treat the naming convention as strict.

- Do not rename canonical files.
- Do not store the main storybook JSON under another filename.
- Do not store evaluation units outside `units.json`.
- Do not store the main book outside `story.epub`.
- Do not place story illustrations outside `illustrations/` unless another tool explicitly requires a temporary
  location.
- Do not place concept or style artworks outside `artworks/` unless another tool explicitly requires a temporary
  location.

Additional files may exist in the story folder, but they must not replace or shadow the canonical artifacts.

## Helper Compatibility

Assume helper scripts resolve story artifacts by label and canonical filename.

Therefore:

- prefer label-based access over manual path improvisation,
- keep canonical files present and up to date,
- and preserve this layout unless the repository conventions are explicitly changed.

## Artifact Contract

Respect the repository's authoritative schema and artifact definitions for canonical files such as `story.json` and
`units.json`.

Use this skill to determine where artifacts must live and how they must be named.

Use the repository's schema definitions and validators to determine what those artifacts must contain.

