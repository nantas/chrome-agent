# Specification Delta

## Capability 对齐（已确认）

- Capability: `table-grid-parser`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 转置阈值 >10 列，converter 通用层增强 colspan/rowspan 解析

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: build-table-grid-from-html

`HtmlToMarkdownConverter._build_table_grid(node, source_dir)` SHALL parse a `<table>` selectolax node into a normalized 2D grid (`list[list[str]]`) where every row has the same number of columns, by expanding `colspan` and `rowspan` attributes into placeholder cells.

The method SHALL:
1. Traverse all `<tr>` children using `_child_nodes()`
2. For each `<th>` or `<td>`, read `colspan` (default 1) and `rowspan` (default 1) as integers
3. Track vertically-spanning cells using a `col_spans: dict[int, tuple[int, str]]` mapping column index → (remaining_rows, content)
4. For each row, fill grid slots left-to-right: first check `col_spans` for occupied columns, then consume the next `<th>`/`<td>` element
5. Render cell content using `_render_inline_children(cell, source_dir=source_dir)`
6. Expand colspan into the current row (duplicate content across columns) and register rowspan into `col_spans` for future rows
7. Pad rows shorter than `max_cols` with empty strings

#### Scenario: simple-table-without-spans

- **WHEN** parsing `<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>`
- **THEN** the grid SHALL be `[["A", "B"], ["1", "2"]]`
- **AND** both rows have exactly 2 columns

#### Scenario: colspan-in-header

- **WHEN** parsing `<table><tr><th colspan="2">Header</th></tr><tr><td>A</td><td>B</td></tr></table>`
- **THEN** the grid SHALL be `[["Header", "Header"], ["A", "B"]]`
- **AND** both rows have exactly 2 columns

#### Scenario: rowspan-in-first-column

- **WHEN** parsing `<table><tr><th rowspan="2">Label</th><td>1</td></tr><tr><td>2</td></tr></table>`
- **THEN** the grid SHALL be `[["Label", "1"], ["Label", "2"]]`
- **AND** both rows have exactly 2 columns

#### Scenario: mixed-colspan-rowspan

- **WHEN** parsing a table with `<th rowspan="3">Character</th>` in row 1, `<th colspan="13">Rebirth</th>` in row 1, then `<th rowspan="2">Isaac</th>` in row 2, and `<th>Judas</th>` + `<th>Black Judas</th>` in row 3
- **THEN** row 1 SHALL have 22 columns (1 "Character" + 13 "Rebirth" + 2 "Afterbirth" + 3 "Afterbirth†" + 3 "Repentance")
- **AND** row 2 SHALL have 22 columns with "Character" repeated from rowspan
- **AND** row 3 SHALL have 22 columns with "Character" repeated and sub-characters filling their columns

#### Scenario: malformed-table-with-zero-cells

- **WHEN** parsing a `<table>` with no `<tr>` children or no `<th>`/`<td>` in any row
- **THEN** `_build_table_grid()` SHALL return an empty list `[]`
- **AND** `_render_table()` SHALL return an empty string `""`

#### Scenario: excessive-colspan-protection

- **WHEN** the calculated grid width exceeds 200 columns
- **THEN** `_build_table_grid()` SHALL cap column allocation at 200 and log a warning
- **AND** render the grid with the capped width

### Requirement: render-grid-as-markdown-table

`HtmlToMarkdownConverter._render_grid_as_table(grid, header_row_count)` SHALL render a normalized 2D grid as a standard Markdown table.

