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

Only **illustration generation** (stage 2) is implemented as runnable code.

**Story segmentation** (stage 1) is not automated by ``librito``. It can be
performed manually or with the help of a coding agent (such as GitHub Copilot)
equipped with the ``segment-story`` skill shipped in
``.agents/skills/segment-story/``. Because segmentation is inherently a creative
task, it is well suited to LLM-based agents and may never be implemented as
library code.

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

API Key
=======

Illustration generation requires an API key for the configured image generation
provider. See the :ref:`supported-providers` section in
:doc:`illustration_generation` for the list of supported providers and their
required environment variables.

Quick Start
===========

Once dependencies are installed and the appropriate API key is set, generate
illustrations for a segmented story:

.. code-block:: bash

    python -m librito.generate_illustrations path/to/story.json

On Windows PowerShell with the project virtual environment:

.. code-block:: powershell

    .\.venv\Scripts\python.exe -m librito.generate_illustrations .\path\to\story.json

A sample segmented story is available at ``docs/examples/leo/story.json``.

This command reads the segmented story, generates missing scene illustrations,
writes them into the ``illustrations/`` subdirectory next to the JSON file, and
updates each scene's ``image_path`` in place. Already generated scenes are
skipped automatically (see :doc:`illustration_generation`).

Documentation
=============

* :doc:`story_segmentation` — the segmented story format and how to produce it.
* :doc:`illustration_generation` — how illustration generation works.
* :doc:`complete_example` — the full Leo example from story to illustrations.

Read them in that order.
