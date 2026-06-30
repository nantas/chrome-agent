"""Tests for scripts.explore.architecture_gate dead-config detection.

Validates that after removing the `if key == "cleanup": return True` hardcode,
cleanup config is still NOT flagged as dead — because preprocessor.py (now in
_PIPELINE_FILES) genuinely consumes it. Also confirms truly-unknown fields are
still detected, so the check remains effective.
"""

import os
import unittest

from scripts.explore.architecture_gate import (
    _detect_dead_config,
    detect_dead_cleanup_operations,
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PIPELINE_FILES = [
    os.path.join(REPO_ROOT, "scripts", "lib", "extraction", "converter.py"),
    os.path.join(REPO_ROOT, "scripts", "lib", "extraction", "preprocessor.py"),
]


class TestDeadConfigDetection(unittest.TestCase):
    def setUp(self):
        for p in PIPELINE_FILES:
            self.assertTrue(os.path.exists(p), f"pipeline file missing: {p}")

    def test_cleanup_not_flagged_dead(self):
        """cleanup key is consumed by preprocessor.py — must not be flagged dead."""
        rules = {"extraction": {"cleanup": ["strip_fandom_infobox_tables"]}}
        dead = _detect_dead_config(rules, PIPELINE_FILES)
        self.assertNotIn("cleanup", dead)

    def test_truly_unknown_field_still_detected(self):
        """A field no pipeline file references must still be reported dead."""
        rules = {"extraction": {"totally_bogus_field_xyz": True}}
        dead = _detect_dead_config(rules, PIPELINE_FILES)
        self.assertIn("totally_bogus_field_xyz", dead)


class TestDeadCleanupOperations(unittest.TestCase):
    def test_known_cleanup_op_consumed(self):
        """strip_fandom_infobox_tables is referenced in preprocessor.py — not dead."""
        extraction = {"cleanup": ["strip_fandom_infobox_tables"]}
        dead_ops = detect_dead_cleanup_operations(extraction, PIPELINE_FILES)
        self.assertNotIn("strip_fandom_infobox_tables", dead_ops)

    def test_unknown_cleanup_op_detected(self):
        """An op no pipeline file references must be reported dead."""
        extraction = {"cleanup": ["nonexistent_op_xyz"]}
        dead_ops = detect_dead_cleanup_operations(extraction, PIPELINE_FILES)
        self.assertIn("nonexistent_op_xyz", dead_ops)


if __name__ == "__main__":
    unittest.main()
