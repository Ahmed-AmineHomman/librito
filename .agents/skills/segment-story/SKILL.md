---
name: segment-story
description: Analyzes a story provided by the user, extracts constants (characters, style), segments it into scenes, and generates a valid JSON object with story text and English image prompts. Use when ChatGPT must transform a user-provided story into a scene-by-scene structure for illustrated book generation, while enforcing the expected JSON schema and validating that the final output parses correctly as standard JSON.
---

This skill tells you how to segment a story, provided by the user, into scenes defined as a text (for the story) and an illustration description. The objective is to generate each illustration with an AI and assemble both texts and illustrations into an illustrated book. This operation is therefore the first step to transform the given story into a fully-fledged illustrated book.

The story may be provided by the user in any form supported by the conversation: pasted directly in the prompt, attached as a file, or otherwise supplied during the exchange. Always work from the story content actually provided by the user.

Therefore, you must transform the provided story into a set of successive scenes, with each scene being composed of:

* a text, describing the story in the scene,
* an image description, serving to generate the corresponding illustration.

This decomposition should be structured in the format described below.

## Workflow

* Read the story provided by the user thoroughly.
* Identify the recurring concepts in the story:
  * characters, along with their physical descriptions and clothing,
  * environments or settings,
  * objects, artifacts, etc.
* If not already provided by the user, identify a suiting art style for the illustrations.
* Define the story tags (see below) corresponding to all of the identified recurring concepts.
* Decompose the story into scenes. Ensure that:
  * global narrative is intact,
  * no important information is lost with the decomposition,
  * the story flow is preserved by the decomposition.
  You will probably have to drop some parts of the story in this exercise. This is acceptable. Just ensure that the missing parts do not hurt the overall story quality and flow.
* Write the scenes and their associated descriptions.
* Write the final JSON output.
* Before returning the result, verify that:
  * the output matches the expected schema exactly,
  * all required fields are present,
  * field types are correct,
  * the JSON parses correctly as standard JSON, with no trailing commas, comments, invalid quotes, or malformed structure.
* If the JSON is invalid, fix it before returning it.

## Style & Tag Definition

The art style must be defined once in the dedicated `style` field of the output. It should be a comprehensive description of the artistic style in English. Its value will be prefixed to all scene descriptions automatically when generating the illustrated book, in order to ensure style consistency across illustrations.

Tags allow to factorise the description of recurring concepts. They must be defined once in the `recurring_concepts` field of the output, and then represented as anchors in the scene illustrations. The anchors will be replaced by their corresponding description (the tag value) when generating the illustrated book.

The `constraints` field should be left empty by default. Default generation constraints (such as "single scene", "no visible text", "no frame or border") are applied automatically by the illustration generation pipeline. Only populate this field when the user explicitly requests additional or different constraints, or when the story imposes specific generation constraints not covered by the defaults.

The tags defined should be the following:

* `<[CONCEPT_NAME]>`: Detailed description of the corresponding concept (character, environment, object, etc.). Make sure environments are described generally enough to accommodate different rooms or angles if needed, while keeping a consistent aesthetic.

Descriptions of recurring concepts must be visually robust enough to ensure consistency across images. For recurring characters in particular, include stable visual attributes whenever they can be inferred or reasonably fixed for consistency: body type, age group, fur/skin tone, hair or fur color, eye color, clothing, and any distinctive markers. Avoid underspecified character descriptions that would let an image model reinvent the character differently from one scene to another.

Examples:

* `style`: "Children's watercolor illustration, soft strokes, pastel colors, warm and natural lighting".
* `<LEO>`: "5-year old male toddler wearing beige sports pants and a plain white t-shirt. He has very short black hair, brown eyes, fair skin with some freckles on his cheeks."

## Scene texts

The scene texts should be extracted from the story. They should preserve the story flow, and naturally follow each other. They should form a consistent and coherent narrative by their own (i.e. even if we stripped the illustrations from the book).

The texts should in addition be as close as possible to the initial story text, as long as it does not hurt the story flow and global consistency described below. Ideally, readers of the illustrated book should easily recognize the writing style of the original story.

**Texts should always be written in the language of the story**.

## Scene illustrations

Illustrations should represent the important part of their associated scene. They should not necessarily aim to represent every detail of the scene, or every action described. Instead, they should describe an image that can represent the main idea of the scene.

Illustrations should be described using the tags defined above. They should use the corresponding anchor whenever applicable, and avoid referencing story-related concepts without them. This guarantees visual consistency across the generated book.

