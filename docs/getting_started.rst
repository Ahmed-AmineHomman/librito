Démarrage Rapide
================

Cette section vous fournit les instructions nécessaires pour installer et utiliser ``librito`` afin de commencer rapidement à créer vos livres illustrés.

Pré-requis
----------

Pour utiliser ``librito``, assurez-vous de disposer des éléments suivants :

* **Python 3.11** ou une version plus récente.
* Un environnement d'exécution standard (terminal sous Linux, macOS ou Windows).
* Une méthode de génération pour le texte et les images. ``librito`` offre une architecture modulaire : vous pouvez utiliser une clé d'API pour des services distants (comme l'API Gemini, renseignée via une variable d'environnement ``GEMINI_API_KEY`` dans un fichier ``.env``) ou vous appuyer sur des modèles et alternatives locales.

Installation
------------

Pour installer ``librito`` et préparer votre environnement de travail :

1. Clonez le dépôt et placez-vous dans le répertoire du projet :

   .. code-block:: bash

      git clone https://github.com/Ahmed-AmineHomman/librito.git
      cd librito

2. Créez un environnement virtuel Python et activez-le :

   .. code-block:: bash

      python -m venv .venv
      source .venv/bin/activate

   *(Sous Windows PowerShell, utilisez : ``.\.venv\Scripts\Activate.ps1``)*

3. Installez les dépendances nécessaires :

   .. code-block:: bash

      pip install -r requirements.txt

Exemple d'utilisation
---------------------

Voici le déroulement typique pour transformer une histoire brute en un livre illustré prêt à la lecture :

1. **Initialisation de l'espace de travail**

   Chaque histoire est gérée dans un répertoire dédié sous ``database/``. Vous pouvez initialiser une nouvelle histoire avec le script d'initialisation :

   .. code-block:: bash

      python helpers/initialize.py mon_histoire

   Cette commande crée le dossier ``database/mon_histoire/`` avec les sous-répertoires requis.

2. **Écriture de l'histoire source**

   Placez le texte brut de votre histoire dans le fichier ``database/mon_histoire/story.md``.

3. **Création du storybook**

   Le fichier ``database/mon_histoire/story.json`` contient la structure complète du livre : métadonnées, style artistique, concepts récurrents, textes des scènes et descriptions pour l'illustration.

   Cette étape de structuration et de rédaction des descriptions est conçue pour être menée avec l'aide d'un assistant ou d'un agent d'intelligence artificielle, guidé par les principes méthodologiques de ``librito``.

4. **Génération des illustrations**

   Une fois le storybook complété et les références visuelles établies, lancez la génération des illustrations pour toutes les scènes et les couvertures :

   .. code-block:: bash

      python helpers/illustrate_story.py --story mon_histoire

   Les images générées sont automatiquement enregistrées dans le dossier ``database/mon_histoire/illustrations/``.

5. **Assemblage du livre**

   Rassemblez les textes, la mise en page et les illustrations au sein d'un livre électronique au format EPUB :

   .. code-block:: bash

      python helpers/assemble_book.py --story mon_histoire

6. **Lecture du résultat**

   Le livre final est généré sous le nom ``database/mon_histoire/story.epub``. Vous pouvez l'ouvrir avec n'importe quelle liseuse compatible EPUB (comme Foliate, Apple Books ou Calibre).