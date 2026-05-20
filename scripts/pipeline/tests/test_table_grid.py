"""Unit tests for table grid parsing, rendering, and transpose in HtmlToMarkdownConverter."""

from __future__ import annotations

import pytest
from selectolax.parser import HTMLParser

from scripts.lib.extraction.converter import HtmlToMarkdownConverter


def _convert_table(html: str, config: dict = None) -> str:
    """Helper: wrap <table> in a body, convert, return table output."""
    wrapper = f"<div>{html}</div>"
    converter = HtmlToMarkdownConverter(
        wiki_domain="test.wiki.gg",
        extraction_config=config,
    )
    parser = HTMLParser(wrapper)
    root = parser.css_first("div")
    table_node = root.css_first("table")
    return converter._render_table(table_node, source_dir="")


# ---------------------------------------------------------------------------
# _build_table_grid tests
# ---------------------------------------------------------------------------


class TestBuildTableGrid:
    def test_simple_table_no_spans(self):
        html = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        result = _convert_table(html)
        assert "| A | B |" in result
        assert "| --- | --- |" in result
        assert "| 1 | 2 |" in result

    def test_colspan_header(self):
        html = '<table><tr><th colspan="2">Header</th></tr><tr><td>A</td><td>B</td></tr></table>'
        result = _convert_table(html)
        lines = result.split("\n")
        # Header row should have "Header" twice
        assert "| Header | Header |" in lines[0]
        assert "| A | B |" in result

    def test_rowspan_first_column(self):
        html = '<table><tr><th rowspan="2">Label</th><td>1</td></tr><tr><td>2</td></tr></table>'
        result = _convert_table(html)
        # First row is mixed th/td, so header_row_count=0
        # Grid: [["Label", "1"], ["Label", "2"]]
        assert "Label" in result
        assert "| Label | 2 |" in result

    def test_empty_table(self):
        html = '<table></table>'
        result = _convert_table(html)
        assert result == ""

    def test_empty_tr(self):
        html = '<table><tr></tr></table>'
        result = _convert_table(html)
        assert result == ""

    def test_mixed_colspan_rowspan(self):
        """Simplified version of the Characters table structure."""
        html = (
            '<table>'
            '<tr><th rowspan="2">Stat</th><th colspan="2">DLC1</th></tr>'
            '<tr><th>CharA</th><th>CharB</th></tr>'
            '<tr><td>HP</td><td>3</td><td>4</td></tr>'
            '</table>'
        )
        result = _convert_table(html)
        # Should produce a valid markdown table with 3 columns
        assert "---" in result
        lines = [l for l in result.split("\n") if l.strip()]
        # header_row_count=2 (first two rows are all <th>)
        assert len(lines) >= 4  # 2 header + separator + 1 body


# ---------------------------------------------------------------------------
# _render_grid_as_table tests
# ---------------------------------------------------------------------------


class TestRenderGridAsTable:
    def test_pipe_escape(self):
        html = '<table><tr><th>a | b</th></tr><tr><td>val</td></tr></table>'
        result = _convert_table(html)
        assert "a \\| b" in result

    def test_empty_grid(self):
        converter = HtmlToMarkdownConverter(wiki_domain="test.wiki.gg")
        assert converter._render_grid_as_table([], header_row_count=1) == ""


# ---------------------------------------------------------------------------
# _transpose_grid tests
# ---------------------------------------------------------------------------


class TestTransposeGrid:
    def test_transpose_2x3(self):
        grid = [["A", "B", "C"], ["1", "2", "3"]]
        result = HtmlToMarkdownConverter._transpose_grid(grid, header_row_count=1)
        assert result == [["A", "1"], ["B", "2"], ["C", "3"]]

    def test_transpose_empty(self):
        assert HtmlToMarkdownConverter._transpose_grid([], header_row_count=1) == []

    def test_transpose_multi_row_header(self):
        grid = [
            ["", "Rebirth", "Rebirth"],
            ["Stat", "Isaac", "Magdalene"],
            ["HP", "❤❤❤", "❤❤❤❤"],
        ]
        result = HtmlToMarkdownConverter._transpose_grid(grid, header_row_count=2)
        # Row 0: col0 has ["", "Stat"] -> "Stat"; col0 data=HP
        assert result[0] == ["Stat", "HP"]
        # Row 1: col1 has ["Rebirth", "Isaac"] -> "Rebirth → Isaac"; col1 data=❤❤❤
        assert result[1] == ["Rebirth → Isaac", "❤❤❤"]
        # Row 2: col2 has ["Rebirth", "Magdalene"] -> "Rebirth → Magdalene"; col2 data=❤❤❤❤
        assert result[2] == ["Rebirth → Magdalene", "❤❤❤❤"]

    def test_transpose_header_row_count_zero(self):
        grid = [["A", "B"], ["1", "2"]]
        result = HtmlToMarkdownConverter._transpose_grid(grid, header_row_count=0)
        assert result == [["A", "1"], ["B", "2"]]


# ---------------------------------------------------------------------------
# Integration: transpose_wider_than threshold
# ---------------------------------------------------------------------------


class TestTransposeThreshold:
    def test_wide_table_transposes(self):
        """22-column table with threshold 10 should transpose."""
        cols = 22
        header_cells = "".join(f'<th>H{i}</th>' for i in range(cols))
        data_cells = "".join(f'<td>D{i}</td>' for i in range(cols))
        html = f'<table><tr>{header_cells}</tr><tr>{data_cells}</tr></table>'
        result = _convert_table(html, config={"table_options": {"transpose_wider_than": 10}})
        # After transpose, should have many rows but only 2 columns
        lines = [l for l in result.split("\n") if l.strip() and "---" not in l]
        # Header row + 22 data rows = 23 lines (minus separator)
        assert len(lines) >= 22

    def test_narrow_table_no_transpose(self):
        """5-column table with threshold 10 should NOT transpose."""
        html = '<table><tr><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th></tr><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td></tr></table>'
        result = _convert_table(html, config={"table_options": {"transpose_wider_than": 10}})
        # Should stay as 5-column table
        assert "| A | B | C | D | E |" in result
        assert "| 1 | 2 | 3 | 4 | 5 |" in result

    def test_no_config_no_transpose(self):
        """Without config, wide table should NOT transpose."""
        cols = 22
        header_cells = "".join(f'<th>H{i}</th>' for i in range(cols))
        data_cells = "".join(f'<td>D{i}</td>' for i in range(cols))
        html = f'<table><tr>{header_cells}</tr><tr>{data_cells}</tr></table>'
        result = _convert_table(html, config=None)
        # Should stay wide
        assert "H0" in result

    def test_transposed_renders_as_markdown_table(self):
        """Transposed table should render as valid markdown table."""
        html = '<table><tr><th>A</th><th>B</th><th>C</th></tr><tr><td>1</td><td>2</td><td>3</td></tr></table>'
        result = _convert_table(html, config={"table_options": {"transpose_wider_than": 2}})
        # Should have separator
        assert "| --- |" in result
        # No fallback list format
        assert not any(line.startswith("- ") for line in result.split("\n"))


# ---------------------------------------------------------------------------
# Regression: no fallback list output
# ---------------------------------------------------------------------------


class TestNoFallback:
    def test_complex_table_no_list_output(self):
        """Complex table should never produce '- cell | cell' fallback."""
        html = (
            '<table><tr><th colspan="2">Header</th></tr>'
            '<tr><td>A</td><td>B</td></tr></table>'
        )
        result = _convert_table(html)
        assert not any(line.startswith("- ") for line in result.split("\n"))
        assert "| --- |" in result
