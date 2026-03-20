Story Segmentation for Generation
=================================

The generation phase expects a **segmented story** as input. This input is a
single JSON object describing:

* the story title,
* the visual constants shared by all illustrations,
* the ordered list of scenes to generate.

In practice, this segmentation is the bridge between a raw story and an
illustrated book. A human can prepare it manually, and a coding agent can also
prepare it when equipped with the appropriate segmentation skill such as
``segment-story``.

What the Generation Phase Expects
---------------------------------

The expected input format is a valid JSON object with exactly this structure:

.. code-block:: json

   {
     "title": "Story title",
     "constants": {
       "style": "Artistic style in English",
       "recurring_concepts": {
         "<CONCEPT_NAME>": "Detailed concept description"
       }
     },
     "scenes": [
       {
         "text": "Scene text in the language of the story",
         "prompt": "Scene illustration prompt in English",
         "image_path": ""
       }
     ]
   }

Each field has a precise role:

``title``
   The book title.

``constants.style``
   A single English description of the visual style to keep all generated
   illustrations coherent.

``constants.recurring_concepts``
   A dictionary of reusable visual anchors such as characters, places, and
   objects. Each key is a tag like ``<CALMIO>`` or ``<RIVERBANK>`` and each
   value is a stable visual description.

``scenes``
   The ordered sequence of story scenes. Each scene contains the story text to
   display and the English prompt to use for illustration generation.

``image_path``
   Reserved for generated image files. During segmentation it should be an
   empty string.

How to Segment a Story
----------------------

Good segmentation does not cut the story mechanically sentence by sentence. It
extracts the scenes that matter for the illustrated narrative.

Use the following method:

1. Read the full story and identify its main narrative beats.
2. Extract the recurring concepts that must stay visually consistent:
   characters, locations, objects, creatures, and distinctive groups.
3. Define one global illustration style in English.
4. Split the story into scenes that preserve the narrative flow.
5. Write one ``text`` per scene using the language of the original story.
6. Write one ``prompt`` per scene in English, focusing on the main image to
   generate.
7. Reuse recurring concept tags inside prompts instead of rewriting character
   or setting descriptions every time.

The goal is not to preserve every sentence of the original story. The goal is
to preserve the story's meaning, rhythm, and readability while producing clear
illustration prompts.

Rules That Matter
-----------------

The generation input should follow these rules:

* ``text`` stays in the language of the original story.
* ``prompt`` is always written in English.
* Prompts should use recurring concept tags whenever a recurring character,
  place, or object appears.
* Every tag used in a prompt must be defined in
  ``constants.recurring_concepts``.
* Character tags should be visually stable enough to avoid inconsistent
  illustrations across scenes.
* ``image_path`` should be ``""`` at segmentation time.

The tag system is essential. It prevents the image model from reinventing the
same character or object differently from one scene to the next.

Example of a Good Prompt Strategy
---------------------------------

Prefer prompts that reuse defined tags:

.. code-block:: text

   <CALMIO> trots cheerfully along the <VILLAGE_STREET> with <VILLAGE_CHILDREN>.

Avoid prompts that drop the tags:

.. code-block:: text

   Calmio trots cheerfully along the village street with some children.

The second version is weaker because the image generator no longer has a stable
definition for the dog, the street, or the children.

Illustrated Example
-------------------

The sample story in ``database/calmio/story.json`` shows the target format.
Below is a shortened excerpt.

Example recurring concepts:

.. code-block:: json

   {
     "style": "Children's watercolor storybook illustration, soft brushwork, luminous golden light, pastel earth tones, delicate textures, and expressive animal faces",
     "recurring_concepts": {
       "<CALMIO>": "A small, fluffy cream-and-golden dog with very soft fur, a compact body, drooping ears, and large kind eyes. He has a gentle, curious expression and no clothing.",
       "<VILLAGE_STREET>": "A peaceful old village street paved with cobblestones, lined with warm stone houses, flower boxes, and soft afternoon sunlight.",
       "<BUTTERFLY>": "A delicate butterfly with autumn-colored wings that flutter lightly through the air."
     }
   }

Example scene:

.. code-block:: json

   {
     "text": "One golden afternoon, Calmio followed a butterfly with wings as delicate as autumn leaves.",
     "prompt": "<CALMIO> chases a <BUTTERFLY> along the <VILLAGE_STREET> under warm afternoon light.",
     "image_path": ""
   }

Notice the division of responsibilities:

* the scene ``text`` tells the story to the reader,
* the scene ``prompt`` describes the image to generate,
* the tags carry the stable visual definitions.

Checklist Before Passing to Generation
--------------------------------------

Before using a segmented story as generation input, verify the following:

* the file is valid JSON,
* the top-level keys are exactly ``title``, ``constants``, and ``scenes``,
* ``constants`` contains both ``style`` and ``recurring_concepts``,
* each scene contains exactly ``text``, ``prompt``, and ``image_path``,
* prompts are in English,
* scene texts are in the story language,
* all prompt tags are defined,
* ``image_path`` is empty for every scene.

Who Can Produce This Input
--------------------------

This segmentation can be written by hand, but it is also suitable for coding
agents. In particular, an agent configured with a story-segmentation skill such
as ``segment-story`` can transform a raw story into the JSON structure expected
by the generation phase.
