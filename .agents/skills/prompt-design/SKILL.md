---
name: prompt-design
description: Design illustration prompts for scenes and book parts by describing what to represent and how concepts interact in each illustration. Use when Codex must create or refine scene prompts after concept definition and before illustration generation; this skill sets the stage without concern for the final rendering result.
---

Use this skill to create or revise the illustration prompts of a storybook.

This skill defines the creative work of illustration design:

- writing scene illustration prompts that describe what to represent,
- writing book-part illustration prompts (covers, endpapers, etc.),
- using concept anchors for cross-scene visual consistency,
- describing how concepts interact within each scene,
- ensuring prompts are faithful to the scene intent.

The role of prompt design is to **set the stage**: it specifies what should be illustrated in each scene, how concepts interact, and what visual moment to capture. It is not concerned with the final rendering quality or prompt engineering for the image generator. That work belongs to the illustration-generation skill.

This skill does **not** handle:

- scene breakdown or scene texts (use the segment-story skill),
- concept identification or anchor definition (use the concept-definition skill),
- style definition or artwork generation (use the artwork-generation skill),
- final prompt engineering, generation, or iteration (use the illustration-generation skill).

Use the repository's authoritative schema, storage rules, and validators for artifact structure and compliance.

Workflow
--------

1. Read the segmented storybook, its concepts, their descriptions, and any existing prompts.
2. Inspect any existing prompt definitions.
3. Determine whether the prompts should be created, kept, or revised.
4. For each scene, write an illustration prompt that:
   * describes the main visual moment to capture,
   * specifies how concepts interact in the scene,
   * uses concept anchor tags where they improve cross-scene consistency,
   * remains faithful to the scene text.
5. For each illustrated non-scene book part, write an illustration prompt appropriate to its function (see Book-Part Prompt Guidance below).
6. Reuse anchors where they improve consistency across scenes and book parts.
7. Check the prompts after anchor expansion and revise them until they remain self-contained, visually coherent, and faithful to the intended page function.
8. Run the relevant repository validators and consistency checks.
9. Repair weak or invalid prompt state before declaring the work complete.

Scene Prompts
-------------

Scene prompts should:

* describe what is visually happening in the scene,
* specify which concepts are present and how they interact,
* use anchor tags for recurring concepts,
* remain faithful to the associated scene text,
* be written in English,
* stay understandable once anchors are expanded,
* avoid relying on hidden context outside the storybook artifact.

Scene prompts should focus on **what to illustrate**, not on how to render it. Rendering details (prompt engineering, negative prompts, technical parameters) belong to the illustration-generation skill.

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

Anchor Usage
------------

Prompts should use concept anchor tags whenever a recurring concept appears in a scene or book part.

After expansion, prompts should:

- remain self-contained,
- preserve visual consistency for concepts,
- preserve the intended function of each page,
- avoid contradiction between anchor descriptions and inline wording,
- avoid accidental duplication of the same concept description,
- remain readable enough for downstream use.

Output Validation Rules
-----------------------

Before declaring prompt design complete, verify through repository tools and validators that:

* the canonical storybook artifact respects the repository schema,
* every scene has a non-empty prompt,
* prompts remain aligned with their associated scenes or book parts,
* all anchors used in prompts are defined as concepts,
* no defined concept is unused across all prompts,
* no concept anchor appears in only one prompt (inline those instead),
* resolved prompts remain consistent and usable.

Completion
----------

The work is complete only when the prompts are both semantically faithful and structurally validated.

If a storage-management skill exists, use it for file placement and naming.
