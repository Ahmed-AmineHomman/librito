Story Segmentation
==================

The story segmentation stage transforms a raw story into a structured JSON file
ready for illustration generation. The result captures:

* the story title,
* one global visual style,
* optional generation constraints,
* recurring visual concepts defined as anchors,
* an ordered list of scenes containing story text and illustration prompts.

This page describes both the **segmentation standard** and the **agentic
workflow** used to produce it.

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
         "label": "scene-find-car",
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

   In the agent tool interface, recurring concepts are created and renamed from
   plain names such as ``leo`` or ``living room``. The implementation
   normalizes them internally to canonical keys such as ``<LEO>`` and
   ``<LIVING_ROOM>``.

``scenes[].label``
   Stable identifier for the scene. Labels must be unique and non-empty. They
   do not define order; the order comes from the ``scenes`` array itself.

``scenes[].text``
   The story text for the scene, written in the language of the original story.

``scenes[].prompt``
   The illustration prompt for the scene, always written in English. It should
   reference recurring concepts through their tags whenever those concepts
   appear in more than one scene.

``scenes[].image_path``
   Reserved for generated image paths. Segmentation tools do not modify it.

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
         "label": "scene-find-car",
         "text": "Léo a cinq ans, et son trésor, c'est une petite voiture rouge qu'il ne quitte jamais...",
         "prompt": "<LEO> kneels on the floor of the <LIVING_ROOM>, smiling with relief as he pulls his <TOY_CAR> from under the sofa.",
         "image_path": ""
       }
     ]
   }

In this example:

* the story text stays in French,
* the illustration prompt is written in English,
* recurring concepts are defined once and referenced by tag,
* scene identity is handled by ``label``,
* scene order is defined by the list order,
* ``constraints`` is empty because the default constraints apply.

Segmentation Architecture
-------------------------

The segmentation workflow is agentic, but the underlying design is simple:

1. A source story is loaded.
2. A mutable segmentation state is created or resumed.
3. The agent iteratively edits that state through a constrained toolset.
4. The agent uses analysis tools to inspect the current draft.
5. The final storybook is exported only when validation passes.

This design deliberately separates:

* **creative work**: choosing scenes, phrasing scene text, selecting visual
  emphasis, and defining concept descriptions;
* **structural guarantees**: schema validity, anchor usage, and prompt
  consistency.

The state being edited is the storybook itself: global attributes, recurring
concepts, and ordered scenes.

Segmentation Instructions
-------------------------

The segmentation agent should follow a narrow workflow:

1. Read the full story.
2. Inspect the current segmentation draft.
3. Define or update the title, style, and optional constraints.
4. Define recurring concepts only for visually important concepts that appear in
   more than one scene.
5. Build scenes in narrative order.
6. Write scene texts in the story language.
7. Write scene prompts in English, using explicit anchors like ``<LEO>`` when a
   recurring concept is referenced.
8. Run prompt-consistency checks.
9. Repair the draft until validation passes.
10. Export the storybook.

Prompt Consistency
------------------

Prompt consistency is treated as a concrete validation problem.

The first validation slice checks only:

* undefined anchors,
* unused recurring concepts,
* anchors used in exactly one unique scene.

This keeps the validator narrow and deterministic while still enforcing the core
anchor policy:

* recurring concepts should be anchored,
* one-scene concepts should remain inline,
* every anchored prompt must remain resolvable.

Toolset
-------

An implementation can expose the following categories of tools:

Read tools
~~~~~~~~~~

* get the full story,
* get the title, style, and constraints,
* list recurring concepts,
* list scenes in their current order.

Write tools
~~~~~~~~~~~

* set the title, style, and constraints,
* add, remove, and rename recurring concepts,
* add, update, move, and delete scenes.

Analysis tools
~~~~~~~~~~~~~~

* count concept occurrences across the story,
* check prompt consistency,
* expand prompts,
* expand scenes with expanded prompts when needed.

Finalization
~~~~~~~~~~~~

* export the final storybook only when validation succeeds.

Implementation
--------------

The current implementation uses a filesystem-backed draft and a single ADK
agent run:

* ``segment_story.py`` starts the segmentation agent,
* the raw story is stored separately from the segmentation draft,
* the draft is autosaved after every mutation tool call,
* the final ``story.json`` is written only by the export tool,
* the agent tools are thin wrappers over a Python editor service.

More concretely:

* ``story.md`` stores the source story text,
* ``story.segmentation.draft.json`` stores the mutable segmentation draft,
* ``story.json`` stores the exported validated segmentation.

The current runtime uses:

* Google ADK as the agent framework,
* plain function tools registered with the agent,
* LiteLLM for LM Studio's local API,
* Gemini models for larger runs when the ``gemini`` provider is selected.

Runtime configuration comes from environment variables:

* ``GEMINI_API_KEY`` for Gemini-backed segmentation,
* ``LMS_API_URL`` for LM Studio's OpenAI-compatible endpoint,
* ``LMS_API_KEY`` when the local endpoint expects authentication.

Checklist
---------

Before a segmentation is passed to illustration generation, verify:

* the file is valid JSON,
* top-level keys are exactly ``title``, ``style``, ``constraints``,
  ``recurring_concepts``, and ``scenes``,
* each scene contains exactly ``label``, ``text``, ``prompt``, and
  ``image_path``,
* labels are unique non-empty strings,
* prompts are in English,
* scene texts are in the story language,
* every tag used in a prompt is defined in ``recurring_concepts``,
* unused recurring concepts are removed,
* anchors used in one unique scene are removed or inlined.
