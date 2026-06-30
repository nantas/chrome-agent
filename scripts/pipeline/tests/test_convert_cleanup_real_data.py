"""L2 regression: pipeline HTML conversion on real bindingofisaacrebirth HTML.

Validates the C4 fix (pipeline runs preprocess_html before convert_body) on a
minimal subset of REAL wiki.gg HTML. Two assertions (Q5: A+B):
  A. cleanup 生效 — portable-infobox / mw-editsection removed from output
  B. 内容不丢 — body content (Effects, Speed) preserved

Golden snapshot: tests/fixtures/boa_bloody_gust_minimal.golden.md
Input fixture:   tests/fixtures/boa_bloody_gust_minimal.html (extracted from
                 .cache/mediawiki/bindingofisaacrebirth.wiki.gg/Bloody_Gust.json)

Why minimal subset, not full cache: the full 50KB cache is gitignored runtime
data; this fixture keeps the real DOM structure that triggers cleanup ops
(portable-infobox + mw-editsection h2 + figure, wrapped in .mw-parser-output)
while staying lightweight and self-contained.
"""

import unittest
from pathlib import Path

from scripts.pipeline.pipeline.phases.convert import _process_html_page

_REPO_ROOT = Path(__file__).resolve().parents[3]

FIXTURE_HTML = _REPO_ROOT / "tests" / "fixtures" / "boa_bloody_gust_minimal.html"
GOLDEN_MD = _REPO_ROOT / "tests" / "fixtures" / "boa_bloody_gust_minimal.golden.md"

# bindingofisaacrebirth extraction config (subset that drives cleanup ops)
EXTRACTION_CONFIG = {
    "selectors": {"body": ".mw-parser-output"},
    "cleanup": [
        "strip_edit_links",
        "strip_category_links",
        "strip_footer",
        "strip_skip_links",
        "convert_nested_images",
        "unwrap_image_wrappers",
    ],
    "image_filtering": {"skip_patterns": []},
}


class TestPipelineCleanupOnRealHTML(unittest.TestCase):
    """C4 verification on real wiki.gg HTML (minimal fixture subset)."""

    def setUp(self):
        self.assertTrue(FIXTURE_HTML.exists(), f"fixture missing: {FIXTURE_HTML}")
        self.assertTrue(GOLDEN_MD.exists(), f"golden missing: {GOLDEN_MD}")

    def test_cleanup_and_content_preserved(self):
        """Run _process_html_page on real fixture, assert A (cleanup) + B (content)."""
        html = FIXTURE_HTML.read_text(encoding="utf-8")
        result = _process_html_page(
            {"html": html, "rendered_html": html},
            title="Bloody_Gust",
            source_dir="",
            source_url="https://bindingofisaacrebirth.wiki.gg/wiki/Bloody_Gust",
            domain="bindingofisaacrebirth.wiki.gg",
            manifest_pages=[],
            frontmatter_fields=[],
            extraction_config=EXTRACTION_CONFIG,
            redirect_map=None,
        )
        md = result["content"]

        # A. cleanup 生效: these wiki structures must be stripped
        self.assertNotIn("portable-infobox", md, "portable-infobox not stripped")
        self.assertNotIn("mw-editsection", md, "mw-editsection not stripped")
        self.assertNotIn("[edit]", md, "edit link text not stripped")

        # B. 内容不丢: body content must survive preprocessing
        self.assertIn("Effects", md, "section heading lost")
        self.assertIn("Speed", md, "body content lost")
        self.assertIn("Fire Rate", md, "body content lost")

    def test_golden_snapshot(self):
        """Output matches recorded golden (regression baseline for C4)."""
        html = FIXTURE_HTML.read_text(encoding="utf-8")
        result = _process_html_page(
            {"html": html, "rendered_html": html},
            title="Bloody_Gust",
            source_dir="",
            source_url="https://bindingofisaacrebirth.wiki.gg/wiki/Bloody_Gust",
            domain="bindingofisaacrebirth.wiki.gg",
            manifest_pages=[],
            frontmatter_fields=[],
            extraction_config=EXTRACTION_CONFIG,
            redirect_map=None,
        )
        golden = GOLDEN_MD.read_text(encoding="utf-8")
        self.assertEqual(result["content"], golden,
                         "pipeline output drifted from golden — re-record with update_golden if C4 behavior changed")


if __name__ == "__main__":
    unittest.main()
