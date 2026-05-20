# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: converter `_render_table()` 重构为网格驱动；删除 `_is_simple_markdown_table()` 及 fallback；新增 `_build_table_grid()`、`_render_grid_as_table()`、`_transpose_grid()`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本文件是 `fix-pipeline-quality-gaps` 中同名 spec + `fix-complex-table-rendering` 中 `table-grid-parser`/`table-transpose-config` spec 的增量补充

## MODIFIED Requirements

### Requirement: table-rendering-refactored

`HtmlToMarkdownConverter._render_table(node, source_dir)` SHALL be refactored to use the grid-based parsing pipeline:

1. Call `self._build_table_grid(node, source_dir)` to produce a normalized 2D grid — grid builder SHALL only collect direct child `<tr>` elements to avoid mixing rows from nested tables
2. If the grid is empty, return `""`
3. Read `self.config.get("table_options", {}).get("transpose_wider_than")` to determine the transpose threshold
4. If the grid's column count exceeds the threshold, call `self._transpose_grid(grid, header_row_count)` to transpose
5. Call `self._render_grid_as_table(grid, header_row_count)` to produce the Markdown output

The method SHALL NOT contain any fallback logic to flat list rendering.

#### Scenario: complex-character-table-produces-markdown-table

- **WHEN** converting the Characters page table (29 rows, 22 columns, with colspan/rowspan)
- **AND** `transpose_wider_than` is `10`
- **THEN** the output SHALL be a valid Markdown table
- **AND** SHALL NOT contain `- cell | cell | ...` bullet-list fallback output
- **AND** the transposed table SHALL have characters as rows and stats (Health, Damage, ...) as columns

#### Scenario: simple-table-still-works

- **WHEN** converting a simple 3×2 table without colspan/rowspan
- **AND** `transpose_wider_than` is `10` (not triggered for 2 columns)
- **THEN** the output SHALL be a standard Markdown table with header row and separator
- **AND** the output SHALL match pre-refactor behavior

#### Scenario: nav-table-preserved

- **WHEN** converting a `table.navbox` element (already stripped by `clean_html`)
- **THEN** the navbox SHALL NOT appear in the converted output
- **AND** this behavior SHALL be unchanged from pre-refactor (navboxes removed before table rendering)

### Requirement: build-table-grid-integration

`HtmlToMarkdownConverter` SHALL expose `_build_table_grid(node, source_dir)` as specified in `specs/table-grid-parser/spec.md`. The method SHALL be called from `_render_table()` and MAY be called from other methods in the future.

### Requirement: render-grid-as-table-integration

`HtmlToMarkdownConverter` SHALL expose `_render_grid_as_table(grid, header_row_count)` as specified in `specs/table-grid-parser/spec.md`.

### Requirement: transpose-grid-integration

`HtmlToMarkdownConverter` SHALL expose `_transpose_grid(grid, header_row_count)` as a static method, as specified in `specs/table-transpose-config/spec.md`.

### Requirement: block-tags-coverage

`HtmlToMarkdownConverter._BLOCK_TAGS` SHALL include `"article"` and `"section"` to ensure HTML5 semantic sectioning elements are treated as block containers. This prevents `_has_block_children()` from returning `False` for parent elements whose only block children are `<article>` or `<section>`, which would cause their content to be rendered inline and concatenated.

#### Scenario: tabber-section-renders-as-separate-blocks

- **WHEN** a `<section>` contains two `<article>` elements, each wrapping a `<table>`
- **AND** `"article"` and `"section"` are in `_BLOCK_TAGS`
- **THEN** `_render_block(section)` SHALL separate the two tables with `\n\n`
- **AND** the last row of the first table SHALL NOT be concatenated with the header of the second table

### Requirement: strategy-config-integration

`HtmlToMarkdownConverter._render_table()` SHALL read `self.config.table_options.transpose_wider_than` to determine whether to transpose, as specified in `specs/table-transpose-config/spec.md`.

## REMOVED Requirements

### Requirement: is-simple-markdown-table-check

**Reason**: `_is_simple_markdown_table()` is replaced by `_build_table_grid()` which handles both simple and complex tables uniformly. The grid-based approach eliminates the need for a separate simplicity heuristic.

**Migration**: All callers of `_render_table()` (only `_render_block()`) are automatically migrated by the refactored `_render_table()` method. No external callers exist.

### Requirement: fallback-to-flat-list-rendering

**Reason**: The fallback branch in `_render_table()` that produces `- cell | cell | ...` output is replaced by grid-based rendering which always produces valid Markdown tables.

**Migration**: No migration needed. All tables now render as Markdown tables. The change is a quality improvement with no loss of functionality.

## RENAMED Requirements

- FROM: `### Requirement: N/A` (no renames in this change)
- TO: `### Requirement: N/A`
