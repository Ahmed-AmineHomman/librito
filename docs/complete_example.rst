Complete Example
================

This page walks through the full Leo sample — from the original story to the
segmented JSON to the generated illustrations — so you can see what each stage
of the pipeline produces without leaving the documentation.

All source files are in ``docs/examples/leo/``.

Original Story
--------------

The starting point is a short children's story written in French:

   Léo a cinq ans, et son trésor, c'est une petite voiture rouge qu'il ne
   quitte jamais. Ce matin-là, impossible de la trouver. Il cherche partout,
   soulève les coussins, regarde derrière les rideaux… jusqu'à ce qu'il
   l'aperçoive, cachée sous le canapé du salon. Son visage s'illumine quand il
   la récupère enfin.

   Tout content, il file dans sa chambre pour jouer. Il fait rouler son bolide
   sur le parquet, invente des circuits autour des pieds de chaise et le long
   des bords du tapis. Les heures passent sans qu'il s'en rende compte.

   Quand la faim se fait sentir, Léo retourne au salon. Sa maman lui a préparé
   de bons gâteaux pour le goûter. Assis près d'elle, il les dévore avec
   appétit, sa petite voiture rouge serrée dans la main.

Segmented Story
---------------

After segmentation (see :doc:`story_segmentation`), the story becomes a
structured JSON file. The segmentation defines a visual style, three concept
tags, and three scenes:

.. literalinclude:: examples/leo/story.json
   :language: json

Generated Illustrations
-----------------------

Running the illustration generation stage (see :doc:`illustration_generation`)
on the segmented story produces one image per scene. Below is each scene with
its story text, illustration prompt, and generated image.

Scene 1
~~~~~~~

**Text:**
   Léo a cinq ans, et son trésor, c'est une petite voiture rouge qu'il ne
   quitte jamais. Ce matin-là, impossible de la trouver. Il cherche partout,
   soulève les coussins, regarde derrière les rideaux… jusqu'à ce qu'il
   l'aperçoive, cachée sous le canapé du salon. Son visage s'illumine quand il
   la récupère enfin.

**Prompt:**
   ``<LEO> kneels on the floor of the <LIVING_ROOM>, after searching everywhere, smiling with relief as he pulls his <TOY_CAR> from under the sofa.``

.. image:: examples/leo/illustrations/scene-001.png
   :alt: Léo finds his toy car under the sofa.
   :width: 80%
   :align: center

Scene 2
~~~~~~~

**Text:**
   Tout content, il file dans sa chambre pour jouer. Il fait rouler son bolide
   sur le parquet, invente des circuits autour des pieds de chaise et le long
   des bords du tapis. Les heures passent sans qu'il s'en rende compte.

**Prompt:**
   ``<LEO> plays in his bedroom, guiding his <TOY_CAR> across the parquet floor around chair legs and along the edge of a rug.``

.. image:: examples/leo/illustrations/scene-002.png
   :alt: Léo plays with his toy car in his bedroom.
   :width: 80%
   :align: center

Scene 3
~~~~~~~

**Text:**
   Quand la faim se fait sentir, Léo retourne au salon. Sa maman lui a préparé
   de bons gâteaux pour le goûter. Assis près d'elle, il les dévore avec
   appétit, sa petite voiture rouge serrée dans la main.

**Prompt:**
   ``<LEO> sits in the <LIVING_ROOM> at snack time, eating little cakes with appetite while holding his <TOY_CAR> tightly in one hand.``

.. image:: examples/leo/illustrations/scene-003.png
   :alt: Léo enjoys a snack with his mother in the living room.
   :width: 80%
   :align: center

