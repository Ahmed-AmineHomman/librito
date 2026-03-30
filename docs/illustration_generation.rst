Illustration Generation
=======================

The illustration generation stage takes a segmented story (see
:doc:`story_segmentation`) and produces one illustration per scene by sending
constructed prompts to an image generation model.

This document explains how the generation process works and uses the Leo sample
story (``docs/examples/leo/story.json``) as a running example.

How to Run
----------

Prerequisites are described in :doc:`README` (installation and API key setup).

From the repository root:

.. code-block:: bash

   python helpers/illustrate_story.py --story leo --provider gemini --model gemini-3.1-flash-image-preview

On Windows PowerShell with the project virtual environment:

.. code-block:: powershell

   .\.venv\Scripts\python.exe helpers/illustrate_story.py --story leo --provider gemini --model gemini-3.1-flash-image-preview

What the Command Does
---------------------

1. Loads and validates the segmented ``story.json``.
2. Creates the ``illustrations/`` subdirectory next to the JSON file if needed.
3. Iterates over scenes in array order.
4. For each scene without an existing illustration:

   a. Builds the render prompt (see `Prompt Construction`_ below).
   b. Sends the prompt to the configured image generation model.
   c. Saves the returned image as ``scene-001.png``, ``scene-002.png``, etc.,
      based on the current scene order.
   d. Updates the scene's ``image_path`` in the JSON file immediately.

Resume Behavior
---------------

If a scene already has a non-empty ``image_path`` and the referenced file exists
on disk, that scene is skipped. This makes interrupted runs resumable without
regenerating every image.

Use ``--force`` to ignore existing images and regenerate every scene in order.

Prompt Construction
-------------------

The generation process builds the render prompt in three layers:

1. **Style** — the global style from ``style``.
2. **Resolved prompt** — the scene's ``prompt`` field after anchor resolution
   (concept tags are replaced by their bracketed descriptions).
3. **Constraints** — when the storybook's ``constraints`` field is non-empty, its
   value is used. Otherwise the default constraints from the packaged resource
   file ``librito/resources/prompt_constraints.txt`` are applied.

These are assembled using the template in
``librito/resources/image_prompt_template.txt``:

.. code-block:: text

   Style: {style}

   Scene: {scene_prompt}

   Constraints:
   {constraints}

The current default packaged constraints are:

.. code-block:: text

   single scene
   no visible text
   no frame or border

Anchor Expansion Example
~~~~~~~~~~~~~~~~~~~~~~~~~

Take the first Leo scene prompt:

.. code-block:: text

   <LEO> kneels on the floor of the <LIVING_ROOM>, smiling with relief as he pulls his <TOY_CAR> from under the sofa.

Before sending it to the image generation model, each anchor is resolved to its
description in brackets:

.. code-block:: text

   [A 5-year-old boy with fair skin, short black hair, warm brown eyes, and a cheerful round face. He wears a plain white t-shirt and beige pants.] kneels on the floor of the [A cozy family living room with a soft sofa, warm wooden floor, pale walls, light curtains, and gentle daylight.], smiling with relief as he pulls his [A small bright red toy race car with a smooth shiny body, black wheels, and a thin white stripe on top.] from under the sofa.

This makes the prompt self-contained: the model receives actual visual
descriptions instead of abstract tag names.

Full Prompt Example
~~~~~~~~~~~~~~~~~~~

For the same scene, the render prompt is:

.. code-block:: text

   Style: Children's watercolor storybook illustration, soft brushwork, warm natural light, gentle pastel colors, cozy home interiors, and expressive characters

   Scene: [A 5-year-old boy with fair skin, short black hair, warm brown eyes, and a cheerful round face. He wears a plain white t-shirt and beige pants.] kneels on the floor of the [A cozy family living room with a soft sofa, warm wooden floor, pale walls, light curtains, and gentle daylight.], smiling with relief as he pulls his [A small bright red toy race car with a smooth shiny body, black wheels, and a thin white stripe on top.] from under the sofa.

   Constraints:
   single scene
   no visible text
   no frame or border

The style drives the general visual look, the scene prompt describes the action,
the anchors provide stable visual definitions, and the constraints add global
generation rules.

Output Layout
-------------

For a story identified as ``leo``, a successful run produces:

.. code-block:: text

   database/leo/
   ├── illustrations/
   │   ├── scene-001.png
   │   ├── scene-002.png
   │   └── ...
   └── story.json

After generation, each scene's ``image_path`` contains a relative path:

.. code-block:: json

   {
     "label": "scene-find-car",
     "text": "Léo a cinq ans, et son trésor, c'est une petite voiture rouge...",
     "prompt": "<LEO> kneels on the floor of the <LIVING_ROOM>...",
     "image_path": "illustrations/scene-001.png"
   }

.. _supported-providers:

Supported Providers
-------------------

The table below lists the currently supported image generation APIs, their
model argument meaning, and the environment variables used by each.

.. list-table::
   :header-rows: 1
   :widths: 20 35 25 20

   * - Provider
     - ``--model`` meaning
     - Env Variables
      - Default Settings
   * - Google Gemini
     - Gemini image model identifier
     - ``GEMINI_API_KEY``
     - 1:1 aspect ratio, 1K image size
   * - ComfyUI
     - Checkpoint filename used with ``workflow_checkpoint.json``
     - ``COMFYUI_API_URL`` and optional ``COMFYUI_API_KEY``
     - 1:1 aspect ratio, 1K image size
   * - Mock
     - Ignored placeholder value
     - None
     - 1:1 aspect ratio, 1K image size

Set the appropriate variables before running:

.. code-block:: bash

   export GEMINI_API_KEY="your-api-key"
   export COMFYUI_API_URL="http://127.0.0.1:8188"

On Windows PowerShell:

.. code-block:: powershell

   $env:GEMINI_API_KEY = "your-api-key"
   $env:COMFYUI_API_URL = "http://127.0.0.1:8188"

Provider connection settings come from environment variables, while model and
image-generation options are exposed through the command line.

Current Limitations
-------------------

The current implementation does not provide:

* a dry-run mode,
* a single-scene generation flag.

For debugging purposes, the generation script can be run with
``--provider mock --model mock`` to produce pixel-noise images without calling
a real API.

