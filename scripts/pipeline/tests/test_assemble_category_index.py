"""Unit tests for category index page generation in assemble phase."""

import os
import tempfile
import unittest

# Ensure repo root is importable for scripts.* imports
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import sys
sys.path.insert(0, _repo_root)


def _run_assemble(output_dir, manifest, results, strategy=None, domain="test.wiki.gg",
                  client=None):
    """Wrapper to call run_assemble with minimal stubs."""
    from unittest.mock import MagicMock
    from scripts.pipeline.strategies import LinkResolver, ListPageAssembler

    assembler = MagicMock(spec=ListPageAssembler)
    resolver = MagicMock(spec=LinkResolver)

    from scripts.pipeline.pipeline.phases.assemble import run_assemble
    return run_assemble(
        output_dir=output_dir,
        manifest=manifest,
        results=results,
        strategy=strategy or {},
        domain=domain,
        list_page_assembler=assembler,
        link_resolver=resolver,
        client=client,
    )


class TestCategoryIndexGeneration(unittest.TestCase):
    """Test category index page generation (ns=14) in assemble phase."""

    def _make_manifest(self, pages):
        return {"pages": pages, "list_page_content": {}}

    def _make_results(self, titles_ok=None):
        """Build results dict. titles_ok: set of titles with status=ok."""
        results = {}
        for t in (titles_ok or set()):
            results[t] = {
                "status": "ok",
                "content": f"---\ntitle: \"{t}\"\n---\n\n# {t}\n\nContent for {t}.",
                "frontmatter": {"title": t},
            }
        return results

    def test_manifest_fallback_when_no_client(self):
        """W2 scenario 1: client=None triggers manifest-based fallback."""
        manifest = self._make_manifest([
            {"title": "Category:Modes", "target_directory": "modes",
             "target_filename": "index.md", "ns": 14},
            {"title": "Daily_Challenges", "target_directory": "modes",
             "target_filename": "Daily_Challenges.md", "ns": 0},
            {"title": "Greed_Mode", "target_directory": "modes",
             "target_filename": "Greed_Mode.md", "ns": 0},
        ])
        results = self._make_results({"Daily_Challenges", "Greed_Mode"})

        with tempfile.TemporaryDirectory() as tmpdir:
            _run_assemble(tmpdir, manifest, results, client=None)

            index_path = os.path.join(tmpdir, "modes", "index.md")
            self.assertTrue(os.path.exists(index_path), "Category index should be written")

            content = open(index_path).read()
            self.assertIn("# Category:Modes", content)
            self.assertIn("[Daily Challenges](Daily_Challenges.md)", content)
            self.assertIn("[Greed Mode](Greed_Mode.md)", content)
            # No ## headers — flat list
            self.assertNotIn("## Pages", content)
            self.assertNotIn("## Subcategories", content)

    def test_empty_category_produces_minimal_output(self):
        """Empty category with no children produces frontmatter + title only."""
        manifest = self._make_manifest([
            {"title": "Category:Empty", "target_directory": "empty",
             "target_filename": "index.md", "ns": 14},
        ])
        results = self._make_results()

        with tempfile.TemporaryDirectory() as tmpdir:
            _run_assemble(tmpdir, manifest, results, client=None)

            index_path = os.path.join(tmpdir, "empty", "index.md")
            self.assertTrue(os.path.exists(index_path))

            content = open(index_path).read()
            self.assertIn("# Category:Empty", content)
            # No member links
            self.assertNotIn("- [", content)

    def test_missing_child_links_to_wiki_url(self):
        """API-returned member not in manifest links to original wiki URL."""
        from unittest.mock import MagicMock

        client = MagicMock()
        client.query.return_value = {
            "query": {
                "categorymembers": [
                    {"title": "Daily_Challenges", "ns": 0},
                    {"title": "NonExistent_Page", "ns": 0},
                ]
            }
        }

        manifest = self._make_manifest([
            {"title": "Category:Modes", "target_directory": "modes",
             "target_filename": "index.md", "ns": 14},
            {"title": "Daily_Challenges", "target_directory": "modes",
             "target_filename": "Daily_Challenges.md", "ns": 0},
            # NonExistent_Page intentionally not in manifest
        ])
        results = self._make_results({"Daily_Challenges"})

        with tempfile.TemporaryDirectory() as tmpdir:
            _run_assemble(tmpdir, manifest, results, client=client)

            index_path = os.path.join(tmpdir, "modes", "index.md")
            content = open(index_path).read()

            # Daily_Challenges in manifest → relative path
            self.assertIn("[Daily Challenges](Daily_Challenges.md)", content)
            # NonExistent_Page not in manifest → wiki URL
            self.assertIn("NonExistent Page", content)
            self.assertIn("test.wiki.gg/wiki/NonExistent_Page", content)

    def test_non_category_pages_not_affected(self):
        """Non-ns=14 pages are written normally, not touched by category logic."""
        manifest = self._make_manifest([
            {"title": "Some_Page", "target_directory": "items",
             "target_filename": "Some_Page.md", "ns": 0},
        ])
        results = {
            "Some_Page": {
                "status": "ok",
                "content": "---\ntitle: Some_Page\n---\n\n# Some Page\n\nOriginal content.",
                "frontmatter": {"title": "Some_Page"},
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            _run_assemble(tmpdir, manifest, results, client=None)

            page_path = os.path.join(tmpdir, "items", "Some_Page.md")
            self.assertTrue(os.path.exists(page_path))
            content = open(page_path).read()
            self.assertIn("Original content.", content)

    def test_members_sorted_alphabetically(self):
        """Members are sorted alphabetically in output."""
        manifest = self._make_manifest([
            {"title": "Category:Test", "target_directory": "test",
             "target_filename": "index.md", "ns": 14},
            {"title": "Zebra_Page", "target_directory": "test",
             "target_filename": "Zebra_Page.md", "ns": 0},
            {"title": "Alpha_Page", "target_directory": "test",
             "target_filename": "Alpha_Page.md", "ns": 0},
            {"title": "Middle_Page", "target_directory": "test",
             "target_filename": "Middle_Page.md", "ns": 0},
        ])
        results = self._make_results({"Alpha_Page", "Middle_Page", "Zebra_Page"})

        with tempfile.TemporaryDirectory() as tmpdir:
            _run_assemble(tmpdir, manifest, results, client=None)

            index_path = os.path.join(tmpdir, "test", "index.md")
            content = open(index_path).read()

            lines = [l for l in content.split("\n") if l.startswith("- [")]
            # Extract page names to check order
            names = [l.split("]")[0].replace("- [", "") for l in lines]
            self.assertEqual(names, sorted(names))


if __name__ == "__main__":
    unittest.main()
