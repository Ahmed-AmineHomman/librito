Story Segmentation
==================

The story segmentation stage transforms a raw story into a structured JSON file
ready for illustration generation and book assembly. The result captures:

* the canonical book title and author,
* one global visual style,
* optional generation constraints,
* visual concepts defined as anchors,
* structured non-scene book parts such as covers and front matter,
* an ordered list of scenes containing story text and illustration prompts.

This page describes both the **storybook schema** and the **agent-native
workflow** used to produce it.

Expected JSON Format
--------------------

The canonical storybook must be a valid JSON object with exactly this shape:

.. code-block:: json

   {
     "title": "Story title",
     "author": "Author name",
     "style": "Artistic style description in English",
     "constraints": "",
     "concepts": {
       "<CONCEPT_NAME>": "Detailed visual description of the concept"
     },
     "parts": {
       "front_cover": {
         "text": [],
         "illustration": {
           "prompt": "Illustration prompt in English",
           "image_path": "",
           "text_mode": "overlay"
         }
       },
       "front_endpaper": null,
       "opening_page": null,
       "frontispiece": null,
       "title_page": {
         "text": [],
         "illustration": null
       },
       "closing_facing_page": null,
       "closing_illustration": null,
       "back_cover": {
         "text": [
           "Reader-facing teaser text"
         ],
         "illustration": null
       }
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

Top-level fields
++++++++++++++++

``title``
   Canonical book title. The assembler uses this on the front cover and title
   page.

``author``
   Canonical reader-facing author name. The assembler uses this on the front
   cover and title page.

``style``
   A single English description of the visual style applied to all generated
   illustrations. This value is automatically prefixed to every scene prompt
   during scene illustration generation.

``constraints``
   Optional generation constraints as a single string. When empty, the built-in
   constraints shipped in ``librito/resources/prompt_constraints.txt`` are used.

``concepts``
   A dictionary of reusable visual anchors such as characters, settings, and
   recurring objects. Each key is an uppercase tag like ``<LEO>`` or
   ``<LIVING_ROOM>`` and each value is a stable visual description.

``parts``
   Structured non-scene pages used by the final book.

Book-part fields
++++++++++++++++

Every book-part slot stores the same ``PageSpec`` structure:

* ``text``: an ordered array of reader-facing strings,
* ``illustration``: either ``null`` or an illustration object.

The illustration object always contains:

* ``prompt``: illustration prompt written in English,
* ``image_path``: relative path to the generated image,
* ``text_mode``: either ``"overlay"``, ``"embedded"``, or ``null`` when that
  distinction is not relevant for the page.

The slot-specific meaning is interpreted by the assembler:

``parts.front_cover``
   Required page object. In practice, assembly expects its illustration to be
   present and uses ``text_mode`` to decide whether to overlay the canonical
   title and author.

``parts.front_endpaper``
   Optional page object or ``null``. When present, it usually uses only
   ``illustration``.

``parts.opening_page``
   Optional page object or ``null``. When present, its ``text`` array carries
   the dedication and/or epigraph.

``parts.frontispiece``
   Optional page object or ``null``. When present, it usually uses only
   ``illustration``.

``parts.title_page``
   Required page object. The assembler always renders the canonical title and
   author; the optional illustration is treated as a small supporting image.

``parts.closing_facing_page``
   Optional page object or ``null``. When present, its ``text`` array carries
   the free closing text.

``parts.closing_illustration``
   Optional page object or ``null``. When present, it usually uses only
   ``illustration``.

``parts.back_cover``
   Required page object. In practice, assembly expects ``text`` to contain the
   teaser, and when an illustration is present it is always treated as a
   full-page image. ``text_mode`` determines whether the teaser is overlaid by
   the assembler or already embedded in that image.

Scene fields
++++++++++++

``scenes[].label``
   Stable identifier for the scene. Labels must be unique and non-empty.

``scenes[].text``
   Reader-facing scene text written in the language of the original story.

``scenes[].prompt``
   Scene illustration prompt written in English.

``scenes[].image_path``
   Relative path to the generated scene illustration inside the story
   workspace.

Schema vs. Guidelines
---------------------

The repository deliberately separates:

* **schema**: which attributes exist, whether they are required, and their
  basic types,
* **skills and specs**: what those fields should contain semantically,
* **assembly**: how the stored content is finally laid out on pages.

As a result, the JSON schema does **not** enforce editorial rules such as:

* whether a front cover should use framing rather than embedded text,
* whether the front endpaper or the frontispiece should carry the quieter image,
* whether the closing illustration should avoid or embrace end-of-story spoilers.

Those are creative and layout guidelines handled by skills and documentation,
not by structural validation.

Illustration and Text Guidelines
--------------------------------

The following guidelines are repository standards for authoring content. They
are advisory, not schema rules.

Front cover
~~~~~~~~~~~

* Always design for title and author visibility.
* When ``text_mode`` is ``overlay``, the assembler adds the title and author on
  top of the illustration.
* When ``text_mode`` is ``embedded``, the title and author are assumed to
  already appear inside the image, so the assembler does not add them again.
* The illustration should either represent an iconic story moment or combine
  the story's main recurring concepts into a cover-specific composition.

Front endpaper and frontispiece
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* These pages work best as calmer, less cluttered images.
* Prefer contemplative subjects such as a setting, a single object, or a quiet
  character moment.
* In most books, only one of ``front_endpaper`` or ``frontispiece`` should take
  the more prominent illustration role to avoid visual overload.

Title page
~~~~~~~~~~

* The assembler always places the canonical ``title`` and ``author`` on the
  title page.
* The optional title-page illustration should stay small and simple.
* The illustration should support the title page rather than dominate it.

Opening page
~~~~~~~~~~~~

* The page ``text`` array may contain one dedication, one epigraph, or both in
  reading order.
* A dedication addresses someone directly.
* An epigraph is a short quote that sets the tone.

Closing illustration
~~~~~~~~~~~~~~~~~~~~

* The closing illustration may reflect the story ending more directly than the
  front matter does.
* It can visually reference the final emotional note or the resolved state of
  the story.

Back cover
~~~~~~~~~~

* The back cover always stores its teaser inside ``text``.
* When back-cover ``text_mode`` is ``overlay``, the assembler renders the teaser
  on top of the full-page illustration.
* When ``text_mode`` is ``embedded``, the teaser is assumed to already be part
  of the supplied illustration and is not drawn again by the assembler.

Running Example
---------------

The Leo sample story (``docs/examples/leo/story.json``) illustrates the format.
Shortened excerpt showing the global fields, book parts, and one scene:

.. code-block:: json

   {
     "title": "Léo et sa voiture rouge",
     "author": "Librito Example",
     "style": "Children's watercolor storybook illustration, soft brushwork, warm natural light, gentle pastel colors, cozy home interiors, and expressive characters",
     "constraints": "",
     "concepts": {
       "<LEO>": "A 5-year-old boy with fair skin, short black hair, warm brown eyes, and a cheerful round face. He wears a plain white t-shirt and beige pants."
     },
     "parts": {
       "front_cover": {
         "text": [],
         "illustration": {
           "prompt": "<LEO> smiles while holding his <TOY_CAR> in the warm light of the <LIVING_ROOM>.",
           "image_path": "",
           "text_mode": "overlay"
         }
       },
       "front_endpaper": null,
       "opening_page": null,
       "frontispiece": null,
       "title_page": {
         "text": [],
         "illustration": null
       },
       "closing_facing_page": null,
       "closing_illustration": null,
       "back_cover": {
         "text": [
           "Une histoire douce et lumineuse autour d'un petit garçon et de sa voiture rouge préférée."
         ],
         "illustration": null
       }
     },
     "scenes": [
       {
         "label": "scene-find-car",
         "text": "Léo a cinq ans, et son trésor, c'est une petite voiture rouge...",
         "prompt": "<LEO> kneels on the floor of the <LIVING_ROOM>...",
         "image_path": ""
       }
     ]
   }

Segmentation Workflow
---------------------

The segmentation workflow remains agentic, but the underlying design is simple:

1. Read the full story.
2. Inspect the current storybook draft.
3. Define or revise the canonical title, author, style, and optional constraints.
4. Define the required and optional book parts relevant to the intended book.
5. Define concepts only for visually important concepts that recur.
6. Build scenes in narrative order.
7. Write scene texts in the story language.
8. Write illustration prompts in English.
9. Run prompt-consistency checks.
10. Repair weak or invalid state until the artifact is structurally valid.

Prompt Consistency
------------------

Prompt consistency is currently enforced for scene prompts through the existing
validator stack:

* undefined anchors,
* unused concepts,
* anchors used in exactly one unique scene.

This keeps the deterministic checks narrow while preserving the repository's
core scene-illustration policy.

Implementation
--------------

The current implementation is repository-native rather than script-driven:

* ``story.md`` stores the raw source story,
* ``story.json`` stores the canonical storybook artifact,
* Codex performs the semantic segmentation work directly in the workspace,
* helper scripts provide deterministic validation and downstream processing.

Runtime configuration comes from environment variables:

* ``GEMINI_API_KEY`` for Gemini-backed helpers,
* ``LMS_API_URL`` for LM Studio's OpenAI-compatible endpoint,
* ``LMS_API_KEY`` when the local endpoint expects authentication.

Checklist
---------

Before a storybook is passed downstream, verify:

* the file is valid JSON,
* top-level keys are exactly ``title``, ``author``, ``style``, ``constraints``,
  ``concepts``, ``parts``, and ``scenes``,
* ``parts`` contains exactly the repository-defined book-part keys,
* required parts are present as objects,
* optional parts are either valid objects or ``null``,
* each scene contains exactly ``label``, ``text``, ``prompt``, and
  ``image_path``,
* labels are unique non-empty strings,
* prompts are written in English,
* scene texts stay in the story language,
* every scene tag used in a prompt is defined in ``concepts``,
* unused concepts are removed,
* anchors used in one unique scene are removed or inlined.
