"""Unit tests for freeze.py capability gate integration."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml


class TestFreezeCapabilityGate(unittest.TestCase):
    """Tests for capability gate integration in freeze.py."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

        # Create a minimal repo structure
        self.sites_dir = os.path.join(self.tmpdir, "sites", "strategies")
        os.makedirs(self.sites_dir, exist_ok=True)
        self.configs_dir = os.path.join(self.tmpdir, "configs")
        os.makedirs(self.configs_dir, exist_ok=True)

        # Create capability registry
        self.registry = {
            "convert": {
                "cleanup_ops": [
                    {"name": "strip_fandom_infobox_tables", "implemented_in": "preprocessor.py", "strategy_field": "extraction.cleanup"},
                ]
            },
            "extract": {
                "infobox_handlers": [
                    {"name": "text", "implemented_in": "infobox.py", "strategy_field": "extraction.infobox_field_handlers"},
                ]
            },
        }
        with open(os.path.join(self.configs_dir, "capability-registry.yaml"), "w") as f:
            yaml.dump(self.registry, f)

        # Create empty registry.json
        with open(os.path.join(self.sites_dir, "registry.json"), "w") as f:
            json.dump({"entries": []}, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_freeze_passes_when_all_covered(self):
        """Freeze should succeed when scaffold uses only known capabilities."""
        scaffold_content = """# Auto-generated scaffold — review recommended
---
domain: example.com
description: Test site
protection_level: low
extraction:
  cleanup:
    - strip_fandom_infobox_tables
  infobox_field_handlers:
    text: {}
---
"""
        scaffold_path = os.path.join(self.sites_dir, "example.com", "strategy.md")
        os.makedirs(os.path.dirname(scaffold_path), exist_ok=True)
        with open(scaffold_path, "w") as f:
            f.write(scaffold_content)

        from scripts.explore.freeze import freeze
        result = freeze(self.tmpdir, scaffold_path)
        self.assertTrue(result.get("ok"), f"Expected ok=True, got: {result}")

        # No gap file should exist
        gap_path = os.path.join(os.path.dirname(scaffold_path), "capability-gap.yaml")
        self.assertFalse(os.path.exists(gap_path))

    def test_freeze_blocks_on_unknown_capability(self):
        """Freeze should detect unknown capabilities and exit."""
        scaffold_content = """# SCAPFOLD: auto-generated — review recommended
---
domain: example.com
description: Test site
protection_level: low
extraction:
  cleanup:
    - unknown_cleanup_op
  infobox_field_handlers:
    text: {}
---
"""
        scaffold_path = os.path.join(self.sites_dir, "example.com", "strategy.md")
        os.makedirs(os.path.dirname(scaffold_path), exist_ok=True)
        with open(scaffold_path, "w") as f:
            f.write(scaffold_content)

        from scripts.explore.freeze import freeze
        result = freeze(self.tmpdir, scaffold_path)
        self.assertFalse(result.get("ok"), f"Expected ok=False, got: {result}")
        self.assertIn("gaps", result)

        # Gap file should exist
        gap_path = os.path.join(os.path.dirname(scaffold_path), "capability-gap.yaml")
        self.assertTrue(os.path.exists(gap_path), f"Expected gap file at {gap_path}")

        # Verify gap content
        with open(gap_path) as f:
            gaps = yaml.safe_load(f)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["capability"], "convert")
        self.assertEqual(gaps[0]["issue"], "new_cleanup_op")


if __name__ == "__main__":
    unittest.main()
