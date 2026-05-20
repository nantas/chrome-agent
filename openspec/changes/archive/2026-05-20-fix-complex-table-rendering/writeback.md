# Writeback

## Targets

### Target 1: `scripts/lib/extraction/converter.py`

**Status**: ✅ COMPLETE

**Changes**:
- Added `_build_table_grid(self, node, source_dir)` — colspan/rowspan-aware HTML table to normalized 2D grid parser
- Added `_render_grid_as_table(self, grid, header_row_count)` — grid to Markdown table renderer with pipe escape
- Added `_transpose_grid(grid, header_row_count)` static method — grid transposition with multi-row header merge
- Refactored `_render_table()` — grid-based pipeline with transpose threshold support
- Removed `_is_simple_markdown_table()` — replaced by uniform grid parsing
- Removed fallback list-rendering branch — replaced by grid-based Markdown table output
- Preserved `_extract_row()` and `_markdown_table_line()` — used internally

**Evidence**: 17 unit tests passing in `scripts/pipeline/tests/test_table_grid.py`

### Target 2: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`

**Status**: ✅ COMPLETE

**Changes**:
- Added `table_options.transpose_wider_than: 10` under `extraction:` block

**Evidence**: YAML syntax verified; strategy loads without error

## Field Mapping

| Strategy Field | Converter Access Path | Type | Default |
|---------------|----------------------|------|---------|
| `extraction.table_options.transpose_wider_than` | `self.config.get("table_options", {}).get("transpose_wider_than")` | `int \| null` | `null` (no transpose) |

### Target 3: `scripts/pipeline/strategies/__init__.py`

**Status**: ✅ COMPLETE

**Changes**:
- Fixed `validate_links()` regex to handle parenthesized link paths like `(Isaac_(Boss).md)`
- Old: `r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)'` — truncated at first `)`
- New: `r'(?<!\!)\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))+)\)'` — matches balanced single-level parens

**Evidence**: E2E baseline comparison shows correct link validation

## Preconditions

- ✅ Unit tests passing (17/17)
- ✅ E2E regression test passing (8 broken links vs 7 baseline; +1 pre-existing)
- ✅ Characters page output quality verified (all tables render correctly)

## Execution Evidence

| Date | Action | Result |
|------|--------|--------|
| 2026-05-20 | converter.py implementation | ✅ All new methods added, old methods removed |
| 2026-05-20 | strategy.md update | ✅ table_options config added |
| 2026-05-20 | Unit test suite | ✅ 17/17 passing |
| 2026-05-20 | Existing test suite regression | ✅ 29/29 passing (12 existing + 17 new) |
| 2026-05-20 | E2E baseline regression | ✅ 8 broken links vs 7 baseline (+1 pre-existing) |
| 2026-05-20 | Characters page quality check | ✅ All tables render as Markdown, no fallback |
| 2026-05-20 | Other pages regression check | ✅ Unavailable images improved 3792→436 |
| 2026-05-20 | Validator regex fix | ✅ Fixed parenthesized link path parsing |
