# Specification Delta

## Capability 对齐（已确认）

- Capability: `html-to-markdown-converter`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 确认 — 可复用的 HTML→MD 转换器，支持表格处理

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Basic HTML to Markdown conversion
The converter SHALL transform standard HTML elements to Markdown equivalents: `<h1>`–`<h6>` to `#`–`######`, `<p>` to paragraph blocks, `<strong>`/`<b>` to `**text**`, `<em>`/`<i>` to `*text*`, `<a href>` to `[text](href)`, `<ul>`/`<ol>`/`<li>` to list items, `<pre>`/`<code>` to code blocks, and `<br>` to line breaks.

#### Scenario: Basic heading conversion
- **WHEN** input HTML contains `<h2>Section Title</h2>`
- **THEN** output Markdown SHALL contain `## Section Title`

### Requirement: Table conversion with rowspan and colspan
The converter SHALL transform HTML `<table>` elements to Markdown tables, correctly handling `rowspan` and `colspan` attributes.

- Cells with `rowspan="N"` SHALL propagate their content to `N-1` subsequent rows in the same column position.
- Cells with `colspan="N"` SHALL occupy `N` column positions in the current row.
- The first row of each table SHALL be treated as the header row, followed by a separator line `| --- | --- |`.
- Pipe characters (`|`) in cell content SHALL be escaped as `\|`.

#### Scenario: Simple table
- **WHEN** input HTML contains a `<table>` with one header row and two data rows, all with equal columns
- **THEN** output SHALL be a valid Markdown table with header, separator, and two data rows

#### Scenario: Rowspan propagation
- **WHEN** a cell has `rowspan="2"` in column 0
- **THEN** the next row SHALL have an empty cell at column 0, with subsequent columns shifted right

#### Scenario: Pipe character in cell
- **WHEN** a table cell contains the literal pipe character `|` (e.g., Unicode codepoint reference table)
- **THEN** that `|` SHALL be output as `\|` in the Markdown table

### Requirement: Nested table handling
The converter SHALL handle tables nested inside other table cells by flattening the inner table content into inline text with escaped pipe separators.

#### Scenario: Nested table in cell
- **WHEN** a `<td>` contains a child `<table>` with locale code mappings
- **THEN** the inner table SHALL be converted to a single line of text with `\|` separators, replacing the cell content, rather than breaking the outer table structure

### Requirement: Image preservation
The converter SHALL preserve `<img>` tags as Markdown image syntax `![alt](src)` with the original `src` attribute value unchanged. Template boilerplate images (`noscript.svg`, `template/img/*`) SHALL be discarded.

#### Scenario: Content image preserved
- **WHEN** input contains `<img src="../Attachments/Attach_xxx/yyy.png" title="Click to zoom in.">`
- **THEN** output SHALL contain `![Click to zoom in.](../Attachments/Attach_xxx/yyy.png)`

#### Scenario: Template image discarded
- **WHEN** input contains `<img src="../template/img/noscript.svg">`
- **THEN** output SHALL NOT contain any reference to that image

### Requirement: Navigation table removal
The converter SHALL remove navigation tables (`class` containing `page_nav`) and breadcrumb divs from output.

#### Scenario: Nav table stripped
- **WHEN** input contains `<table class="page_navi_root">...</table>`
- **THEN** output SHALL NOT contain any content from that table

### Requirement: Conditional table processing
The converter SHALL only apply table conversion when `<table>` elements are present in the input HTML. If no tables exist, the converter SHALL skip table-specific processing.

#### Scenario: No tables in input
- **WHEN** input HTML contains no `<table>` elements
- **THEN** the converter SHALL produce valid Markdown without table-specific artifacts or placeholders
