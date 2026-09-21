Le Procédé
==========

Transformer une simple histoire textuelle en un livre illustré harmonieux requiert une méthode progressive. Dans ``librito``, cette transformation se déroule en plusieurs étapes bien délimitées, assurant à la fois la fidélité au récit d'origine et la cohérence esthétique de l'ouvrage final.

Voici les six étapes fondamentales de ce procédé :

1. Le découpage narratif (segmentation)
---------------------------------------

Le procédé débute avec l'histoire brute. Cette première étape consiste à analyser le texte pour le découper en moments narratifs forts et visuellement porteurs : les **scènes**.

* Chaque scène correspond à un temps fort du récit qui mérite d'être illustré.
* Le texte de l'histoire est réparti de manière équilibrée pour constituer les futures pages de lecture.
* Les éléments d'encadrement sont également pensés dès cette étape : le texte d'accroche pour la quatrième de couverture, d'éventuelles dédicaces ou des textes de clôture.

2. L'identification des concepts récurrents
-------------------------------------------

Pour qu'un livre illustré soit crédible, les personnages, les animaux, les objets significatifs ou les lieux remarquables doivent rester immédiatement reconnaissables tout au long de l'ouvrage.

* Lors de cette étape, tous les éléments visuels récurrents sont répertoriés.
* Chaque élément reçoit une balise canonique (par exemple ``<RENARD>`` ou ``<CHAPEAU_BLEU>``).
* Une description physique détaillée et stable est rédigée pour chacun d'entre eux, fixant leurs caractéristiques distinctives (traits, vêtements, couleurs, proportions).
* Enfin, chaque concept est rattaché aux scènes précises dans lesquelles il doit intervenir.

3. Définition du style et création des artworks de référence
------------------------------------------------------------

Avant de lancer la production des illustrations du livre, l'établissement de la direction artistique et des repères visuels constitue un préalable indispensable :

* **Choix du style global** : Définition d'un univers plastique (par exemple une gouache douce sur papier texturé, des traits vifs au crayon de couleur ou des aplats modernes).
* **Génération des artworks** : Pour chaque concept récurrent identifié, une illustration de référence isolée (un *artwork*) est générée conformément au style retenu.
* Ces artworks servent d'ancres visuelles enregistrées dans l'espace de travail : ils constituent la référence graphique concrète requise pour aborder l'étape d'illustration.

4. Conception des prompts d'illustration
----------------------------------------

Une fois les concepts définis et leurs artworks créés, chaque scène fait l'objet d'un travail de mise en scène :

* Un *prompt* (description textuelle destinée au modèle d'illustration) est rédigé pour chaque scène et chaque couverture.
* Le prompt intègre les balises d'ancrage des concepts (comme ``<RENARD>``) et se concentre sur **l'action, l'émotion, le cadrage et l'interaction** avec le décor.
* Cette approche permet de concentrer l'effort sur la narration visuelle, les balises reliant directement les protagonistes de la scène à leurs références visuelles respectives.

5. Génération des illustrations finales
---------------------------------------

C'est à cette étape que les images définitives du livre prennent vie :

* Le système associe le prompt de mise en scène, le style global et les artworks de référence des concepts intervenant dans l'image.
* Les artworks de référence sont fournis au modèle d'image accompagnés d'un inventaire ordonné des concepts de la scène et d'instructions de composition originale, garantissant la fidélité des sujets dans une composition entièrement nouvelle.
* Chaque scène reçoit son illustration en pleine page, de même que les différentes couvertures et pages intérieures illustrées.

6. Assemblage du livre
----------------------

La dernière étape réunit l'ensemble des éléments textuels et visuels dans un livre achevé :

* Les pages de texte et les illustrations correspondantes sont combinées en vis-à-vis pour former des doubles-pages équilibrées.
* La couverture, les pages liminaires (page de titre, dédicace) et la quatrième de couverture sont ordonnées selon les règles de mise en page éditoriale.
* L'ensemble est compilé dans un fichier au format EPUB à mise en page fixe (*fixed-layout*), garantissant que le livre sera restitué fidèlement sur les liseuses et écrans de lecture.