La Base de Données
==================

Pour que chaque projet de livre soit autonome et facilement consultable, ``librito`` organise l'ensemble des fichiers au sein d'un répertoire dédié appelé la **base de données** (le dossier ``database/`` à la racine du projet).

Cette section vous aide à comprendre comment sont organisés les fichiers pour chaque histoire et quel est le rôle de chacun de ces éléments.

Organisation par histoire
-------------------------

Chaque livre possède son propre sous-dossier dans ``database/``, nommé d'après un identifiant simple et standardisé (en minuscules, sans espaces ni caractères spéciaux, par exemple ``database/mon_histoire/``).

Ce répertoire rassemble tous les artefacts produits tout au long de la création du livre, de la première ébauche de texte jusqu'au fichier électronique final.

Anatomie d'un projet d'histoire
-------------------------------

À l'intérieur du dossier d'une histoire (par exemple ``database/mon_histoire/``), vous trouverez l'arborescence suivante :

.. code-block:: text

   database/mon_histoire/
   ├── story.md
   ├── story.json
   ├── units.json
   ├── artworks/
   │   ├── concept_01.png
   │   └── ...
   ├── illustrations/
   │   ├── scene_001.png
   │   └── ...
   └── story.epub

Voici la fonction de chacun de ces fichiers et dossiers :

* **``story.md`` (Histoire source)**
  Le document initial contenant le texte brut de l'histoire tel que fourni par l'auteur ou l'utilisateur.

* **``story.json`` (Storybook canonique)**
  Le document central décrivant l'architecture complète du livre : métadonnées, direction artistique, concepts récurrents, découpage des scènes et prompts d'illustration. C'est le plan de fabrication manipulé à chaque étape du procédé.

* **``artworks/`` (Dossier des artworks de référence)**
  Ce sous-répertoire conserve les images de référence créées pour chaque concept récurrent (les personnages, les décors ou les objets importants) ainsi que l'éventuelle référence du style graphique. Ces images servent de points d'ancrage visuels pour garantir la continuité du dessin.

* **``illustrations/`` (Dossier des illustrations finales)**
  Ce sous-répertoire regroupe toutes les illustrations destinées aux scènes du livre, aux couvertures et aux pages intérieures une fois générées.

* **``story.epub`` (Livre assemblé)**
  L'ouvrage final terminé, prêt à être diffusé ou lu. Ce fichier au format standard EPUB réunit la mise en page, les typographies, les textes et les illustrations.

* **``units.json`` (Unités narratives)**
  Un fichier intermédiaire découpant l'histoire d'origine en unités sémantiques minimales. Il est principalement utilisé en coulisses pour vérifier que le découpage en scènes n'a oublié aucun élément narratif important du récit d'origine.