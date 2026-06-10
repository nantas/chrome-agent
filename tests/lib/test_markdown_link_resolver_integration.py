"""Integration tests for markdown_link_resolver in site sample conversion.

Verifies that ../Pages/Page_*.html links in converted Markdown are resolved
to full URLs when no page mapping exists (unmapped links scenario).
"""

import unittest


class TestLinkResolutionIntegration(unittest.TestCase):
    """Test that fix_all_links resolves ../Pages/Page_*.html patterns."""

    def test_resolves_page_links_to_full_urls(self):
        """../Pages/Page_*.html with empty mapping resolves to full URL."""
        from scripts.lib.markdown_link_resolver import fix_all_links

        md = "[4 Network Service](../Pages/Page_106359822.html) > [4.4 Status](../Pages/Page_159219887.html)"
        result = fix_all_links(md, {}, "https://developer.nintendo.com", "Account_Guide", uses_contents=True)

        self.assertNotIn("../Pages/Page_106359822.html", result)
        self.assertNotIn("../Pages/Page_159219887.html", result)
        self.assertIn("https://developer.nintendo.com/Account_Guide/contents/Pages/Page_106359822.html", result)
        self.assertIn("https://developer.nintendo.com/Account_Guide/contents/Pages/Page_159219887.html", result)

    def test_resolves_page_links_without_contents(self):
        """../Pages/Page_*.html without contents/ subdirectory."""
        from scripts.lib.markdown_link_resolver import fix_all_links

        md = "[link](../Pages/Page_123.html)"
        result = fix_all_links(md, {}, "https://example.com", "Manual", uses_contents=False)

        self.assertNotIn("../Pages/Page_123.html", result)
        self.assertIn("https://example.com/Manual/Pages/Page_123.html", result)

    def test_mapped_page_links_resolve_to_md(self):
        """../Pages/Page_*.html with mapping resolves to .md filename."""
        from scripts.lib.markdown_link_resolver import fix_all_links

        mapping = {"Pages/Page_123.html": "Page_123.md"}
        md = "[link](../Pages/Page_123.html)"
        result = fix_all_links(md, mapping, "https://example.com", "Guide", uses_contents=True)

        self.assertEqual(result, "[link](Page_123.md)")

    def test_leaves_absolute_urls_unchanged(self):
        """Absolute URLs pass through unchanged."""
        from scripts.lib.markdown_link_resolver import fix_all_links

        md = "[external](https://other.site.com/page)"
        result = fix_all_links(md, {}, "https://example.com", "Guide", uses_contents=True)

        self.assertEqual(result, md)

    def test_leaves_anchor_links_unchanged(self):
        """Anchor-only links pass through unchanged."""
        from scripts.lib.markdown_link_resolver import fix_all_links

        md = "[section](#heading)"
        result = fix_all_links(md, {}, "https://example.com", "Guide", uses_contents=True)

        self.assertEqual(result, md)

    def test_mixed_links_resolved_correctly(self):
        """Mix of Page links, absolute URLs, and anchors all resolve correctly."""
        from scripts.lib.markdown_link_resolver import fix_all_links

        md = (
            "[page](../Pages/Page_111.html) and "
            "[external](https://other.site.com) and "
            "[anchor](#section)"
        )
        result = fix_all_links(md, {}, "https://developer.nintendo.com", "Guide", uses_contents=True)

        self.assertNotIn("../Pages/", result)
        self.assertIn("https://other.site.com", result)
        self.assertIn("#section", result)

    def test_structural_assertion_passes_after_fix(self):
        """assert_links_resolved passes after applying fix_all_links."""
        from scripts.lib.markdown_link_resolver import fix_all_links
        from scripts.lib.test_assertions import assert_links_resolved

        md = "[4.4 Status](../Pages/Page_159219887.html)"
        fixed = fix_all_links(md, {}, "https://developer.nintendo.com", "Account_Guide", uses_contents=True)

        # Before fix: would fail
        with self.assertRaises(AssertionError):
            assert_links_resolved(md)

        # After fix: should pass
        assert_links_resolved(fixed)


if __name__ == "__main__":
    unittest.main()
