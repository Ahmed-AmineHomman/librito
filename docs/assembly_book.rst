Assembly Book
=============

The assembly stage takes a structured storybook with generated illustrations and
packages it as a fixed-layout EPUB book.

How to Run
----------

From the repository root:

.. code-block:: bash

   python helpers/assemble_book.py --story sir_turnip

On Windows PowerShell with the project virtual environment:

.. code-block:: powershell

   .\.venv\Scripts\python.exe helpers/assemble_book.py --story sir_turnip

What the Command Does
---------------------

1. Loads and validates ``database/<story>/story.json``.
2. Matches the page geometry to the requested ``--aspect-ratio``.
3. Checks that the storybook has a non-empty title and author.
4. Validates the required book parts:

   * front-cover illustration,
   * title-page structure,
   * back-cover teaser.

5. Validates any optional illustrated book parts that are present.
6. Verifies that every scene has non-empty reader text and a readable
   illustration file.
7. Renders the front matter, scene spreads, optional closing spread, and back
   cover.
8. Packages the result into ``database/<story>/story.epub``.

Rendered Page Order
-------------------

The assembler renders pages in this order:

1. front cover
2. front endpaper on the left when present, otherwise blank
3. dedication/epigraph page on the right when present, otherwise blank
4. frontispiece on the left when present, otherwise blank
5. title page on the right
6. one text page and one full-page illustration for each scene
7. closing facing page on the left when present, otherwise blank
8. closing illustration on the right when present, otherwise blank
9. back cover

Blank filler pages are inserted only when needed to preserve the intended
left-page/right-page pairings.

Layout Rules
------------

The current book uses these rendering rules:

* **Front cover**: always uses the required full-page illustration. When
  ``parts.front_cover.illustration.text_mode`` is ``overlay``, the assembler
  writes the canonical ``title`` and ``author`` on top of that image. When the
  value is ``embedded``, it assumes the text is already inside the artwork.
* **Front endpaper**: renders the supplied illustration full-page.
* **Opening page**: renders the supplied opening-page ``text`` entries.
* **Frontispiece**: renders the supplied illustration full-page.
* **Title page**: always renders the canonical ``title`` and ``author`` and, if
  present, adds the optional small illustration beneath them.
* **Scenes**: each scene remains a two-page spread with story text on the left
  and a full-page illustration on the right.
* **Closing facing page**: renders the supplied closing-page ``text`` entries.
* **Closing illustration**: renders the supplied illustration full-page.
* **Back cover**: always uses the required teaser stored in
  ``parts.back_cover.text``. When a back-cover illustration is present, it is
  always treated as the whole page. ``text_mode = "overlay"`` makes the
  assembler add the teaser, while ``text_mode = "embedded"`` assumes the
  teaser is already part of the image.

Overflow Behavior
-----------------

Any text the assembler is responsible for rendering must fit on its target
page:

* front-cover title and author when ``text_mode`` is ``overlay``,
* title-page title and author,
* opening-page text,
* scene text,
* closing-facing-page text,
* back-cover teaser when it must be overlaid onto the illustration.

If any of those blocks do not fit the configured typography and page size, the
script stops with an error instead of spilling text onto extra pages.

Customization
-------------

The background color used for text pages and blank filler pages can be changed
from the command line:

.. code-block:: bash

   python helpers/assemble_book.py --story sir_turnip --background-color "#f4efe6"

Use ``--aspect-ratio`` to match the page shape to the illustration workflow:

.. code-block:: bash

   python helpers/assemble_book.py --story sir_turnip --aspect-ratio 3:4

The default text color can also be overridden with ``--text-color``.
