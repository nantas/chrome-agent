"""Mirror-equivalence golden snapshot: pipeline vs explore convert paths.

Spec: unify-html-converter / pipeline-convert-phase /
`mirror-equivalence-golden-snapshot`. The convert kernel SHALL produce
byte-identical output regardless of B-axis entry point (standalone
convert_html_to_markdown vs HtmlToMarkdownConverter.convert_body). This test
fails on any future drift between the two entry points.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.lib.extraction.converter import (
    HtmlToMarkdownConverter,
    convert_html_to_markdown,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# A cached wiki page used as the conversion sample. Skip if absent.
_CACHE = REPO_ROOT / ".cache" / "mediawiki" / "bindingofisaacrebirth.wiki.gg" / "Bloody_Gust.json"
_DOMAIN = "bindingofisaacrebirth.wiki.gg"


@unittest.skipIf(not _CACHE.exists(), f"no cached page at {_CACHE}")
class TestMirrorEquivalence(unittest.TestCase):
    def test_pipeline_and_explore_paths_produce_identical_md(self) -> None:
        data = json.loads(_CACHE.read_text(encoding="utf-8"))
        html = data.get("html", "")
        self.assertTrue(html, "cached page has empty html")

        # Path A — explore / standalone kernel entry
        via_explore = convert_html_to_markdown(html, wiki_domain=_DOMAIN)
        # Path B — pipeline / method entry
        via_pipeline = HtmlToMarkdownConverter(wiki_domain=_DOMAIN).convert_body(html)

        self.assertEqual(
            via_explore,
            via_pipeline,
            "B-axis drift: convert_html_to_markdown != HtmlToMarkdownConverter.convert_body",
        )


if __name__ == "__main__":
    unittest.main()
