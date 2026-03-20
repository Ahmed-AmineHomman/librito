"""Tests for prompt construction."""

from __future__ import annotations

import unittest

from librito.models import StoryConstants, StoryScene, Storybook
from librito.prompt_builder import build_scene_prompt, expand_prompt_anchors


class PromptBuilderTests(unittest.TestCase):
    """Validate anchor expansion and prompt assembly."""

    def test_expand_prompt_anchors_replaces_known_anchors(self) -> None:
        """Known anchors should expand to bracketed descriptions."""

        expanded_prompt = expand_prompt_anchors(
            "<CALMIO> runs toward the river.",
            {"<CALMIO>": "A fluffy dog"},
        )

        self.assertEqual(expanded_prompt, "[A fluffy dog] runs toward the river.")

    def test_expand_prompt_anchors_rejects_unknown_anchors(self) -> None:
        """Unknown anchors should fail fast."""

        with self.assertRaisesRegex(ValueError, "Undefined recurring concept anchor"):
            expand_prompt_anchors("<MISSING> appears.", {"<CALMIO>": "A fluffy dog"})

    def test_build_scene_prompt_uses_style_template_and_constraints_resource(self) -> None:
        """The final prompt should combine style, expanded scene prompt, and constraints."""

        storybook = Storybook(
            title="Calmio",
            constants=StoryConstants(
                style="soft watercolor",
                recurring_concepts={"<CALMIO>": "A fluffy dog"},
            ),
            scenes=[
                StoryScene(
                    text="Calmio runs.",
                    prompt="<CALMIO> runs toward the river.",
                    image_path="",
                )
            ],
        )

        prompt = build_scene_prompt(storybook, storybook.scenes[0])

        self.assertIn("Style: soft watercolor", prompt)
        self.assertIn("Scene: [A fluffy dog] runs toward the river.", prompt)
        self.assertIn("single scene", prompt)
        self.assertIn("no visible text", prompt)


if __name__ == "__main__":
    unittest.main()
