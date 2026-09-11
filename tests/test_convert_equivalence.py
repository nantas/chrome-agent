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

from scripts.lib.extraction.converter import HtmlToMarkdownConverter, convert_html_to_markdown, convert_page_full
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
# table with rowspan/colspan, list, image — plus the character-level
# troublemakers from site KI records: pipe in table cell (kernel escapes
# to \|), literal asterisk (kernel does NOT escape; if it ever starts to,
# explore's unconditional escape-artifact cleanup diverges from pipeline
# and CV3 fails — intentional sentinel), parens in page title, image+link
# concatenation (KI-5), tooltip pair, apostrophe+colon title.
HTML = """<div class="mw-parser-output">
<p>The <b>Bloody Gust</b> is a <a href="/wiki/Sword" title="Sword">sword</a> item.
See <a href="https://example.com/guide">the guide</a> for details.</p>
<h2><span class="mw-headline" id="Stats">Stats</span></h2>
<table class="wikitable">
<tr><th>Name</th><th>Damage</th><th>Notes</th></tr>
<tr><td rowspan="2">Gust</td><td>10</td><td>+10% | speed</td></tr>
<tr><td colspan="2">Sweeping</td></tr>
</table>
<ul><li>First effect</li><li>Second effect</li></ul>
<p>Deals 3 * 5 damage with effect_chance. Grants [Flight].</p>
<p>See <a href="/wiki/Item_(DLC)" title="Item (DLC)">Item (DLC)</a> and
<a href="/wiki/Isaac%27s_Tears" title="Isaac's Tears">Isaac's Tears</a>.</p>
<p><img src="/images/thumb/Bloody_Gust.png/32px-Bloody_Gust.png" alt="Bloody Gust" /><a href="/wiki/Guppy" title="Guppy">Guppy</a></p>
<p><a href="/wiki/Brimstone" title="Brimstone"><span class="tooltip">Brimstone</span></a> text</p>
<table class="navbox"><tr><td>Navigation noise</td></tr></table>
<div id="catlinks"><div id="mw-normal-catlinks">Categories noise</div></div>
</div>"""


# Variant fixture that exercises the divergent post-op keys (text_normalization,
# url_conversion, youtube_cleanup, markdown-layer cleanup ops). Before the
# unify-convert-post-ops-into-kernel change, CV3 ran these on its output and
# CV4 did not — so a strategy using them produced divergent Markdown per
# execution path. This fixture binds CV3 ≡ CV4 ≡ kernel for real strategies.
HTML_POSTOPS = """<div class="mw-parser-output">
<p>See the <a href="/wiki/Sword">Sword</a>( ) and a <img src="/images/a.png" alt="A"/>image.</p>
<p>Load video
YouTube
Some player embed
ContinueDismiss</p>
<p>Adjacent <a href="/wiki/X">X</a><a href="/wiki/Y">Y</a> links.</p>
</div>"""

RULES_WITH_POSTOPS = {
    "image_handling": {"base_url": f"https://{DOMAIN}"},
    "cleanup": ["strip_footer", "strip_empty_parens", "fix_separators", "normalize_internal"],
    "text_normalization": ["fix_spaces", "normalize_blank_lines"],
    "url_conversion": {"enabled": True},
    "youtube_cleanup": {"enabled": True},
}


def _unwrap_pipeline_body(content: str, title: str) -> str:
    """Strip CV4's declared wrapping (YAML frontmatter + title heading).

    The title heading is conditional: _process_html_page only prepends
    `# {title}` when the converted body does not already start with a
    Markdown heading (a `#`-prefix check that also matches `##`). Strip
    it when present instead of asserting its presence.
    """
    body = content.split("---\n", 2)[2].lstrip("\n")
    prefix = f"# {title}\n"
    if body.startswith(prefix):
        body = body[len(prefix):]
    return body.strip()


