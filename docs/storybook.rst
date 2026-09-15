Le Storybook
============

Un *storybook* constitue le plan architectural et le document de référence d'un livre illustré dans ``librito``. Il rassemble toutes les informations nécessaires à la fabrication de l'ouvrage, depuis les métadonnées éditoriales jusqu'aux descriptions précises des illustrations.

Concrètement, le storybook est conservé sous la forme d'un fichier structuré (``story.json``) situé au cœur de chaque projet d'histoire. Il s'articule autour de cinq éléments fondamentaux : les métadonnées, le style artistique, les concepts récurrents, les parties du livre et les scènes.

Métadonnées générales
---------------------

Chaque livre débute par des métadonnées indispensables :

* **Titre** : Le titre officiel de l'histoire tel qu'il apparaîtra sur la couverture et dans les données de publication.
* **Auteur** : Le nom de l'auteur ou du créateur de l'histoire.

Style artistique global
-----------------------

Pour garantir que l'ensemble des illustrations du livre présente une atmosphère visuelle homogène, le storybook définit un style artistique unique :

* **Description du style** : Un paragraphe décrivant la technique graphique (aquarelle, linogravure, gouache, dessin au pastel, etc.), la palette de couleurs, le traitement de la lumière et l'ambiance générale.
* **Contraintes** : Des consignes spécifiques éventuelles pour orienter ou restreindre certains aspects visuels (par exemple l'absence de texte incrusté ou la simplification des arrière-plans).
* **Artwork de style** : Une image de référence illustrant le style choisi peut être associée au storybook afin de guider les étapes de génération visuelle.

Concepts récurrents
-------------------

Un livre illustré raconte une histoire à travers des éléments qui reviennent au fil des pages : des personnages principaux, des objets emblématiques ou des décors récurrents.

Dans le storybook, chaque élément récurrent est formalisé sous la forme d'un **concept** :

* **Une balise canonique** : Un identifiant unique encadré par des chevrons et écrit en majuscules (par exemple ``<PERSONNAGE_PRINCIPAL>``, ``<VEHICULE>`` ou ``<MAISON>``).
* **Une description visuelle stable** : Un texte précis décrivant l'apparence physique de l'élément (couleurs, vêtements, caractéristiques physiques, textures). Cette description ne change pas d'une page à l'autre pour assurer la continuité visuelle.
* **Une image de référence (*artwork*)** : Une illustration isolée du concept, générée préalablement, qui sert de point d'ancrage visuel pour toutes les apparitions futures du sujet.
* **La liste des scènes associées** : L'inventaire ordonné des scènes dans lesquelles ce concept intervient visuellement.

Parties du livre
----------------

En plus du récit lui-même, un livre imprimé ou relié comporte des éléments de structure qui encadrent la lecture :

* **Première de couverture (*front cover*)** : L'illustration de couverture, accompagnée du titre et du nom de l'auteur.
* **Page de titre (*title page*)** : La page d'ouverture reprenant le titre, l'auteur et éventuellement une vignette illustrée.
* **Quatrième de couverture (*back cover*)** : Le dos du livre, comprenant un texte d'accroche (résumé ou citation) et éventuellement une illustration.
* **Éléments complémentaires optionnels** : Le storybook permet d'intégrer des pages de garde (*endpapers*), un frontispice, une page de dédicace ou une illustration finale de clôture.

Les scènes
----------

Le corps du livre est constitué d'une suite ordonnée de scènes narratives. Chaque scène correspond dans le livre final à une double-page (le texte d'un côté, l'illustration en pleine page de l'autre).

Pour chaque scène, le storybook consigne :

* **Un identifiant** : Un libellé clair permettant de repérer facilement la scène dans la chronologie de l'histoire.
* **Le texte de l'histoire** : Le texte destiné au lecteur, rédigé dans la langue originale de l'histoire.
* **Le prompt d'illustration** : La description de la mise en scène, rédigée en intégrant les balises des concepts récurrents. Ce texte décrit ce qui se passe dans l'image, la posture des personnages, l'angle de vue et l'atmosphère du moment.
* **Le chemin de l'illustration** : L'emplacement de l'image finale générée correspondant à cette scène.