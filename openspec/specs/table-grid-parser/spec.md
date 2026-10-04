# Specification: table-grid-parser

## Purpose

Define shared HTML table grid construction, structural preservation and semantic continuation cells without duplicating source assets.


## Capability 对齐

- Capability: `table-grid-parser`
- 来源: `fix-complex-table-rendering` change
- 变更类型: `new`

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- 所有表格网格解析与渲染行为必须符合本文档

## Requirements

### Requirement: build-table-grid-from-html

`HtmlToMarkdownConverter._build_table_grid(node, source_dir)` SHALL parse a `<table>` selectolax node into a normalized 2D grid (`list[list[str]]`) where every row has the same number of columns, by expanding `colspan` and `rowspan` attributes into placeholder cells.

The method SHALL:
1. Collect only **direct child** `<tr>` elements (via `<tbody>` if present) using `_child_nodes()` traversal, NOT `node.css("tr")` which captures all descendant rows including those from nested tables
2. For each `<th>` or `<td>`, read `colspan` (default 1) and `rowspan` (default 1) as integers
3. Track vertically-spanning cells using a `col_spans: dict[int, tuple[int, str]]` mapping column index → (remaining_rows, content)
4. For each row, fill grid slots left-to-right: first check `col_spans` for occupied columns, then consume the next `<th>`/`<td>` element
5. Render cell content using `_render_cell_content(cell)` which skips nested `<table>` children
6. Expand colspan into the current row and register rowspan into `col_spans` for future rows; continuation content SHALL follow merged-cell-asset-retention (repeat text context with semantic icon labels, not image assets).
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

#### Scenario: nested-table-rows-excluded

- **WHEN** a parent `<table>` contains a nested `<table>` inside one of its `<td>` cells
- **THEN** `_build_table_grid()` SHALL NOT include rows from the nested table in the parent grid
- **AND** the parent grid SHALL have exactly the same number of rows as direct `<tr>` children

#### Scenario: excessive-colspan-protection

- **WHEN** the calculated grid width exceeds 200 columns
- **THEN** `_build_table_grid()` SHALL cap column allocation at 200 and log a warning
- **AND** render the grid with the capped width

### Requirement: render-grid-as-markdown-table

`HtmlToMarkdownConverter._render_grid_as_table(grid, header_row_count)` SHALL render a normalized 2D grid as a standard Markdown table. Cell content SHALL have `|` escaped as `\|` and `\n` replaced with space.

The method SHALL:
1. Use `header_row_count` to determine which rows are headers (default: 1 if the first row contains any bold or links, consistent with `<th>` heuristic; otherwise 0)
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

### Requirement: nested-table-cell-handling

`HtmlToMarkdownConverter._render_cell_content(cell, source_dir)` SHALL detect nested `<table>` child elements and skip their recursive rendering, preserving only non-table inline content. A WARNING SHALL be logged when a nested table is detected.

Two independent mechanisms prevent nested table corruption:
1. `_build_table_grid` SHALL only collect direct child `<tr>` elements (via `<tbody>` if present), using `_child_nodes()` traversal instead of `node.css("tr")`, which would capture all descendant rows including those from nested tables.
2. `_render_cell_content` SHALL detect nested `<table>` child elements and skip their recursive rendering, preserving only non-table inline content.

#### Scenario: nested-table-in-cell-skipped

- **WHEN** a `<td>` contains a nested `<table>` element and inline text
- **THEN** the cell content SHALL include the inline text
- **AND** SHALL NOT include the nested table's Markdown output

#### Scenario: nested-table-rows-not-in-grid

- **WHEN** a parent `<table>` contains a nested `<table>` inside one of its `<td>` cells
- **THEN** `_build_table_grid()` SHALL NOT include rows from the nested table in the parent grid
- **AND** the parent grid SHALL have exactly the same number of rows as direct `<tr>` children of its `<tbody>`

### Requirement: delete-obsolete-table-methods

`HtmlToMarkdownConverter._is_simple_markdown_table()` and the fallback list-rendering branch in `_render_table()` SHALL be removed. The `_extract_row()` method MAY be retained or replaced based on design decisions, but SHALL NOT be the primary table parsing mechanism.

#### Scenario: no-fallback-to-list

- **WHEN** any HTML table is encountered during conversion
- **THEN** the output SHALL always be either a Markdown table (via `_build_table_grid` + `_render_grid_as_table`) or an empty string
- **AND** SHALL NOT produce `- cell1 | cell2 | ...` flat list output

### Requirement: block-tags-article-section

`HtmlToMarkdownConverter._BLOCK_TAGS` SHALL include `"article"` and `"section"` to ensure HTML5 semantic containers are correctly treated as block-level elements.

#### Scenario: tabber-section-renders-as-separate-blocks

- **WHEN** a `<section>` contains two `<article>` elements, each containing a `<table>`
- **AND** `"article"` and `"section"` are in `_BLOCK_TAGS`
- **THEN** the two tables' Markdown output SHALL be separated by `\n\n`
- **AND** the last row of the first table SHALL NOT merge with the header of the second table

### Requirement: inline-content-preservation-in-table-cells

