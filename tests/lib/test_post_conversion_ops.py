"""Unit tests for apply_post_conversion_ops — the single kernel source of truth
for config-driven markdown-layer post-conversion transforms.

Spec: unify-convert-post-ops-into-kernel / convert-kernel-three-layer-interface,
scenario post-ops-have-one-implementation-in-kernel.

Each test exercises one config key's on/off behavior. The function is a pure
md-transform: md in → md out, no I/O, no self state.
"""

from __future__ import annotations

import unittest

from scripts.lib.extraction.converter import apply_post_conversion_ops

BASE_URL = "https://example.wiki.gg"


class TestTextNormalization(unittest.TestCase):
    def test_fix_spaces_inserts_space_between_letter_and_digit(self) -> None:
        md = "effect_chance50and more"
        out = apply_post_conversion_ops(md, {"text_normalization": ["fix_spaces"]})
        self.assertIn("effect_chance 50 and", out)

    def test_fix_spaces_inserts_space_between_adjacent_images(self) -> None:
        md = "![a](x.png)![b](y.png)"
        out = apply_post_conversion_ops(md, {"text_normalization": ["fix_spaces"]})
        self.assertIn("![a](x.png) ![b](y.png)", out)

    def test_fix_spaces_off_when_key_absent(self) -> None:
        md = "effect_chance50"
        out = apply_post_conversion_ops(md, {"text_normalization": []})
        self.assertEqual(out, md)

    def test_normalize_blank_lines_collapses_three_or_more(self) -> None:
        md = "para\n\n\n\nmore"
        out = apply_post_conversion_ops(md, {"text_normalization": ["normalize_blank_lines"]})
        self.assertEqual(out, "para\n\nmore")

    def test_deduplicate_words_removes_repeated_capitalized_phrase(self) -> None:
        md = "Bloody Gust Bloody Gust item"
        out = apply_post_conversion_ops(md, {"text_normalization": ["deduplicate_words"]})
        self.assertNotIn("Bloody Gust Bloody Gust", out)

    def test_empty_header_removed_unconditionally(self) -> None:
        md = "intro\n## \nbody"
        out = apply_post_conversion_ops(md, {})
        self.assertNotIn("## \n", out)


class TestUrlConversion(unittest.TestCase):
    def test_url_conversion_rewrites_relative_image_and_wiki_links(self) -> None:
        md = "![alt](/images/a.png) and [page](/wiki/Page)"
        out = apply_post_conversion_ops(
            md,
            {"url_conversion": {"enabled": True}, "image_handling": {"base_url": BASE_URL}},
        )
        self.assertIn(f"![alt]({BASE_URL}/images/a.png)", out)
        self.assertIn(f"[page]({BASE_URL}/wiki/Page)", out)

    def test_url_conversion_noop_when_disabled(self) -> None:
        md = "![alt](/images/a.png)"
        out = apply_post_conversion_ops(
            md,
            {"url_conversion": {"enabled": False}, "image_handling": {"base_url": BASE_URL}},
        )
        self.assertEqual(out, md)

    def test_url_conversion_noop_when_no_base_url(self) -> None:
        md = "![alt](/images/a.png)"
        out = apply_post_conversion_ops(md, {"url_conversion": {"enabled": True}})
        self.assertEqual(out, md)


class TestYoutubeCleanup(unittest.TestCase):
    def test_youtube_cleanup_removes_embed_block(self) -> None:
        md = "intro\nLoad video\nYouTube\nblah\nContinueDismiss\nrest"
        out = apply_post_conversion_ops(md, {"youtube_cleanup": {"enabled": True}})
        self.assertNotIn("Load video", out)
        self.assertNotIn("ContinueDismiss", out)
        self.assertIn("intro", out)
        self.assertIn("rest", out)

    def test_youtube_cleanup_noop_when_disabled(self) -> None:
        md = "Load video\nYouTube\nx\nContinueDismiss"
        out = apply_post_conversion_ops(md, {"youtube_cleanup": {"enabled": False}})
        self.assertIn("ContinueDismiss", out)


class TestEscapeArtifactCleanup(unittest.TestCase):
    def test_unescape_triple_star(self) -> None:
        self.assertEqual(apply_post_conversion_ops(r"a \*\*\* b", {}), "a *** b")

    def test_unescape_star_runs(self) -> None:
        self.assertEqual(apply_post_conversion_ops(r"a \*\* b \* c", {}), "a ** b * c")


class TestCleanupOps(unittest.TestCase):
    def test_strip_empty_parens(self) -> None:
        md = "text () and ( ) end"
        out = apply_post_conversion_ops(md, {"cleanup": ["strip_empty_parens"]})
        self.assertNotIn("()", out)

    def test_fix_separators_inserts_space_between_adjacent_links(self) -> None:
        md = "![a](x.png)[b](y.md)"
        out = apply_post_conversion_ops(md, {"cleanup": ["fix_separators"]})
        self.assertIn("![a](x.png) [b](y.md)", out)

    def test_fix_separators_collapses_multiple_spaces(self) -> None:
        md = "a   b"
        out = apply_post_conversion_ops(md, {"cleanup": ["fix_separators"]})
        self.assertEqual(out, "a b")

    def test_normalize_internal_rewrites_root_wiki_links(self) -> None:
        md = "[page](/wiki/Page)"
        out = apply_post_conversion_ops(
            md,
            {"cleanup": ["normalize_internal"], "image_handling": {"base_url": BASE_URL}},
        )
        self.assertIn(f"[page]({BASE_URL}/wiki/Page)", out)

    def test_cleanup_ops_off_when_key_absent(self) -> None:
        md = "text () end"
        out = apply_post_conversion_ops(md, {"cleanup": []})
        self.assertIn("()", out)


class TestIdempotenceAndNoConfig(unittest.TestCase):
    def test_no_config_returns_input_unchanged_except_escape_cleanup(self) -> None:
        # escape-artifact cleanup is unconditional; everything else is gated.
        md = "plain text with /wiki/x link and () parens"
        out = apply_post_conversion_ops(md, {})
        self.assertEqual(out, md)

    def test_output_is_stripped(self) -> None:
        md = "  \n  content  \n  "
        out = apply_post_conversion_ops(md, {})
        self.assertEqual(out, "content")


if __name__ == "__main__":
    unittest.main()
