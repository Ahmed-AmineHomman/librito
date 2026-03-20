Story Segmentation
==================

The illustration generation stage expects a **segmented story** as input: a
single JSON file describing the story title, visual style, optional constraints,
recurring concept definitions, and an ordered list of scenes with their
illustration prompts.

This segmentation is the bridge between a raw story and an illustrated book.
``librito`` does not automate this step. It can be done:

* **manually**, by writing the JSON file according to the schema below, or
* **with a coding agent** (e.g. GitHub Copilot) configured with the
  ``segment-story`` skill shipped in ``.agents/skills/segment-story/``.

Because story segmentation is inherently a creative task — extracting narrative
beats, defining visual concepts, writing illustration prompts — it is well
suited to LLM-based agents and may never be implemented as library code.

This document describes the expected format and gives guidance on how to produce
good segmentations. It uses the Leo sample story shipped in
``docs/examples/leo/`` as a running example. That directory contains:

* ``story.md`` — the original story text (input to segmentation),
* ``story.json`` — the resulting segmented story (input to illustration
  generation).

Expected JSON Format
--------------------

The segmented story must be a valid JSON object with exactly this structure:

.. code-block:: json

   {
     "title": "Story title",
     "style": "Artistic style description in English",
     "constraints": "",
     "recurring_concepts": {
       "<CONCEPT_NAME>": "Detailed visual description of the concept"
     },
     "scenes": [
       {
         "index": 1,
         "text": "Scene text in the language of the story",
         "prompt": "Illustration prompt in English",
         "image_path": ""
       }
     ]
   }

Field Reference
~~~~~~~~~~~~~~~

``title``
   The book title.

``style``
   A single English description of the visual style applied to all
   illustrations. This value is automatically prefixed to every scene prompt
   during generation.

``constraints``
   Optional generation constraints as a single string. When empty (the default),
   the built-in constraints shipped in
   ``librito/resources/prompt_constraints.txt`` are used. Populate this field
   only when the story or user requires specific constraints beyond the defaults.

``recurring_concepts``
   A dictionary of reusable visual anchors (characters, places, objects). Each
   key is an uppercase tag like ``<LEO>`` or ``<LIVING_ROOM>`` and each value is
   a stable visual description. During generation, tags in scene prompts are
   replaced by their description.

``scenes[].index``
   One-based position of the scene within the story.

``scenes[].text``
   The story text for the scene, written in the language of the original story.

``scenes[].prompt``
   The illustration prompt for the scene, always written in English. Should
   reference recurring concepts through their tags.

``scenes[].image_path``
   Reserved for generated image paths. Must be an empty string at segmentation
   time.

Running Example
---------------

The Leo sample story (``docs/examples/leo/story.json``) illustrates the format.
Shortened excerpt showing one scene:

.. code-block:: json

   {
     "title": "Léo et sa voiture rouge",
     "style": "Children's watercolor storybook illustration, soft brushwork, warm natural light, gentle pastel colors, cozy home interiors, and expressive characters",
     "constraints": "",
     "recurring_concepts": {
       "<LEO>": "A 5-year-old boy with fair skin, short black hair, warm brown eyes, and a cheerful round face. He wears a plain white t-shirt and beige pants.",
       "<TOY_CAR>": "A small bright red toy race car with a smooth shiny body, black wheels, and a thin white stripe on top.",
       "<LIVING_ROOM>": "A cozy family living room with a soft sofa, warm wooden floor, pale walls, light curtains, and gentle daylight."
     },
     "scenes": [
       {
         "index": 1,
         "text": "Léo a cinq ans, et son trésor, c'est une petite voiture rouge qu'il ne quitte jamais...",
         "prompt": "<LEO> kneels on the floor of the <LIVING_ROOM>, smiling with relief as he pulls his <TOY_CAR> from under the sofa.",
         "image_path": ""
       }
     ]
   }

In this example:

* the story text stays in French (the original language),
* the illustration prompt is written in English,
* recurring concepts are defined once and referenced by tag,
* ``constraints`` is empty — the default constraints apply,
* ``image_path`` is empty because no illustration has been generated yet.

The full example with all three scenes is available in the file itself.

How to Segment a Story
----------------------

Good segmentation does not cut the story mechanically sentence by sentence. It
extracts the scenes that matter for the illustrated narrative.

Recommended method:

1. Read the full story and identify its main narrative beats.
2. Identify recurring visual concepts (characters, locations, objects) that must
   stay consistent across illustrations.
3. Define one global illustration style in English.
4. Split the story into scenes that preserve narrative flow.
5. Write one ``text`` per scene in the language of the original story.
6. Write one ``prompt`` per scene in English, focusing on the main visual idea.
7. Use recurring concept tags in prompts instead of rewriting descriptions.

The goal is to preserve the story's meaning, rhythm, and readability while
producing clear illustration prompts. Some parts of the original story may be
dropped as long as the overall flow is not harmed.

Rules
-----

* ``text`` stays in the language of the original story.
* ``prompt`` is always written in English (best understood by image generation
  models).
* Prompts must use tags whenever a recurring character, place, or object appears.
* Every tag used in a prompt must be defined in ``recurring_concepts``.
* Character descriptions should be visually detailed enough to ensure consistent
  rendering across scenes (body type, age, clothing, hair, eye color, etc.).
* ``image_path`` must be ``""`` at segmentation time.
* ``constraints`` should be ``""`` unless specific constraints are needed.

Using Tags Effectively
----------------------

Tags prevent the image generation model from reinventing the same character or
object differently in each scene.

Prefer prompts that use defined tags:

.. code-block:: text

   <LEO> kneels on the floor of the <LIVING_ROOM>, smiling as he pulls his <TOY_CAR> from under the sofa.

Avoid prompts that drop the tags:

.. code-block:: text

   Leo kneels on the floor of the living room, smiling as he pulls his small red toy car from under the sofa.

The second version is weaker because the image generation model no longer has
stable visual definitions for Leo, the living room, or the toy car.

Not every element needs a tag. One-off scene details can stay as plain text:

.. code-block:: text

   <LEO> sits in the <LIVING_ROOM> with his mother, happily enjoying a snack of cakes.

Here ``his mother`` and ``a snack of cakes`` are local to the scene and do not
need reusable tags.

Rule of thumb:

* recurring, visually important elements → tags,
* local scene details → plain text.

Checklist
---------

Before passing the segmented story to the generation stage, verify:

* the file is valid JSON,
* top-level keys are exactly ``title``, ``style``, ``constraints``,
  ``recurring_concepts``, and ``scenes``,
* each scene contains exactly ``index``, ``text``, ``prompt``, and
  ``image_path``,
* prompts are in English,
* scene texts are in the story language,
* every tag used in a prompt is defined in ``recurring_concepts``,
* ``image_path`` is empty for every scene,
* ``constraints`` is empty unless specific constraints are needed.
