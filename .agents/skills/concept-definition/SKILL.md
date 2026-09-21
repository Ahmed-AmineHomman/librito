---
name: concept-definition
description: Identify recurring visual concepts in a segmented story, define canonical anchor tags with stable descriptions, and map each concept to the scenes where it appears. Use when Codex must create, refine, or validate the concept layer after segmentation and before artwork generation or prompt design.
---

Use this skill to create or revise the concept layer of a storybook.

This skill defines the semantic work of concept identification:

- identifying recurring visual concepts (characters, settings, objects),
- defining canonical anchor tags,
- writing stable visual descriptions for each concept,
- mapping each concept to the scenes where it appears,
- ensuring concepts are reusable across multiple scenes.

This skill does **not** handle:

- scene breakdown or scene texts (use the segment-story skill),
- artwork generation or style definition (use the artwork-generation skill),
- prompt writing (use the prompt-design skill),
- illustration generation (use the illustration-generation skill).

Use the repository's authoritative schema, storage rules, and validators for artifact structure and compliance.

Workflow
--------

1. Read the segmented storybook and its scene texts carefully.
2. Inspect any existing concept definitions.
3. Determine whether the concept layer should be created, kept, or revised.
4. Identify visual concepts that recur across multiple scenes:
   * characters (appearance, clothing, distinguishing features),
   * important settings (locations, environments),
   * important recurring objects (artifacts, vehicles, tools).
5. Classify each concept as a subject (`is_environment: false`) or an environment (`is_environment: true`).
6. Assign each concept a canonical anchor tag in the strict ``<UPPER_SNAKE>`` format.
7. Write a stable visual description for each concept that is specific enough to guide consistent illustration across scenes.
8. Map each concept to the ordered list of scene labels where it appears.
9. Remove concepts that appear in only one scene; those details belong inline in the scene prompt.
10. Run the relevant repository validators and consistency checks.
11. Repair weak or invalid concept state before declaring the work complete.

Anchor Tags
-----------

Anchor tags must use the strict format ``<NAME>`` with uppercase letters, digits, and underscores only.

Tags should be short, mnemonic, and stable across revisions. Avoid generic names like ``<CHARACTER>`` when a specific name like ``<CALMIO>`` is available.

Concept Classification
----------------------

Each concept must be categorized by setting its boolean `is_environment` field:

* **Subject concepts** (`is_environment: false`): characters, animals, vehicles, and objects. Downstream artwork generation renders these as isolated reference images on a neutral background using subject constraints.
* **Environment concepts** (`is_environment: true`): rooms, houses, landscapes, clearings, and locations. Downstream artwork generation renders these as spatial setting references without characters using environment constraints.

Concept Descriptions
--------------------

Descriptions should:

* be written in English,
* focus on visual appearance rather than narrative role,
* be specific enough to produce consistent imagery across scenes,
* avoid scene-specific actions or transient states,
* remain stable across the full story.

A good description reads like an instruction to an illustrator who must draw the same concept repeatedly.

Scene Mapping
-------------

Each concept must list the scene labels where it visually appears.

The mapping serves two purposes:

* it documents which scenes share visual elements,
* it enables downstream artwork and prompt tools to verify concept coverage.

A concept should be mapped to a scene only when it is visually present, not merely mentioned in narration.

Output Validation Rules
-----------------------

Before declaring concept definition complete, verify through repository tools and validators that:

* the canonical storybook artifact respects the repository schema,
* every concept has a unique and valid anchor tag,
* every concept specifies the `is_environment` boolean flag,
* every concept has a non-empty description,
* every concept is mapped to at least two scenes,
* no concept appears in only one scene (inline those instead),
* scene labels in concept mappings refer to existing scenes,
* descriptions are specific enough to be visually useful.

Completion
----------

The work is complete only when the concept layer is both semantically faithful and structurally validated.

If a storage-management skill exists, use it for file placement and naming.
