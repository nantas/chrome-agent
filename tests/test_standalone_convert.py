"""Regression: standalone fetch_and_convert SHALL apply preprocess cleanup.

Spec: fold-standalone-into-convert-mirror / standalone-orchestrator-delegates-
to-cv4-mirror, scenario fetch-subcommand-applies-preprocess.

Before folding, fetch_and_convert called convert_body directly, skipping
preprocess_html — so config-driven cleanup (strip_footer → #catlinks removal)
silently failed in the fetch/reprocess/reconvert subcommands while the
pipeline subcommand applied it. This test fails on that drift and passes once
fetch_and_convert delegates to convert_single_page (CV4 mirror).
"""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from scripts.pipeline import standalone

# Minimal wiki HTML: body content + a #catlinks block that strip_footer removes.
HTML = """<div class="mw-parser-output">
<p>The <b>Test Page</b> has <a href="/wiki/Link" title="Link">a link</a>.</p>
<div id="catlinks"><div id="mw-normal-catlinks">Categories:shouldBeRemoved</div></div>
</div>"""


class TestFetchAndConvertAppliesPreprocess(unittest.TestCase):
    def test_fetch_subcommand_strips_catlinks_under_strip_footer(self) -> None:
        """fetch_and_convert(mode='html') SHALL honor cleanup:['strip_footer']."""
        extraction_config = {"cleanup": ["strip_footer"]}

        # Mock the network layer: probe + ApiClient.parse (text + images).
        fake_client = MagicMock()
        fake_client.parse.side_effect = [
            {"parse": {"text": {"*": HTML}}},          # prop="text" call
            {"parse": {"images": []}},                  # prop="images" call
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "out.md")
            with patch("scripts.pipeline.standalone.probe_api_endpoint", return_value="https://example.wiki.gg/api.php"), \
                 patch("scripts.pipeline.standalone.ApiClient", return_value=fake_client):
                standalone.fetch_and_convert(
                    url="https://example.wiki.gg/wiki/Test_Page",
                    domain="example.wiki.gg",
                    output=output,
                    mode="html",
                    extraction_config=extraction_config,
                )
            with open(output, "r", encoding="utf-8") as f:
                content = f.read()

        # #catlinks content MUST be stripped (preprocess_html ran).
        self.assertNotIn(
            "shouldBeRemoved",
            content,
            "preprocess drift: fetch_and_convert did not apply strip_footer cleanup "
            "(#catlinks survived) — did it skip preprocess_html?",
        )


if __name__ == "__main__":
    unittest.main()
