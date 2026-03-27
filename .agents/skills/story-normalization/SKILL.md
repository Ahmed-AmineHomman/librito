---
name: story-normalization
description: Normalize a source story into the repository's canonical evaluation-unit artifact while preserving story meaning, original ordering, and dialogue-turn structure. Use when Codex must create, refine, or validate normalized story units for semantic evaluation rather than perform segmentation or prompt optimization.
---

Use this skill to create or revise the normalization layer used for semantic evaluation.

This skill defines the semantic work of normalization:

- preserving the story content,
- preserving unit order,
- making unit boundaries stable across formatting variations,
- isolating dialogue turns from narration when appropriate,
- preparing the story for downstream evaluation.

Use the repository's authoritative models, I/O code, and validators for artifact structure and compliance.

Do not treat this skill as the source of truth for file layout or JSON shape.

Workflow
--------

1. Read the full story carefully.
2. Locate the current story workspace and inspect any existing normalization artifact.
3. Determine whether the current normalized state should be created, kept, or revised.
4. Split narration into ordered local units using the repository standard.
5. Normalize dialogue so that equivalent stories yield equivalent dialogue-turn units even when formatting differs.
6. Keep narration and dialogue units in source order.
7. Preserve the original wording as much as possible.
8. Normalize structure, not meaning.
9. Run the relevant repository validators and consistency checks.
10. Repair weak or invalid normalization state before declaring the work complete.

Normalization Principles
------------------------

The normalization should be conservative.

- Do not paraphrase unless the repository standard explicitly requires it.
- Do not reorder content.
- Do not omit content.
- Do not duplicate content.
- Prefer stable local boundaries over interpretation-heavy decomposition.

Dialogue Handling
-----------------

Dialogue formatting may vary across stories. The normalized result should remain robust to those formatting differences.

Target one dialogue turn per evaluation unit when the repository standard supports that interpretation.

Keep short nearby attribution with the dialogue turn when it clarifies speaker or tone without changing the story structure.

When several quoted sentences belong to the same turn, keep them together unless the repository standard requires a finer split.

Validation Expectations
-----------------------

Before declaring normalization complete, verify through repository tools and validators that:

- the canonical normalization artifact respects the repository schema,
- units are ordered and non-empty,
- unit labels are unique and stable,
- the normalized content covers the whole story without major omission,
- the normalized content does not introduce obvious duplication,
- the normalized wording remains close to the source story.

Completion
----------

The work is complete only when the normalization is both semantically faithful and structurally validated.

If a storage-management skill exists, use it for file placement and naming.
