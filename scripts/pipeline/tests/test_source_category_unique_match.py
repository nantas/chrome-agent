"""Unit tests for _apply_source_category_assignments unique-match logic.

Spec:
  - openspec/changes/fix-page-assignment-priority-gaps/specs/page-assignment/spec.md
  - Requirement: unique-source-category-assignment

Validates:
  1. Single source_categories match → immediate assignment (source_category_match)
  2. Multiple source_categories match → deferred (no assignment)
  3. Zero source_categories match → deferred (no assignment)
"""

from __future__ import annotations

import os
import sys
import unittest

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from scripts.pipeline.pipeline.page_assigner import _apply_source_category_assignments


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ASSIGNMENT_PRIORITY = [
    "Items", "Bosses", "Monsters", "Characters", "Cards",
    "Challenges", "Transformations", "Chapters", "Rooms", "Mechanics",
    "Achievements", "Pickups", "Effects", "Curses", "Seeds",
    "Endings", "Music", "Trinkets", "Modes", "Objects",
    "Attributes", "Completion Marks",
]

CAT_NAME_TO_DIR = {
    "Items": "items", "Bosses": "bosses", "Monsters": "monsters",
    "Characters": "characters", "Cards": "cards", "Challenges": "challenges",
    "Transformations": "transformations", "Chapters": "chapters",
    "Rooms": "rooms", "Mechanics": "mechanics", "Achievements": "achievements",
    "Pickups": "pickups", "Effects": "effects", "Curses": "curses",
    "Seeds": "seeds", "Endings": "endings", "Music": "music",
    "Trinkets": "trinkets", "Modes": "modes", "Objects": "objects",
    "Attributes": "attributes", "Completion Marks": "completion_marks",
}


def _make_page(title: str, source_categories: list[str]) -> dict:
    return {
        "title": title,
        "source_categories": source_categories,
        "assignment_method": None,
    }


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestUniqueSourceCategoryAssignment(unittest.TestCase):
    """Spec requirement: unique-source-category-assignment"""

    def test_single_match_assigns_immediately(self):
        """Scenario: single-source-category-match

        WHEN a page has source_categories: ["Items"]
        AND assignment_priority begins with ["Items", "Bosses", ...]
        THEN the page SHALL be assigned with assignment_method: "source_category_match"
        """
        pages = [_make_page("The Sad Onion", ["Items"])]
        unassigned = list(pages)

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        self.assertEqual(result[0]["target_directory"], "items")
        self.assertEqual(result[0]["assigned_category"], "Items")
        self.assertEqual(result[0]["assignment_method"], "source_category_match")

    def test_multiple_match_defers(self):
        """Scenario: multiple-source-category-match-deferred

        WHEN a page has source_categories: ["Bosses", "Chapters"]
        AND assignment_priority has both "Bosses" and "Chapters"
        THEN the page SHALL NOT be assigned in Step 2
        """
        pages = [_make_page("Basement", ["Bosses", "Chapters"])]
        unassigned = list(pages)

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        self.assertIsNone(result[0].get("assignment_method"))
        self.assertIsNone(result[0].get("target_directory"))

    def test_multiple_match_defers_various_combos(self):
        """Additional: multiple match defers for different category combos."""
        pages = [
            _make_page("Caves", ["Bosses", "Chapters"]),
            _make_page("Womb", ["Bosses", "Chapters", "Monsters"]),
            _make_page("Mixed Page", ["Items", "Transformations", "Mechanics"]),
        ]
        unassigned = list(pages)

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        for page in result:
            self.assertIsNone(page.get("assignment_method"),
                              f"Page '{page['title']}' should be deferred but was assigned")

    def test_zero_match_defers(self):
        """Scenario: zero-source-category-match-deferred

        WHEN a page has source_categories: []
        THEN the page SHALL NOT be assigned in Step 2
        """
        pages = [_make_page("Unknown Page", [])]
        unassigned = list(pages)

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        self.assertIsNone(result[0].get("assignment_method"))
        self.assertIsNone(result[0].get("target_directory"))

    def test_zero_match_when_no_priority_match(self):
        """WHEN source_categories has names not in assignment_priority → deferred."""
        pages = [_make_page("Obscure Page", ["NonExistentCategory"])]
        unassigned = list(pages)

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        self.assertIsNone(result[0].get("assignment_method"))

    def test_already_assigned_pages_not_modified(self):
        """Pages with existing assignment_method should be skipped."""
        pages = [
            {
                "title": "Already Assigned",
                "source_categories": ["Items"],
                "assignment_method": "manual_override",
                "target_directory": "custom",
            },
        ]
        unassigned = []  # No unassigned pages

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        # Should remain unchanged
        self.assertEqual(result[0]["assignment_method"], "manual_override")
        self.assertEqual(result[0]["target_directory"], "custom")

    def test_mixed_batch_single_multi_zero(self):
        """Batch with all three types: single match, multi match, zero match."""
        pages = [
            _make_page("Single", ["Bosses"]),
            _make_page("Multi", ["Bosses", "Chapters"]),
            _make_page("Zero", []),
        ]
        unassigned = list(pages)

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        # Single → assigned
        self.assertEqual(result[0]["assignment_method"], "source_category_match")
        self.assertEqual(result[0]["target_directory"], "bosses")
        # Multi → deferred
        self.assertIsNone(result[1].get("assignment_method"))
        # Zero → deferred
        self.assertIsNone(result[2].get("assignment_method"))

    def test_new_priority_entries_match(self):
        """Spec requirement: assignment-priority-gap-fill

        Pages with source_categories containing newly added
        'Attributes' or 'Completion Marks' should match.
        """
        pages = [
            _make_page("Luck", ["Attributes"]),
            _make_page("Completion Mark Page", ["Completion Marks"]),
        ]
        unassigned = list(pages)

        result = _apply_source_category_assignments(
            pages, unassigned, ASSIGNMENT_PRIORITY, CAT_NAME_TO_DIR,
        )

        self.assertEqual(result[0]["target_directory"], "attributes")
        self.assertEqual(result[0]["assignment_method"], "source_category_match")
        self.assertEqual(result[1]["target_directory"], "completion_marks")
        self.assertEqual(result[1]["assignment_method"], "source_category_match")


if __name__ == "__main__":
    unittest.main()
