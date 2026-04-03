---
name: segment-story
description: Segment a source story into ordered scenes by choosing visually meaningful moments, preserving narrative flow, and writing scene texts. Use when Codex must create, refine, or validate the scene breakdown for an illustrated book; use separate skills for concept definition, prompt design, and illustration work.
---

Use this skill to create or revise the scene breakdown of a storybook.

This skill defines the structural work of segmentation:

- defining the canonical title and author,
- choosing the scene breakdown,
- preserving story coverage and narrative flow,
- writing scene texts,
- determining which non-scene book parts should be present,
- ensuring each scene corresponds to a clear illustratable moment.

This skill does **not** handle:

- concept identification or anchor definition (use the concept-definition skill),
- prompt writing for scenes or book parts (use the prompt-design skill),
- style, constraints, or illustration generation (use artwork-generation and illustration-generation skills).

Use the repository's authoritative schema, storage rules, and validators for artifact structure and compliance.

Do not treat this skill as the source of truth for JSON shape, file layout, or generation parameters.

Workflow
--------

1. Read the full story carefully.
2. Locate the current story workspace and inspect any existing segmentation artifacts.
3. Determine whether the current segmentation should be created, kept, or revised.
4. Define or refine the canonical title and author for the book.
5. Determine which non-scene book parts should be present in the current storybook draft.
6. Split the story into scenes while preserving narrative flow, story coverage, and visual clarity.
7. Ensure that each scene captures a distinct and illustratable moment.
8. Write each scene text in the language of the story.
9. Leave prompt and image_path fields empty for scenes; those are filled by downstream skills.
10. Run the relevant repository validators and consistency checks.
11. Repair weak or invalid segmentation state before declaring the work complete.

Scene Texts
-----------

Scene texts should:

* preserve the story flow,
* cover the story at an appropriate granularity,
* remain close to the original writing when possible,
* stay in the original story language.

Scene Labels
------------

Scene labels should:

* be unique across the storybook,
* follow a stable naming convention,
* remain meaningful enough to identify the scene outside the storybook context.

Output Validation Rules
-----------------------

Before declaring the segmentation complete, verify through repository tools and validators that:

* the canonical segmentation artifact respects the repository schema,
* scene labels are unique and stable,
* scene texts are written in the story language,
* scene order preserves the narrative flow,
* the story is covered without major omissions,
* scenes are distinct enough to avoid obvious redundancy,
* the resulting segmentation is suitable for downstream concept and illustration work.

Completion
----------

The work is complete only when the segmentation is both semantically satisfactory and structurally validated.

If a storage-management skill exists, use it for file placement and naming.