class TestConvertMirrorEquivalence(unittest.TestCase):
    def test_enabled_infobox_survives_pipeline(self):
        html = '<aside class="portable-infobox"><div class="pi-data"><h3 class="pi-data-label">Seed Chance</h3><div class="pi-data-value">7.14%</div></div></aside><p>Body</p>'
        rules = {**RULES_WITH_POSTOPS, "infobox": {"enabled": True, "selector": ".portable-infobox"}}
        result = convert_single_page(
            {"html": html, "content_acquisition": "html_rendered"},
            {"title": TITLE, "target_directory": ""}, [], DOMAIN, [], {},
            ExactTitleLinkResolver(), SimpleSubstitutionTemplateProcessor(), rules, {})
        body = _unwrap_pipeline_body(result["content"], TITLE)
        for marker in ("## Infobox", "Seed Chance", "7.14%"):
            self.assertEqual(body.count(marker), 1, marker)
        self.assertEqual(body, convert_page_full(html, rules).strip())

    def test_infobox_uses_link_index_and_redirects(self):
        html = '<aside class="portable-infobox"><div class="pi-data"><h3 class="pi-data-label">Unlock</h3><div class="pi-data-value"><a href="/wiki/Old">Ending</a></div></div></aside><p>Body</p>'
        rules = {"infobox": {"enabled": True, "selector": ".portable-infobox"}}
        pages = [{"title": "Ending", "target_directory": "endings", "target_filename": "index.md"}]
        converter = HtmlToMarkdownConverter(DOMAIN, rules)
        converter.build_link_index(pages, {"Old": "Ending"})
        md = convert_page_full(html, rules, converter=converter, source_dir="bosses")
        self.assertIn('[Ending](../endings/index.md)', md)

    def test_infobox_base_url_overrides_context(self):
        html = '<aside class="portable-infobox"><div class="pi-data"><h3 class="pi-data-label">Site</h3><div class="pi-data-value"><a href="/guide">Guide</a></div></div></aside>'
        rules = {"image_handling": {"base_url": "https://other.example/"}, "infobox": {"enabled": True}}
        converter = HtmlToMarkdownConverter(DOMAIN, rules)
        self.assertIn("https://other.example/guide", convert_page_full(html, rules, converter=converter))

    def test_context_validation_and_absent_infobox(self):
        rules = {"infobox": {"enabled": True}}
        self.assertEqual(convert_page_full('<p>Body</p>', rules), 'Body')
        with self.assertRaises(ValueError):
            convert_page_full('<p>Body</p>', rules, converter=HtmlToMarkdownConverter(DOMAIN, {}))

    def test_infobox_handler_and_table_selector(self):
        html = '<table class="info"><tr data-source="count"><th>Count</th><td><img src="/a.png"/><img src="/b.png"/></td></tr></table><p>Body</p>'
        rules = {"infobox": {"enabled": True, "selector": "table.info", "field_selector": "tr", "label_selector": "th", "value_selector": "td"}, "infobox_field_handlers": {"count": {"handler": "count_images"}}}
        self.assertIn('| Count | 2 |', convert_page_full(html, rules))

    def test_infobox_configuration_controls_extraction_without_duplicates(self):
        html = '<aside class="portable-infobox"><div class="pi-data"><h3 class="pi-data-label">Seed Chance</h3><div class="pi-data-value">7.14%</div></div></aside>'
        for rules in ({}, {"infobox": {"enabled": False}}, {"infobox": {"enabled": True}}):
            with self.subTest(rules=rules):
                result = convert_page_full(html, rules)
                self.assertEqual(result.count('Seed Chance'), 1)
                self.assertEqual(result.count('7.14%'), 1)
                self.assertEqual('## Infobox' in result, rules.get('infobox', {}).get('enabled', False))

    def test_cv3_explore_mirror_matches_kernel(self) -> None:
        """explore/sample_converter._apply_extraction ≡ convert_page_full."""
        via_explore = _apply_extraction(HTML, RULES, set())
        via_kernel = convert_page_full(HTML, RULES)
        self.assertEqual(
            via_explore,
            via_kernel,
            "B-axis drift: explore sample_converter != convert kernel",
        )

    def test_cv3_explore_matches_kernel_with_postops(self) -> None:
        """CV3 ≡ kernel for a strategy that enables the divergent post-op keys.

        Before unify-convert-post-ops-into-kernel, CV3 inlined the post-ops
        while convert_page_full did not, so this would fail. Now both route
        through convert_page_full → apply_post_conversion_ops.
        Spec: cv3-and-cv4-honor-same-post-ops-for-real-strategies.
        """
        via_explore = _apply_extraction(HTML_POSTOPS, RULES_WITH_POSTOPS, set())
        via_kernel = convert_page_full(HTML_POSTOPS, RULES_WITH_POSTOPS)
        self.assertEqual(
            via_explore,
            via_kernel,
            "B-axis drift: explore != kernel when post-op keys are enabled",
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

    def test_cv4_pipeline_mirror_matches_kernel_with_postops(self) -> None:
        """CV4 ≡ kernel for a strategy that enables the divergent post-op keys.

        Before unify-convert-post-ops-into-kernel, CV4 skipped post-ops while
        the kernel (via convert_page_full) ran them — so pipeline production
        output diverged from explore samples for these strategies. This is
        the core evidence of the defect: it FAILS until CV4 calls
        apply_post_conversion_ops.
        Spec: cv3-and-cv4-honor-same-post-ops-for-real-strategies.
        """
        result = convert_single_page(
            {"html": HTML_POSTOPS},
            {"title": TITLE, "target_directory": ""},
            [],
            DOMAIN,
            [],
            {},
            ExactTitleLinkResolver(),
            SimpleSubstitutionTemplateProcessor(),
            RULES_WITH_POSTOPS,
            {},
        )
        self.assertEqual(result["status"], "ok", result.get("error"))
        via_pipeline = _unwrap_pipeline_body(result["content"], TITLE)
        via_kernel = convert_page_full(HTML_POSTOPS, RULES_WITH_POSTOPS).strip()
        self.assertEqual(
            via_pipeline,
            via_kernel,
            "B-axis drift: pipeline != kernel when post-op keys are enabled "
            "(CV4 must call apply_post_conversion_ops)",
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


class TestInfoboxPoolTargets(unittest.TestCase):
    def test_dedup_keeps_distinct_targets_with_same_label(self):
        rules = {'infobox': {'enabled': True}, 'infobox_field_handlers': {'pool': {'handler': 'dedup_pools'}}}
        html = '<aside class="portable-infobox"><div class="pi-data" data-source="pool"><h3 class="pi-data-label">Pools</h3><div class="pi-data-value"><a href="/wiki/Normal">Pool</a><a href="/wiki/Greed">Pool</a><a href="/wiki/Normal">Pool</a></div></div></aside>'
        md = convert_page_full(html, rules)
        self.assertEqual(md.count('/wiki/Normal'), 1)
        self.assertEqual(md.count('/wiki/Greed'), 1)

if __name__ == "__main__":
    unittest.main()