The method SHALL:
1. Use `header_row_count` to determine which rows are headers (default: 1 if the first row contains any bold or links, consistent with `_is_simple_markdown_table`'s `<th>` heuristic; otherwise 0)
2. Render header rows as `| cell | cell | ... |`
3. Render a separator row: `| --- | --- | ... |` (one per column)
4. Render body rows as standard Markdown table rows
5. Escape `|` characters within cell content as `\|`
6. Strip trailing `|` from table lines

#### Scenario: standard-table-with-header

- **WHEN** rendering `[["A", "B"], ["1", "2"]]` with `header_row_count=1`
- **THEN** output SHALL be:
  ```
  | A | B |
  | --- | --- |
  | 1 | 2 |
  ```

#### Scenario: pipe-escape-in-cell

- **WHEN** a cell contains the text `a | b`
- **THEN** the rendered table cell SHALL be `a \| b`

#### Scenario: empty-grid

- **WHEN** grid is `[]`
- **THEN** output SHALL be an empty string `""`

### Requirement: delete-obsolete-table-methods

`HtmlToMarkdownConverter._is_simple_markdown_table()` and the fallback list-rendering branch in `_render_table()` SHALL be removed. The `_extract_row()` method MAY be retained or replaced based on design decisions, but SHALL NOT be the primary table parsing mechanism.

#### Scenario: no-fallback-to-list

- **WHEN** any HTML table is encountered during conversion
- **THEN** the output SHALL always be either a Markdown table (via `_build_table_grid` + `_render_grid_as_table`) or an empty string
- **AND** SHALL NOT produce `- cell1 | cell2 | ...` flat list output

### Requirement: nested-table-handling

When `_build_table_grid()` encounters a nested `<table>` inside a `<th>` or `<td>` cell, the nested table SHALL NOT be recursively rendered via `_render_inline_children()`. Instead, the cell content SHALL be rendered from non-table inline children only.

Two independent mechanisms prevent nested table corruption:
1. `_build_table_grid` SHALL only collect direct child `<tr>` elements (via `<tbody>` if present), using `_child_nodes()` traversal instead of `node.css("tr")`, which would capture all descendant rows including those from nested tables.
2. `_render_cell_content` SHALL detect nested `<table>` child elements and skip their recursive rendering, preserving only non-table inline content.

#### Scenario: nested-table-in-cell-skipped

- **WHEN** a `<td>` contains a nested `<table>` element
- **THEN** the cell content SHALL NOT include the nested table's Markdown output
- **AND** the outer table's grid SHALL remain correctly column-aligned

#### Scenario: nested-table-rows-not-in-grid

- **WHEN** a parent `<table>` contains a nested `<table>` inside one of its `<td>` cells
- **THEN** `_build_table_grid()` SHALL NOT include rows from the nested table in the parent grid
- **AND** the parent grid SHALL have exactly the same number of rows as direct `<tr>` children of its `<tbody>`

### Requirement: block-tags-article-section

`HtmlToMarkdownConverter._BLOCK_TAGS` SHALL include `"article"` and `"section"` to ensure HTML5 semantic containers are correctly recognized as block-level elements, preventing inline concatenation of adjacent block content.

#### Scenario: section-wraps-two-articles

- **WHEN** a `<section>` contains two `<article>` elements, each containing a `<table>`
- **AND** `"article"` and `"section"` are in `_BLOCK_TAGS`
- **THEN** `_render_block(section)` SHALL render each article as a separate block
- **AND** the two tables' Markdown output SHALL be separated by `\n\n`
- **AND** SHALL NOT be concatenated as inline content

### Requirement: inline-content-preservation-in-table-cells

Cell content rendered via `_render_inline_children()` SHALL preserve all inline formatting, links, and images as generated by the existing inline rendering pipeline.

#### Scenario: image-in-table-cell

- **WHEN** a `<td>` contains `<img src="/images/icon.png" alt="icon">`
- **THEN** the grid cell SHALL contain `![icon](https://bindingofisaacrebirth.wiki.gg/images/icon.png)`

#### Scenario: link-in-table-cell

- **WHEN** a `<td>` contains `<a href="/wiki/Isaac">Isaac</a>`
- **THEN** the grid cell SHALL contain the resolved relative Markdown link `[Isaac](Isaac.md)`