Examples:

* OK: "<LEO> plays in his garden, with his <TOY_CAR>, during a sunny morning."
* NOK: "Leo plays in his garden, with his favorite car, during a sunny morning."

In the above NOK example, the AI generating the illustration will not know about Leo nor his favorite car, and will generate both concepts as it pleases, thus creating inconsistencies in the story (different representations of Leo and his car across scenes). In the OK example, both recurring concepts are represented with their respective anchors, and thus be replaced by their description (defined with the corresponding tag) at generation time.

**Prompts should always be written in English** (as it is the language best understood by AI image generation models).

## Expected JSON Output

The output must be a valid JSON object with exactly the following structure:

{
  "title": "Story title",
  "style": "Artistic style in English",
  "constraints": "",
  "recurring_concepts": {
    "<CONCEPT_NAME>": "Detailed concept description"
  },
  "scenes": [
    {
      "index": 1,
      "text": "Scene text in the language of the story",
      "prompt": "Scene illustration prompt in English",
      "image_path": ""
    }
  ]
}

## Output Validation Rules

Before returning the final answer, perform the following checks:

* The top-level value is a JSON object.
* The object contains exactly these top-level keys:
  * `title`
  * `style`
  * `constraints`
  * `recurring_concepts`
  * `scenes`
* `title` is a string.
* `style` is a string describing the artistic style in English.
* `constraints` is a string. It should be empty (`""`) unless the user or story requires specific constraints.
* `recurring_concepts` is an object mapping tag names to string descriptions.
* `scenes` is an array.
* Each element of `scenes` is an object containing exactly:
  * `index`, an integer (1-based position of the scene),
  * `text`, a string,
  * `prompt`, a string,
  * `image_path`, a string.
* `image_path` must be set to an empty string unless the user explicitly requests otherwise.
* All prompts are written in English.
* All scene texts are written in the language of the story.
* All recurring concepts referenced in prompts are defined in `recurring_concepts`.
* The final output must parse successfully as standard JSON.

If any of these checks fail, correct the JSON before returning it.

## Example

Below is a complete example of how to process an input story into the expected JSON output format. Do not wrap the final output in Markdown code blocks (like ```json) if saving directly to a file.

### Input Story

> Le matin, Léo cherchait son jouet préféré dans le salon lumineux de sa maison. Il finit par trouver sa petite voiture rouge sous le canapé.
> Ravi, le petit garçon courut dehors. Il passa des heures à faire rouler son bolide dans l'herbe haute du jardin sous un grand soleil.
> Quand l'heure du goûter arriva, Léo rentra dans la cuisine. Assis à la grande table en bois, il dévora ses biscuits.

### Expected JSON Output

{
  "title": "Léo et sa voiture rouge",
  "style": "Children's watercolor illustration, soft strokes, pastel colors, warm and natural lighting",
  "constraints": "",
  "recurring_concepts": {
    "<LEO>": "5-year old male toddler wearing beige sports pants and a plain white t-shirt. He has very short black hair, brown eyes, fair skin with some freckles on his cheeks.",
    "<TOY_CAR>": "Small bright red toy sports car with black wheels and a white racing stripe.",
    "<HOUSE>": "Cozy suburban house interior, featuring warm oak wood floors, white walls with pastel yellow accents, and large windows letting in natural sunlight."
  },
  "scenes": [
    {
      "index": 1,
      "text": "Le matin, Léo cherchait son jouet préféré dans le salon lumineux de sa maison. Il finit par trouver sa petite voiture rouge sous le canapé.",
      "prompt": "<LEO> is kneeling on the floor of the <HOUSE> living room, happily pulling a <TOY_CAR> from under a comfortable sofa.",
      "image_path": ""
    },
    {
      "index": 2,
      "text": "Ravi, le petit garçon courut dehors. Il passa des heures à faire rouler son bolide dans l'herbe haute du jardin sous un grand soleil.",
      "prompt": "<LEO> is playing outside in a bright sunny garden with tall green grass, enthusiastically pushing his <TOY_CAR> on the ground.",
      "image_path": ""
    },
    {
      "index": 3,
      "text": "Quand l'heure du goûter arriva, Léo rentra dans la cuisine. Assis à la grande table en bois, il dévora ses biscuits.",
      "prompt": "<LEO> is sitting at a large wooden table in the kitchen of the <HOUSE>, happily eating cookies.",
      "image_path": ""
    }
  ]
}