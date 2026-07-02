"""Unit tests for capability_gate.py."""
from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.explore.capability_gate import check_requirements


class TestCheckRequirements(unittest.TestCase):
    """Tests for check_requirements function."""

    def setUp(self):
        self.registry = {
            "convert": {
                "cleanup_ops": [
                    {"name": "strip_fandom_infobox_tables", "implemented_in": "preprocessor.py", "strategy_field": "extraction.cleanup"},
                    {"name": "convert_ambox_to_text", "implemented_in": "preprocessor.py", "strategy_field": "extraction.cleanup"},
                ]
            },
            "extract": {
                "infobox_handlers": [
                    {"name": "text", "implemented_in": "infobox.py", "strategy_field": "extraction.infobox_field_handlers"},
                    {"name": "count_images", "implemented_in": "infobox.py", "strategy_field": "extraction.infobox_field_handlers"},
                ]
            },
        }

    def test_all_known_returns_empty(self):
        """When scaffold uses only known ops/handlers, returns empty list."""
        scaffold = {
            "extraction": {
                "cleanup": ["strip_fandom_infobox_tables", "convert_ambox_to_text"],
                "infobox_field_handlers": {"text": {}, "count_images": {}},
            }
        }
        gaps = check_requirements(scaffold, self.registry)
        self.assertEqual(gaps, [])

    def test_unknown_cleanup_op_detected(self):
        """Unknown cleanup op generates a gap."""
        scaffold = {
            "extraction": {
                "cleanup": ["unknown_op"],
            }
        }
        gaps = check_requirements(scaffold, self.registry)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["capability"], "convert")
        self.assertEqual(gaps[0]["issue"], "new_cleanup_op")
        self.assertIn("unknown_op", gaps[0]["detail"])

    def test_unknown_infobox_handler_detected(self):
        """Unknown infobox handler generates a gap."""
        scaffold = {
            "extraction": {
                "infobox_field_handlers": {"custom_parser": {"handler": "custom"}},
            }
        }
        gaps = check_requirements(scaffold, self.registry)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["capability"], "extract")
        self.assertEqual(gaps[0]["issue"], "new_infobox_handler")
        self.assertIn("custom_parser", gaps[0]["detail"])

    def test_multiple_gaps(self):
        """Multiple unknown capabilities all reported."""
        scaffold = {
            "extraction": {
                "cleanup": ["bad_op1", "bad_op2", "strip_fandom_infobox_tables"],
                "infobox_field_handlers": {"bad_handler": {}, "text": {}},
            }
        }
        gaps = check_requirements(scaffold, self.registry)
        self.assertEqual(len(gaps), 3)

    def test_empty_scaffold(self):
        """Empty scaffold returns no gaps."""
        gaps = check_requirements({}, self.registry)
        self.assertEqual(gaps, [])

    def test_no_cleanup_in_scaffold(self):
        """Scaffold without extraction.cleanup is fine."""
        scaffold = {"extraction": {"infobox_field_handlers": {"text": {}}}}
        gaps = check_requirements(scaffold, self.registry)
        self.assertEqual(gaps, [])

    def test_missing_registry_sections(self):
        """Registry without convert or extract sections is handled gracefully."""
        empty_registry = {}
        scaffold = {
            "extraction": {
                "cleanup": ["some_op"],
                "infobox_field_handlers": {"some_handler": {}},
            }
        }
        gaps = check_requirements(scaffold, empty_registry)
        self.assertEqual(len(gaps), 2)


if __name__ == "__main__":
    unittest.main()
