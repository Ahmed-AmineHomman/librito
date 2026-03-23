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

**Story segmentation** (stage 1) is implemented as an agentic workflow. The
``segment_story.py`` script runs an LLM agent equipped with segmentation tools
that edit a filesystem-backed draft and export a validated ``story.json``.
The segmentation format and agent workflow are documented in
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

Both entrypoints read provider configuration from environment variables.

* Gemini uses ``GEMINI_API_KEY``.
* LM Studio segmentation uses ``LMS_API_URL`` and optionally ``LMS_API_KEY``.
* ComfyUI illustration runs use ``COMFYUI_API_URL`` and optionally
  ``COMFYUI_API_KEY``.

See :doc:`story_segmentation` and :doc:`illustration_generation` for details.

Quick Start
===========

To create or resume a segmented story with the segmentation agent:

.. code-block:: bash

    python segment_story.py --storybook database/leo --story-file docs/examples/leo/story.md --provider gemini --model gemini-2.0-flash

To resume an existing draft, omit ``--story-file``.

Once dependencies are installed and the appropriate API key is set, generate
illustrations for a segmented story:

.. code-block:: bash

    python illustrate_story.py --storybook path/to/story-folder

On Windows PowerShell with the project virtual environment:

.. code-block:: powershell

    .\.venv\Scripts\python.exe illustrate_story.py --storybook .\path\to\story-folder

A sample segmented story is available at ``docs/examples/leo/story.json``.

This command reads the segmented story, generates missing scene illustrations,
writes them into the ``illustrations/`` subdirectory inside the story folder, and
updates each scene's ``image_path`` in place. Already generated scenes are
skipped automatically (see :doc:`illustration_generation`).

Documentation
=============

* :doc:`story_segmentation` — the segmented story format and how to produce it.
* :doc:`illustration_generation` — how illustration generation works.
* :doc:`complete_example` — the full Leo example from story to illustrations.

Read them in that order.
