"""Tests for scripts.explore.self_check.auto_remediate fix-type mapping.

Behavioural contract: each fixable_type maps to a specific cleanup or
text_normalization op. Validates the dict-lookup refactor preserves the
original 12-arm if/elif behaviour.
"""

import unittest

from scripts.explore.self_check import auto_remediate


class TestAutoRemediate(unittest.TestCase):
    def test_cleanup_fix_types(self):
        """Each cleanup-mapped fix_type adds the right op."""
        cases = {
            "base64_residue": "fix_lazyload_images",
            "link_resolution": "unwrap_image_wrappers",
            "image_wrapper": "unwrap_image_wrappers",
            "table_class_missing": "strip_fandom_infobox_tables",
            "relative_image_url": "convert_images_full_url",
            "relative_link": "convert_links_full_url",
            "infobox_html_residue": "use_balanced_div_matching",
            "section_loss": "use_balanced_toc_removal",
            "nav_leak": "remove_nav_header_sidebar",
            "youtube_title": "retry_oembed_titles",
            "id_navigation_leak": "extract_infobox_nav_cur",
        }
        for fix_type, expected_op in cases.items():
            with self.subTest(fix_type=fix_type):
                result = auto_remediate({}, [{"fixable_type": fix_type}])
                self.assertIn(expected_op, result["cleanup"],
                              f"{fix_type} should add {expected_op}")

    def test_normalization_fix_type(self):
        result = auto_remediate({}, [{"fixable_type": "space_normalization"}])
        self.assertIn("fix_spaces", result["text_normalization"])
        self.assertEqual(result.get("cleanup", []), [])

    def test_unknown_fix_type_ignored(self):
        result = auto_remediate({}, [{"fixable_type": "totally_unknown"}])
        self.assertEqual(result.get("cleanup", []), [])
        self.assertEqual(result.get("text_normalization", []), [])

    def test_multiple_fixes_batched(self):
        result = auto_remediate({}, [
            {"fixable_type": "base64_residue"},
            {"fixable_type": "relative_link"},
            {"fixable_type": "space_normalization"},
        ])
        self.assertIn("fix_lazyload_images", result["cleanup"])
        self.assertIn("convert_links_full_url", result["cleanup"])
        self.assertIn("fix_spaces", result["text_normalization"])

    def test_preserves_existing_rules(self):
        result = auto_remediate(
            {"cleanup": ["existing_op"], "text_normalization": ["existing_norm"]},
            [{"fixable_type": "base64_residue"}],
        )
        self.assertIn("existing_op", result["cleanup"])
        self.assertIn("fix_lazyload_images", result["cleanup"])

    def test_output_sorted(self):
        result = auto_remediate({}, [
            {"fixable_type": "nav_leak"},
            {"fixable_type": "base64_residue"},
        ])
        self.assertEqual(result["cleanup"], sorted(result["cleanup"]))


if __name__ == "__main__":
    unittest.main()