Cell content rendered via `_render_inline_children()` SHALL preserve all inline formatting, links, and images as generated by the existing inline rendering pipeline.

#### Scenario: image-in-table-cell

- **WHEN** a `<td>` contains `<img src="/images/icon.png" alt="icon">`
- **THEN** the grid cell SHALL contain `![icon](https://bindingofisaacrebirth.wiki.gg/images/icon.png)`

#### Scenario: link-in-table-cell

- **WHEN** a `<td>` contains `<a href="/wiki/Isaac">Isaac</a>`
- **THEN** the grid cell SHALL contain the resolved relative Markdown link `[Isaac](Isaac.md)`

### Requirement: merged-cell-asset-retention
共享 HTML 转换内核 SHALL 在合并单元格原始槽位保留允许输出的图片，在 colspan/rowspan 的所有延续槽位保留文本上下文并将图标替换为可读文本，不得复制图片资产或直接删除图标语义。每个源图片出现次数 SHALL 保持一次（不对不同源节点的同 URL 图片作全局去重）。被既有过滤规则排除的图片 SHALL NOT 被名称替换复活。

名称 SHALL 按“策略精确 alt 映射 → 可靠 alt → 可靠 title → 固定占位 `（未命名图标）`”解析；属性匹配前只 trim 首尾空白，映射区分大小写、不做模糊匹配。可靠名称 SHALL 非空，且不是 URL、图片文件名或通用占位名 image/icon；文件名包括 png/jpg/jpeg/gif/svg/webp/avif/ico 扩展名，不区分大小写。系统 SHALL NOT 从路径猜测名称。替代名称 SHALL 作为文本节点渲染，保留图标原有链接目的、相邻文字和顺序，并安全转义 Markdown 特殊字符；同一链接已有相同可见名称，或同一单元格内紧邻的可见标签与可靠名称完全相同时 SHALL 不重复添加该名称。邻接匹配 SHALL 不跨其他文字、图片、换行或块边界；不同链接目的 SHALL 保持独立。系统 SHALL 保留原标签文字、格式和链接目的，不对独立源图片或文字全局去重。

#### Scenario: crypt-keeper-colspan
- **WHEN** 跨两列的效果格包含 `or` 分隔的 Blind、Weak、Vulnerable、Daze 图标
- **THEN** 原格图片保留，第二格具有对应文字名称及原有百分比/顺序，不再产生删除图标导致的 `or or`。

#### Scenario: mixed-span-and-repeated-source-assets
- **WHEN** 图片格同时具有 colspan 和 rowspan，另一个源格也使用相同图片 URL
- **THEN** 每个源图片各输出一次，所有延续槽位含名称，行列占位与邻接数据不变。

#### Scenario: explicit-name-or-unknown
- **WHEN** alt 为 `Dd2 token vulnerable.png` 且存在精确映射
- **THEN** 延续格使用映射值 Vulnerable；未命中且 title 不可靠时使用 `（未命名图标）`，不输出猜测的状态名。

#### Scenario: linked-icon-and-existing-label
- **WHEN** 图标被链接包裹，链接已有同名文本，或名称含管道/方括号
- **THEN** 链接目的与原文字保留，同名不重复，表格行列及 Markdown 链接语法不被破坏。

#### Scenario: ordinary-and-filtered-content
- **WHEN** 表格没有合并格，合并格仅有文字，或图片被过滤
- **THEN** 普通格与纯文本展开保持原行为，过滤图片不产生新标签。

#### Scenario: adjacent-exact-label
- **WHEN** 图标和同名标签位于相邻 inline 节点（可以跨透明包装或空白），标签是纯文字或同目的链接
- **THEN** 延续格只保留一次名称，原文字格式及链接目的不丢失；不同目的链接、其他内容间隔和不同名称不合并。

#### Scenario: merged-image
- WHEN 单个图片位于 colspan 或 rowspan 单元格
- THEN 输出图片出现一次，文本上下文继续保留。

### Requirement: table-section-and-nested-data
完整宽度、单单元格、含标题的行 SHALL 输出独立 Markdown 标题。嵌套表格 SHALL 从父格移出，在所属父表片段后输出独立表格，不丢失数值、不混入父网格。

#### Scenario: nested-skill-levels
- WHEN 技能表内含 Further levels 子表
- THEN 所有等级和对应数值均保留，子表独立且顺序稳定。

### Requirement: browser-table-structures
转换 SHALL 包含直接 thead/tbody/tfoot 行、表格 caption 的资产，以及晋升标题格内的嵌套表。多行表头 SHALL 按列保留各级标签并合并为单个合法 GFM 表头。

#### Scenario: header-and-caption-assets
- WHEN 表头图标在 thead 或 caption 中
- THEN 图片出现次数与来源一致，表头关系、正文值和 tfoot 文本完整。

### Requirement: rich-pre-and-literal-text
富文本 pre 内的图片和链接 SHALL 保留为可用 Markdown，纯文本 pre SHALL 保持代码。可见文字中的尖括号 SHALL 转义，不能被解释为 HTML。

#### Scenario: warning-versus-code
- WHEN pre 含警告图标和链接
- THEN 提示可见、图标保留、链接可点击；普通代码仍使用围栏。
