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


class TestReconvertFileWithoutSourceUrl(unittest.TestCase):
    """reconvert_file no-source_url branch SHALL use the kernel entry.

    Spec: fold-standalone-into-convert-mirror / scenario
    reconvert-without-source-url-uses-kernel-entry. The branch SHALL convert
    the body via convert_page_full (preprocess runs), not via direct
    clean_html+convert (preprocess skipped, #catlinks would survive).
    """

    def test_in_place_reconvert_applies_preprocess(self) -> None:
        frontmatter = "---\ntitle: Test Page\n---\n"
        body_html = (
            '<div class="mw-parser-output">'
            "<p>some content</p>"
            '<div id="catlinks"><div id="mw-normal-catlinks">Categories:shouldBeRemoved</div></div>'
            "</div>"
        )
        extraction_config = {"cleanup": ["strip_footer"]}

        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "page.md")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(frontmatter + body_html)

            standalone.reconvert_file(
                fpath, "example.wiki.gg", extraction_config=extraction_config,
            )

            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

        # #catlinks content MUST be stripped → body went through convert_page_full
        # (preprocess_html ran), not a bare clean_html+convert.
        self.assertNotIn(
            "shouldBeRemoved",
            content,
            "reconvert_file no-source_url branch did not route through "
            "convert_page_full — #catlinks survived, suggesting a regression "
            "to bare clean_html+convert.",
        )
        # Frontmatter preserved.
        self.assertIn("title: Test Page", content)


if __name__ == "__main__":
    unittest.main()

class TestStandaloneAdmission(unittest.TestCase):
    def test_api_challenge_never_becomes_markdown(self):
        from pathlib import Path
        html = (Path(__file__).parent / 'fixtures/challenge-wikigg.html').read_text()
        client = MagicMock()
        client.parse.side_effect = [{'parse':{'text':{'*':html}}}, {'parse':{'images':[]}}]
        with tempfile.TemporaryDirectory() as tmp, patch.object(standalone,'probe_api_endpoint',return_value='https://example.test/api.php'), patch.object(standalone,'ApiClient',return_value=client):
            output = str(Path(tmp)/'out.md')
            with self.assertRaisesRegex(RuntimeError, 'challenge_page'):
                standalone.fetch_and_convert('https://example.test/wiki/Bad','example.test',output)
            self.assertFalse(Path(output).exists())
