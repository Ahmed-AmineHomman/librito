---
name: illustration-definition
description: Define and refine the illustration-facing layer of a storybook, including scene prompts, global style, optional custom constraints, and expanded-prompt consistency. Use when Codex must improve how scenes are expressed for image generation after segmentation has already established the story structure.
---

Use this skill to create or revise the illustration-definition layer of a storybook.

This skill defines the generation-facing work:

- choosing or refining one global visual style,
- writing or revising scene prompts,
- deciding whether custom constraints are needed,
- checking prompt consistency once anchors are expanded,
- improving prompt clarity for downstream image generation.

Use the repository's authoritative models, prompt-building code, and validators for artifact structure and compliance.

Do not treat this skill as the source of truth for file layout, JSON shape, or segmentation policy.

Workflow
--------

1. Read the current storybook and inspect the existing prompts, style, constraints, and anchors.
2. Determine whether the illustration-definition state should be created, kept, or revised.
3. Define or refine one global visual style that can apply coherently across the whole story.
4. Rewrite scene prompts so they faithfully express the intent of each scene without changing the segmentation.
5. Reuse recurring anchors where they improve consistency across scenes.
6. Check the prompts after anchor expansion and revise them until they remain self-contained, visually coherent, and faithful to the scene intent.
7. Keep custom constraints empty unless the story or the user requires generation rules beyond the repository defaults.
8. If custom constraints are needed, write only the additional constraints that materially improve generation quality or safety.
9. Run the relevant repository validators and consistency checks.
10. Repair weak or invalid illustration-definition state before declaring the work complete.

Style
-----

The global style should define a coherent visual direction for the whole story.

- Keep it stable across scenes.
- Make it specific enough to guide image generation.
- Do not use style to encode scene-specific actions or story events.
- Prefer one strong visual direction over a vague list of aesthetics.

Constraints
-----------

Constraints are optional.

The repository already provides default generation constraints. Therefore:

- leave custom constraints empty when the defaults are sufficient,
- add custom constraints only when they are clearly needed,
- avoid repeating default intent unless the repository standard explicitly requires it,
- do not use constraints to compensate for weak scene prompts when the prompt itself should be improved.

Prompt Definition
-----------------

Scene prompts should:

- remain faithful to the associated scene,
- describe the main visual moment clearly,
- use recurring anchors when those anchors improve cross-scene consistency,
- stay understandable once anchors are expanded,
- avoid relying on hidden context outside the storybook artifact.

Expanded-Prompt Consistency
---------------------------

Anchor expansion is part of the real generation path.

Therefore, evaluate prompts not only in their compressed form, but also in their expanded form.

After expansion, prompts should:

- remain self-contained,
- preserve visual consistency for recurring concepts,
- avoid contradiction between anchor descriptions and inline wording,
- avoid accidental duplication of the same concept description,
- remain readable enough for image-generation models.

Validation Expectations
-----------------------

Before declaring illustration definition complete, verify through repository tools and validators that:

- the canonical storybook artifact respects the repository schema,
- prompts remain aligned with their associated scenes,
- the global style is coherent across the story,
- custom constraints are used only when needed,
- all anchors used in prompts are defined,
- expanded prompts remain consistent and usable for generation.

Completion
----------

The work is complete only when the illustration definition is both semantically faithful and structurally validated.

If a storage-management skill exists, use it for file placement and naming.
