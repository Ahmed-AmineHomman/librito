Assembly Storybook
==================

The assembly stage takes a segmented story with generated illustrations and
packages it as a fixed-layout EPUB storybook.

How to Run
----------

From the repository root:

.. code-block:: bash

   python helpers/assemble_storybook.py --story sir_turnip

On Windows PowerShell with the project virtual environment:

.. code-block:: powershell

   .\.venv\Scripts\python.exe helpers/assemble_storybook.py --story sir_turnip

What the Command Does
---------------------

1. Loads and validates ``database/<story>/story.json``.
2. Checks that the storybook has a non-empty title and at least one scene.
3. Verifies that every scene has non-empty reader text.
4. Verifies that every scene has an ``image_path`` pointing to an existing,
   readable illustration file.
5. Renders a text-only cover page.
6. Renders one text page and one illustration page for every scene.
7. Packages the result into ``database/<story>/story.epub``.

Layout Rules
------------

The current book intentionally uses a minimalist fixed layout:

* cover: title only,
* each scene: exactly two pages,
* left page: rendered scene text on a solid background color,
* right page: full-page illustration,
* no visible prompts, labels, or internal metadata.

Overflow Behavior
-----------------

Scene text must fit on a single left page. If a scene is too long for the
configured typography and page size, the script stops with an error instead of
spilling text onto extra pages.

Customization
-------------

The text-page and cover background color can be changed from the command line:

.. code-block:: bash

   python helpers/assemble_storybook.py --story sir_turnip --background-color "#f4efe6"

The default text color can also be overridden with ``--text-color``.
