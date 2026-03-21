---
name: segment-story
description: Analyzes a story provided by the user, extracts recurring visual concepts, segments it into scenes, and generates a valid JSON object with story text and English image prompts. Use when ChatGPT must transform a user-provided story into the Librito segmented story standard while enforcing anchor consistency and valid JSON.
---

This skill explains how to transform a raw story into a segmented storybook for
illustrated-book generation.

The output is a JSON object containing:

* a title,
* a global illustration style,
* optional constraints,
* recurring concept anchors,
* an ordered list of scenes.

Each scene contains:

* a stable ``label``,
* a ``text`` field in the story language,
* a ``prompt`` field in English,
* an ``image_path`` field.

Workflow
--------

1. Read the full story carefully.
2. Identify the recurring visual concepts in the story:
   * characters,
   * important settings,
   * important recurring objects.
3. If the user does not provide one, choose a suitable illustration style in
   English.
4. Define recurring concept anchors for concepts that appear in more than one
   scene.
5. Split the story into scenes while preserving the narrative flow.
6. Write each scene text in the language of the story.
7. Write each scene prompt in English.
8. Verify prompt consistency:
   * all referenced anchors are defined,
   * unused anchors are removed,
   * anchors used in exactly one scene are removed or inlined.
9. Return valid JSON matching the expected schema.

Style and Anchor Definition
---------------------------

The ``style`` field is a single English description of the illustration style.
It is automatically prefixed to all prompts during illustration generation.

The ``constraints`` field should remain empty by default. Only populate it when
the user or story requires additional generation constraints.

Recurring concepts are stored in ``recurring_concepts`` as anchor mappings:

* ``<CONCEPT_NAME>``: stable visual description of the concept.

Anchor tags must use the strict format ``<NAME>`` with uppercase letters,
digits, and underscores only.

Prompts should use anchors whenever a story concept appears in more than one
scene. One-scene details should stay inline.

Scene Texts
-----------

Scene texts should:

* preserve the story flow,
* remain close to the original writing when possible,
* stay in the original story language.

Scene Prompts
-------------

Scene prompts should:

* be written in English,
* represent the main visual moment of the scene,
* use recurring concept anchors when appropriate,
* remain understandable once anchors are expanded.

Expected JSON Output
--------------------

The output must be a valid JSON object with exactly this structure:

{
  "title": "Story title",
  "style": "Artistic style in English",
  "constraints": "",
  "recurring_concepts": {
    "<CONCEPT_NAME>": "Detailed concept description"
  },
  "scenes": [
    {
      "label": "scene-find-car",
      "text": "Scene text in the language of the story",
      "prompt": "Scene illustration prompt in English",
      "image_path": ""
    }
  ]
}

Output Validation Rules
-----------------------

Before returning the final answer, verify:

* the top-level value is a JSON object,
* the object contains exactly ``title``, ``style``, ``constraints``,
  ``recurring_concepts``, and ``scenes``,
* ``title``, ``style``, and ``constraints`` are strings,
* ``recurring_concepts`` is an object mapping anchor tags to strings,
* ``scenes`` is an array,
* each scene contains exactly ``label``, ``text``, ``prompt``, and
  ``image_path``,
* scene labels are unique non-empty strings,
* prompts are written in English,
* scene texts are written in the story language,
* all anchors used in prompts are defined,
* the final output parses correctly as standard JSON.

Example
-------

### Input Story

> Le matin, Léo cherchait son jouet préféré dans le salon lumineux de sa maison. Il finit par trouver sa petite voiture rouge sous le canapé.
> Ravi, le petit garçon courut dehors. Il passa des heures à faire rouler son bolide dans l'herbe haute du jardin sous un grand soleil.
> Quand l'heure du goûter arriva, Léo rentra dans la cuisine. Assis à la grande table en bois, il dévora ses biscuits.

### Expected JSON Output

{
  "title": "Léo et sa voiture rouge",
  "style": "Children's watercolor illustration, soft strokes, pastel colors, warm and natural lighting",
  "constraints": "",
  "recurring_concepts": {
    "<LEO>": "5-year old male toddler wearing beige sports pants and a plain white t-shirt. He has very short black hair, brown eyes, fair skin with some freckles on his cheeks.",
    "<TOY_CAR>": "Small bright red toy sports car with black wheels and a white racing stripe.",
    "<HOUSE>": "Cozy suburban house interior, featuring warm oak wood floors, white walls with pastel yellow accents, and large windows letting in natural sunlight."
  },
  "scenes": [
    {
      "label": "scene-find-car",
      "text": "Le matin, Léo cherchait son jouet préféré dans le salon lumineux de sa maison. Il finit par trouver sa petite voiture rouge sous le canapé.",
      "prompt": "<LEO> is kneeling on the floor of the <HOUSE> living room, happily pulling a <TOY_CAR> from under a comfortable sofa.",
      "image_path": ""
    },
    {
      "label": "scene-garden-play",
      "text": "Ravi, le petit garçon courut dehors. Il passa des heures à faire rouler son bolide dans l'herbe haute du jardin sous un grand soleil.",
      "prompt": "<LEO> is playing outside in a bright sunny garden with tall green grass, enthusiastically pushing his <TOY_CAR> on the ground.",
      "image_path": ""
    },
    {
      "label": "scene-snack",
      "text": "Quand l'heure du goûter arriva, Léo rentra dans la cuisine. Assis à la grande table en bois, il dévora ses biscuits.",
      "prompt": "<LEO> is sitting at a large wooden table in the kitchen of the <HOUSE>, happily eating cookies.",
      "image_path": ""
    }
  ]
}
