---
name: artwork-generation
description: Define the global visual style and generate reference artworks for each recurring concept to ground visual consistency. Use when Codex must create or refine the style direction and produce concept artworks (image anchors) after concept definition and before prompt design.
---

Use this skill to define the visual style and generate reference artworks for a storybook.

This skill defines the creative work of visual grounding:

- choosing or refining one global visual style,
- generating one reference artwork per recurring concept,
- ensuring artworks faithfully represent their concept descriptions in the chosen style.

The purpose of artworks is to ground abstract concept descriptions into concrete images. These images serve as **image anchors** for downstream illustration generation, providing the image generator with visual references rather than relying solely on textual descriptions. This produces more accurate and consistent representations of concepts across scenes.

This skill does **not** handle:

- scene breakdown or scene texts (use the segment-story skill),
- concept identification or anchor definition (use the concept-definition skill),
- scene prompt writing (use the prompt-design skill),
- final illustration generation (use the illustration-generation skill).

Use the repository's authoritative schema, storage rules, and validators for artifact structure and compliance.

Workflow
--------

1. Read the segmented storybook, its concepts, and their descriptions.
2. Inspect any existing style definition and artworks.
3. Determine whether the style and artworks should be created, kept, or revised.
4. Define or refine one global visual style that can apply coherently across the whole story.
5. For each concept, generate a reference artwork that represents it faithfully in the chosen style.
6. Store artworks in the canonical artworks directory of the story workspace.
7. Record artwork paths in the storybook artifact (concept image paths).
8. Review generated artworks for visual quality and consistency with descriptions.
9. Regenerate or refine artworks that do not meet quality expectations.
10. Run the relevant repository validators and consistency checks.
11. Repair weak or invalid artwork state before declaring the work complete.

Style
-----

The global style should define a coherent visual direction for the whole story.

- Keep it stable across scenes and concepts.
- Make it specific enough to guide image generation.
- Do not use style to encode scene-specific actions or story events.
- Prefer one strong visual direction over a vague list of aesthetics.

Artworks
--------

Concept artworks are a **mandatory preliminary step** before scene illustration. The illustration pipeline enforces that all concepts referenced in a scene prompt possess generated reference artworks on disk.

Use the `helpers/illustrate_artworks.py` script to generate concept artworks deterministically. The helper supports separate constraint overrides via `--subject-constraints` and `--environment-constraints`.

Each concept artwork should:

* faithfully represent the concept description,
* be rendered in the global visual style,
* adhere to its concept category:
  * **subject concepts**: isolated on a clean neutral background using subject constraints,
  * **environment concepts**: depicting the spatial layout, architectural/natural features, and atmosphere without characters using environment constraints,
* be suitable as a visual reference for an image generator.

Artworks are stored in the story workspace under the canonical artworks directory (`database/<story>/artworks/`). The storybook artifact records relative paths to each artwork.

Output Validation Rules
-----------------------

Before declaring artwork generation complete, verify through repository tools and validators that:

* the canonical storybook artifact respects the repository schema,
* the global style is defined and non-empty,
* every concept has a reference artwork at its recorded path,
* artwork paths are valid relative paths within the story workspace,
* the visual style is coherent across the generated artworks.

Completion
----------

The work is complete only when the style is defined and all concept artworks are generated, reviewed, and structurally validated.

If a storage-management skill exists, use it for file placement and naming.
