---
name: segment-story
description: Segment a source story into the repository's canonical storybook artifact by choosing visually meaningful scenes, preserving narrative flow, and defining consistent anchors. Use when Codex must create, refine, or validate the story structure for an illustrated book inside the workspace; use a separate skill for detailed prompt, style, or constraint work.
---

Use this skill to create or revise the segmentation layer of a storybook for illustrated-book generation.

This skill defines the semantic work of segmentation:

- defining the canonical title and author,
- choosing the scene breakdown,
- preserving story coverage,
- preserving the story flow,
- defining visual anchors,
- writing scene texts,
- ensuring each scene corresponds to a clear illustratable moment.

Use the repository's authoritative schema, storage rules, and validators for artifact structure and compliance.

Do not treat this skill as the source of truth for JSON shape, file layout, or generation parameters.

Workflow
--------

1. Read the full story carefully.
2. Locate the current story workspace and inspect any existing segmentation artifacts.
3. Determine whether the current segmentation should be created, kept, or revised.
4. Define or refine the canonical title and author for the book.
5. Determine which non-scene book parts should be present in the current storybook draft.
6. Identify visual concepts in the story:
   * characters,
   * important settings,
   * important recurring objects.
7. Split the story into scenes while preserving narrative flow, story coverage, and visual clarity.
8. Ensure that each scene captures a distinct and illustratable moment.
9. Write each scene text in the language of the story.
10. Define concept anchors only for concepts that appear in more than one scene.
11. If the canonical artifact includes prompt fields outside scenes, keep them structurally aligned with the intended book part, but leave detailed prompt optimization to a dedicated prompting skill.
12. Run the relevant repository validators and consistency checks.
13. Repair weak or invalid segmentation state before declaring the work complete.

Anchor Definition
-----------------

Concepts are stored as anchor mappings from canonical tags to stable visual descriptions.

Anchor tags must use the strict format ``<NAME>`` with uppercase letters,
digits, and underscores only.

Prompts should use anchors whenever a story concept appears in more than one
scene. One-scene details should stay inline.

Scene Texts
-----------

Scene texts should:

* preserve the story flow,
* cover the story at an appropriate granularity,
* remain close to the original writing when possible,
* stay in the original story language.

Scene Prompts
-------------

Scene prompts should:

* remain faithful to the scene intent,
* preserve anchor usage when anchors are relevant,
* stay usable for downstream illustration work,
* are written in english.

Prompt wording refinement, style definition, and constraint tuning belong to a separate prompting or illustration-preparation skill.

Output Validation Rules
-----------------------

Before declaring the segmentation complete, verify through repository tools and validators that:

* the canonical segmentation artifact respects the repository schema,
* scene labels are unique and stable,
* scene texts are written in the story language,
* scene prompts are written in english,
* scene order preserves the narrative flow,
* the story is covered without major omissions,
* scenes are distinct enough to avoid obvious redundancy,
* all anchors used in prompts are defined,
* unused concepts are removed,
* anchors used in only one scene are removed or inlined,
* the resulting segmentation is suitable for downstream illustration generation.

Completion
----------

The work is complete only when the segmentation is both semantically satisfactory and structurally validated.

If a storage-management skill exists, use it for file placement and naming.

