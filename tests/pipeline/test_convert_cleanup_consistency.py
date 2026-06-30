"""Regression: pipeline HTML conversion MUST execute cleanup ops like explore.

Architecture invariant (per docs/architecture/05-converter-architecture.md):
explore sampling and pipeline conversion must behave consistently, so that
explore sample output can serve as a quality proxy for pipeline production.

This was broken: cleanup ops (e.g. strip_fandom_infobox_tables) ran only in
explore's preprocessor, never in pipeline's _process_html_page. The result:
samples looked clean while pipeline output retained noise — quality gate
conclusions did not reflect pipeline reality.
"""

import unittest

from scripts.pipeline.pipeline.phases.convert import _process_html_page
from scripts.explore.sample_converter import _apply_extraction

# Fandom-style portable infobox table + body paragraph
INFBOX_HTML = """<html><body>
<table class="portable-infobox"><tr><th>Infobox</th></tr><tr><td>SHOULD_BE_STRIPPED</td></tr></table>
<p>BodyParagraph</p>
</body></html>"""

CLEANUP_CONFIG = {
    "image_handling": {"base_url": "https://example.com"},
    "cleanup": ["strip_fandom_infobox_tables"],
}


class TestCleanupConsistency(unittest.TestCase):
    """explore (sample) and pipeline paths must apply cleanup ops identically."""

    def test_explore_path_strips_fandom_infobox(self):
        """Explore sample conversion strips the infobox table (baseline behaviour)."""
        md = _apply_extraction(INFBOX_HTML, CLEANUP_CONFIG, set())
        self.assertNotIn("SHOULD_BE_STRIPPED", md)
        self.assertIn("BodyParagraph", md)

    def test_pipeline_path_strips_fandom_infobox(self):
        """Pipeline conversion must also strip the infobox table, matching explore."""
        result = _process_html_page(
            {"html": INFBOX_HTML},
            title="TestPage",
            source_dir="",
            source_url="https://example.com/wiki/TestPage",
            domain="example.com",
            manifest_pages=[],
            frontmatter_fields=[],
            extraction_config=CLEANUP_CONFIG,
            redirect_map=None,
        )
        self.assertEqual(result["status"], "ok", f"conversion failed: {result}")
        self.assertNotIn(
            "SHOULD_BE_STRIPPED", result["content"],
            "pipeline did not strip infobox — cleanup ops not executed (explore/pipeline divergence)",
        )
        self.assertIn("BodyParagraph", result["content"])


if __name__ == "__main__":
    unittest.main()
