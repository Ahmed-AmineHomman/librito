=======
Librito
=======

``librito`` is an early-stage pipeline for transforming stories into illustrated
storybooks. The full pipeline is divided into three stages:

1. **Story segmentation** — decomposing a natural-language story into a
   structured JSON file containing scenes, illustration prompts, and visual
   constants.
2. **Illustration generation** — producing one illustration per scene from the
   segmented story using an image generation model.
3. **Assembly** — constructing the final illustrated storybook from scene texts
   and generated illustrations.

Current State
=============

**Story segmentation** (stage 1) is an agent-native workflow carried out
directly in the repository by Codex using skills and helper scripts. The
canonical output is a validated ``story.json`` stored in the story workspace.
The segmentation format and workflow are documented in
:doc:`story_segmentation`.

**Illustration generation** (stage 2) is implemented as runnable code and
consumes the exported ``story.json``.

**Assembly** (stage 3) is not yet implemented.

A sample story (Leo) is included under ``docs/examples/leo/`` with both the
original text and the segmented JSON ready for illustration generation.

Installation
============

Clone the repository and install the required dependencies:

.. code-block:: bash

    git clone git@github.com:Ahmed-AmineHomman/librito.git
    cd librito
    pip install -r requirements.txt

Environment
===========

Runtime components read provider configuration from environment variables.

* Gemini uses ``GEMINI_API_KEY``.
* LM Studio embedding helpers use ``LMS_API_URL`` and optionally ``LMS_API_KEY``.
* ComfyUI illustration runs use ``COMFYUI_API_URL`` and optionally
  ``COMFYUI_API_KEY``.

See :doc:`story_segmentation` and :doc:`illustration_generation` for details.

Quick Start
===========

To segment a story, place the source text at ``database/<story>/story.md`` and
run the segmentation workflow with Codex inside this repository. The resulting
canonical artifact is ``database/<story>/story.json``.

To validate anchor usage in an existing segmented story:

.. code-block:: bash

    python helpers/check_anchoring_consistency.py --story leo

Once dependencies are installed and the appropriate API key is set, generate
illustrations for a segmented story:

.. code-block:: bash

    python helpers/illustrate_story.py --story leo --provider gemini --model gemini-3.1-flash-image-preview

On Windows PowerShell with the project virtual environment:

.. code-block:: powershell

    .\.venv\Scripts\python.exe helpers/illustrate_story.py --story leo --provider gemini --model gemini-3.1-flash-image-preview

A sample segmented story is available at ``docs/examples/leo/story.json``.

This command reads ``database/leo/story.json``, generates missing scene
illustrations inside ``database/leo/illustrations/``, and updates each scene's
``image_path`` in place. Already generated scenes are skipped automatically
(see :doc:`illustration_generation`).

Documentation
=============

* :doc:`story_segmentation` — the segmented story format and how to produce it.
* :doc:`illustration_generation` — how illustration generation works.
* :doc:`complete_example` — the full Leo example from story to illustrations.

Read them in that order.
