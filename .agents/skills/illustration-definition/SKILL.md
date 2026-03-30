---
name: illustration-definition
description: Define and refine the illustration-facing layer of a storybook, including scene prompts, global style, optional custom constraints, and resolved prompt consistency. Use when Codex must improve how scenes are expressed for image generation after segmentation has already established the story structure.
---

Use this skill to create or revise the illustration-definition layer of a storybook.

This skill defines the generation-facing work:

- choosing or refining one global visual style,
- writing or revising prompts for scene and non-scene illustrated book parts,
- deciding whether custom constraints are needed,
- checking prompt consistency once anchors are resolved,
- improving prompt clarity for downstream image generation.

Use the repository's authoritative models, prompt-building code, and validators for artifact structure and compliance.

Do not treat this skill as the source of truth for file layout, JSON shape, or segmentation policy.

Workflow
--------

1. Read the current storybook and inspect the existing prompts, style, constraints, book parts, and anchors.
2. Determine whether the illustration-definition state should be created, kept, or revised.
3. Define or refine one global visual style that can apply coherently across the whole story.
4. Rewrite scene prompts so they faithfully express the intent of each scene without changing the segmentation.
5. Define or refine prompts for any illustrated non-scene book parts that are present in the schema.
6. Reuse anchors where they improve consistency across scenes and book parts.
7. Check the prompts after anchor expansion and revise them until they remain self-contained, visually coherent, and faithful to the intended page function.
8. Keep custom constraints empty unless the story or the user requires generation rules beyond the repository defaults.
9. If custom constraints are needed, write only the additional constraints that materially improve generation quality or safety.
10. Run the relevant repository validators and consistency checks.
11. Repair weak or invalid illustration-definition state before declaring the work complete.

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
- use anchors when they improve cross-scene consistency,
- stay understandable once anchors are expanded,
- avoid relying on hidden context outside the storybook artifact.

Book-Part Prompt Guidance
-------------------------

Front cover
~~~~~~~~~~~

- The cover should support title and author legibility.
- When ``text_mode`` is ``overlay``, assume the assembler will add the title and author.
- When ``text_mode`` is ``embedded``, assume the image itself already contains them.
- The image should either depict the most iconic story moment or combine the book's main concepts into a cover-specific composition.

Front endpaper and frontispiece
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- These illustrations should usually feel contemplative and uncluttered.
- Favor a strong setting, object, or quiet character focus over a busy narrative scene.
- In most books, prefer making only one of these two pages visually prominent to avoid crowding the opening.

Title page
~~~~~~~~~~

- The title page receives the canonical title and author during assembly.
- Any optional title-page illustration should stay small, simple, and secondary to the typography.
- Prefer one iconic concept rather than a complex action scene.

Closing illustration
~~~~~~~~~~~~~~~~~~~~

- The closing illustration may acknowledge the resolved end state of the story.
- Unlike the opening images, it may safely allude to the ending.
- Keep the composition calm enough to feel like an ending image rather than another action spread.

Back cover
~~~~~~~~~~

- The back cover always carries a teaser.
- When ``text_mode`` is ``overlay``, assume the assembler will place the teaser over the full-page image.
- When ``text_mode`` is ``embedded``, assume the teaser is already present inside the image.
- The back-cover image should leave room for teaser legibility when overlay mode is used.

Resolved-Prompt Consistency
---------------------------

Anchor expansion is part of the real generation path.

Therefore, evaluate prompts not only in their compressed form, but also in their resolved form.

After resolution, prompts should:

- remain self-contained,
- preserve visual consistency for concepts,
- preserve the intended function of each page,
- avoid contradiction between anchor descriptions and inline wording,
- avoid accidental duplication of the same concept description,
- remain readable enough for image-generation models.

Validation Expectations
-----------------------

Before declaring illustration definition complete, verify through repository tools and validators that:

- the canonical storybook artifact respects the repository schema,
- prompts remain aligned with their associated scenes or book parts,
- the global style is coherent across the story,
- custom constraints are used only when needed,
- all anchors used in prompts are defined,
- resolved prompts remain consistent and usable for generation.

Completion
----------

The work is complete only when the illustration definition is both semantically faithful and structurally validated.

If a storage-management skill exists, use it for file placement and naming.

