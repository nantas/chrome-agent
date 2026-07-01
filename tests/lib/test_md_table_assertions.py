"""Unit tests for assert_valid_md_tables escaped-pipe handling.

Guards the fix: escaped pipes (\\|) inside table cells must not inflate the
column count. selectolax emits \\| per Markdown spec; the assertion must
honor the escape or flag real tables as malformed.
"""

from __future__ import annotations

import unittest

from scripts.lib.test_assertions import assert_valid_md_tables


class TestValidMdTablesEscapedPipes(unittest.TestCase):
    def test_escaped_pipe_in_cell_does_not_inflate_columns(self) -> None:
        # 4-column table; one cell contains escaped pipes (a \| b \| c)
        md = (
            "| A | B | C | D |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | 2 | 3 | a \\| b \\| c |\n"
        )
        assert_valid_md_tables(md)  # must not raise

    def test_genuinely_mismatched_columns_still_raise(self) -> None:
        md = (
            "| A | B |\n"
            "| --- | --- |\n"
            "| 1 | 2 | 3 |\n"
        )
        with self.assertRaises(AssertionError):
            assert_valid_md_tables(md)


if __name__ == "__main__":
    unittest.main()
