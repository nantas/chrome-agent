"""Mirror equivalence proofs for the convert capability (ADR 0013 §4.3).

Declared in docs/architecture/00-target-architecture.md §3.1: the three
convert mirrors (CV3 explore, CV4 pipeline, CV5 pipeline-cdp) SHALL produce
output identical to the shared kernel (CV1, lib/extraction/converter.py)
for the same HTML input. Golden-snapshot style: same fixture in, assert
same Markdown out — any diff is drift between kernel and mirror.

Self-contained: the fixture is embedded, no .cache dependency, never skips.

Mirrors add declared path-specific wrapping around the conversion core:
- CV3 `_apply_extraction`: config-driven post-ops (all inert under the
  minimal ruleset used here, so output must equal the kernel byte-for-byte).
- CV4 `convert_single_page`: YAML frontmatter + title heading around the
  body; the test strips that declared wrapping before comparing.
- CV5 generic path: no extraction config; equivalent to the kernel invoked
  with empty rules.
"""

from __future__ import annotations

import unittest

from scripts.lib.extraction.converter import convert_html_to_markdown, convert_page_full
from scripts.explore.sample_converter import _apply_extraction
from scripts.pipeline.pipeline.phases.convert import convert_single_page
from scripts.pipeline.strategies import (
    ExactTitleLinkResolver,
    SimpleSubstitutionTemplateProcessor,
)

DOMAIN = "example.wiki.gg"
TITLE = "Bloody Gust"

# Minimal ruleset: base_url lets the kernel derive wiki_domain; every
# other config-driven post-op (infobox, normalization, url_conversion)
# is absent. cleanup=["strip_footer"] is included deliberately: only
# preprocess_html removes #catlinks (the converter kernel does not), so
# a mirror that skips preprocess_html fails this test.
RULES = {
    "image_handling": {"base_url": f"https://{DOMAIN}"},
    "cleanup": ["strip_footer"],
}

# Representative MediaWiki page body: /wiki/ link, external link, heading,
# table with rowspan/colspan, list, image.
HTML = """<div class="mw-parser-output">
<p>The <b>Bloody Gust</b> is a <a href="/wiki/Sword" title="Sword">sword</a> item.
See <a href="https://example.com/guide">the guide</a> for details.</p>
<h2><span class="mw-headline" id="Stats">Stats</span></h2>
<table class="wikitable">
<tr><th>Name</th><th>Damage</th><th>Notes</th></tr>
<tr><td rowspan="2">Gust</td><td>10</td><td>Fast</td></tr>
<tr><td colspan="2">Sweeping</td></tr>
</table>
<ul><li>First effect</li><li>Second effect</li></ul>
<p><img src="/images/thumb/Bloody_Gust.png/32px-Bloody_Gust.png" alt="Bloody Gust" /></p>
<table class="navbox"><tr><td>Navigation noise</td></tr></table>
<div id="catlinks"><div id="mw-normal-catlinks">Categories noise</div></div>
</div>"""


def _unwrap_pipeline_body(content: str, title: str) -> str:
    """Strip CV4's declared wrapping (YAML frontmatter + title heading)."""
    body = content.split("---\n", 2)[2].lstrip("\n")
    prefix = f"# {title}\n"
    if not body.startswith(prefix):
        raise AssertionError(f"CV4 wrapping drift: body lacks '# {title}' heading")
    return body[len(prefix):].strip()


class TestConvertMirrorEquivalence(unittest.TestCase):
    def test_cv3_explore_mirror_matches_kernel(self) -> None:
        """explore/sample_converter._apply_extraction ≡ convert_page_full."""
        via_explore = _apply_extraction(HTML, RULES, set())
        via_kernel = convert_page_full(HTML, RULES)
        self.assertEqual(
            via_explore,
            via_kernel,
            "B-axis drift: explore sample_converter != convert kernel",
        )

    def test_cv4_pipeline_mirror_matches_kernel(self) -> None:
        """pipeline convert_single_page body ≡ convert_page_full."""
        result = convert_single_page(
            {"html": HTML},
            {"title": TITLE, "target_directory": ""},
            [],  # manifest_pages: empty link index, same as kernel's no-index
            DOMAIN,
            [],  # frontmatter_fields
            {},  # template_map
            ExactTitleLinkResolver(),
            SimpleSubstitutionTemplateProcessor(),
            RULES,
            {},  # redirect_map
        )
        self.assertEqual(result["status"], "ok", result.get("error"))
        via_pipeline = _unwrap_pipeline_body(result["content"], TITLE)
        via_kernel = convert_page_full(HTML, RULES).strip()
        self.assertEqual(
            via_pipeline,
            via_kernel,
            "B-axis drift: pipeline convert phase != convert kernel",
        )

    def test_cv5_generic_mirror_matches_kernel(self) -> None:
        """CDP generic path (wiki_domain="") ≡ kernel with empty rules."""
        via_cdp = convert_html_to_markdown(HTML, wiki_domain="")
        via_kernel = convert_page_full(HTML, {})
        self.assertEqual(
            via_cdp,
            via_kernel,
            "B-axis drift: generic CDP path != convert kernel",
        )


if __name__ == "__main__":
    unittest.main()
