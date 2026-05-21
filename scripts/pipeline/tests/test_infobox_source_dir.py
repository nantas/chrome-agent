"""Unit tests for infobox source_dir passthrough.

Spec: infobox-link-source-dir-passthrough (3 scenarios).
Change: openspec/changes/infobox-link-source-dir-fix
"""

from __future__ import annotations

import inspect
import unittest
from unittest.mock import MagicMock, call

from selectolax.parser import HTMLParser

from scripts.lib.extraction.infobox import extract_infobox, _extract_selectolax


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_infobox_html(
    label="Ending",
    value_text="Ending 18",
    value_href="/wiki/Ending_18",
):
    # Build a minimal portable-infobox HTML fragment.
    return (
        '<aside class="portable-infobox">'
        '<div class="pi-data" data-source="ending">'
        '<h3 class="pi-data-label">{label}</h3>'
        '<div class="pi-data-value">'
        '<a href="{href}">{text}</a>'
        '</div>'
        '</div>'
        '</aside>'
    ).format(label=label, href=value_href, text=value_text)


def _parse_node(html):
    # Parse HTML and return the portable-infobox node.
    parser = HTMLParser(html)
    return parser.css_first("aside.portable-infobox")


# ---------------------------------------------------------------------------
# Scenario 1: infobox-link-uses-correct-relative-path
#   source_dir=bosses should cause render_inline_children_fn to receive
#   source_dir=bosses, enabling correct ../endings/... relative paths.
# ---------------------------------------------------------------------------

class TestSourceDirCrossDirectory(unittest.TestCase):

    def test_selectolax_passes_source_dir_to_render_fn(self):
        node = _parse_node(_make_infobox_html())
        mock_render = MagicMock(return_value="Ending 18")

        _extract_selectolax(
            node,
            selector="aside.portable-infobox",
            field_sel="div.pi-data",
            label_sel="h3.pi-data-label",
            value_sel="div.pi-data-value",
            nav_strip_selectors=[],
            handlers={},
            wiki_domain="wiki.gg",
            config={},
            source_dir="bosses",
            render_inline_children_fn=mock_render,
        )

        label_node = node.css_first("h3.pi-data-label")
        value_node = node.css_first("div.pi-data-value")
        expected_label_call = call(label_node, source_dir="bosses")
        expected_value_call = call(value_node, source_dir="bosses")
        self.assertIn(expected_label_call, mock_render.call_args_list)
        self.assertIn(expected_value_call, mock_render.call_args_list)

    def test_extract_infobox_with_source_dir_selectolax(self):
        node = _parse_node(_make_infobox_html())
        mock_render = MagicMock(return_value="Ending 18")

        result = extract_infobox(
            node,
            config={},
            wiki_domain="wiki.gg",
            parser="selectolax",
            source_dir="bosses",
            field_selector="div.pi-data",
            label_selector="h3.pi-data-label",
            value_selector="div.pi-data-value",
            render_inline_children_fn=mock_render,
        )

        self.assertIn("## Infobox", result)
        for c in mock_render.call_args_list:
            self.assertEqual(c.kwargs.get("source_dir"), "bosses")


# ---------------------------------------------------------------------------
# Scenario 2: infobox-link-same-directory
#   source_dir defaults to empty string; same-dir links need no prefix.
# ---------------------------------------------------------------------------

class TestSourceDirEmptyDefault(unittest.TestCase):

    def test_default_source_dir_is_empty_string(self):
        node = _parse_node(_make_infobox_html())
        mock_render = MagicMock(return_value="Item")

        _extract_selectolax(
            node,
            selector="aside.portable-infobox",
            field_sel="div.pi-data",
            label_sel="h3.pi-data-label",
            value_sel="div.pi-data-value",
            nav_strip_selectors=[],
            handlers={},
            wiki_domain="wiki.gg",
            config={},
            render_inline_children_fn=mock_render,
        )

        for c in mock_render.call_args_list:
            self.assertEqual(c.kwargs.get("source_dir"), "")

    def test_explicit_empty_source_dir(self):
        node = _parse_node(_make_infobox_html())
        mock_render = MagicMock(return_value="Item")

        _extract_selectolax(
            node,
            selector="aside.portable-infobox",
            field_sel="div.pi-data",
            label_sel="h3.pi-data-label",
            value_sel="div.pi-data-value",
            nav_strip_selectors=[],
            handlers={},
            wiki_domain="wiki.gg",
            config={},
            source_dir="",
            render_inline_children_fn=mock_render,
        )

        for c in mock_render.call_args_list:
            self.assertEqual(c.kwargs.get("source_dir"), "")


# ---------------------------------------------------------------------------
# Scenario 3: bs4-path-unaffected
#   BS4 path should not use source_dir -- behavior unchanged from before.
# ---------------------------------------------------------------------------

class TestBS4PathUnaffected(unittest.TestCase):

    def test_bs4_path_ignores_source_dir(self):
        html = _make_infobox_html()

        result_no_dir = extract_infobox(
            html,
            config={},
            wiki_domain="wiki.gg",
        )

        result_with_dir = extract_infobox(
            html,
            config={},
            wiki_domain="wiki.gg",
            source_dir="bosses",
        )

        # Both should produce identical output
        self.assertEqual(result_no_dir, result_with_dir)

    def test_bs4_signature_no_source_dir_param(self):
        sig = inspect.signature(_extract_bs4)
        param_names = list(sig.parameters.keys())
        self.assertNotIn("source_dir", param_names)


# Need to import _extract_bs4 for signature check
from scripts.lib.extraction.infobox import _extract_bs4


if __name__ == "__main__":
    unittest.main()
