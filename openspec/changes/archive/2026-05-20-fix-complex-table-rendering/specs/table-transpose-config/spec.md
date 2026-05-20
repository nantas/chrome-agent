# Specification Delta

## Capability 对齐（已确认）

- Capability: `table-transpose-config`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 转置阈值 >10 列，通过 strategy `extraction.table_options.transpose_wider_than` 配置

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: strategy-table-options-schema

The strategy YAML frontmatter SHALL support an optional `extraction.table_options` block with the following schema:

```yaml
extraction:
  table_options:
    transpose_wider_than: <integer | null>
    # 未来扩展点（v1 不实现）:
    # transpose_selectors: <array of CSS selectors>
    # header_row_count: <integer | auto>
```

Fields:
- `transpose_wider_than`: integer column count threshold. When a table grid has more columns than this value, `_render_table()` SHALL transpose the grid before rendering. When `null` or absent, no transposition occurs.

#### Scenario: transpose-wider-than-10-enabled

- **WHEN** `table_options.transpose_wider_than` is set to `10`
- **AND** a table grid has 22 columns and 15 rows
- **THEN** the table SHALL be transposed to 15 columns × 22 rows before rendering
- **AND** the original row headers (e.g., "Health", "Damage") become transposed column headers

#### Scenario: transpose-not-triggered

- **WHEN** `table_options.transpose_wider_than` is set to `10`
- **AND** a table grid has 5 columns and 3 rows
- **THEN** the table SHALL NOT be transposed
- **AND** it SHALL be rendered in its original orientation

#### Scenario: transpose-wider-than-absent

- **WHEN** `table_options` is absent from the strategy or `transpose_wider_than` is not set
- **THEN** no transposition SHALL occur for any table
- **AND** all tables SHALL be rendered in their original orientation

#### Scenario: transpose-wider-than-zero

- **WHEN** `table_options.transpose_wider_than` is set to `0`
- **THEN** all tables with at least 1 column SHALL be transposed (effectively enabling global transpose)

### Requirement: transpose-grid-method

`HtmlToMarkdownConverter._transpose_grid(grid)` SHALL be a static method that transposes a 2D grid (`list[list[str]]`), treating the first `header_row_count` rows as headers that become the first columns in the transposed result.

The method SHALL:
1. Accept `grid` (list of equal-length rows) and `header_row_count` (default 1)
2. Compute the transposed grid where `result[j][i] = grid[i][j]`
3. Merge multi-row headers: when `header_row_count > 1`, concatenate header values from multiple rows into a single header column using ` → ` as the separator (e.g., row 1 "Rebirth" + row 2 "Isaac" + row 3 "Judas" → `"Rebirth → Isaac → Judas"`)
4. The original row labels (from column 0 of data rows) become column headers in the transposed result
5. The merged multi-row headers become the row labels in the transposed result

#### Scenario: transpose-2x3-grid

- **WHEN** transposing `[["A", "B", "C"], ["1", "2", "3"]]` with `header_row_count=1`
- **THEN** result SHALL be `[["A", "1"], ["B", "2"], ["C", "3"]]`

#### Scenario: transpose-with-multi-row-header

- **WHEN** transposing:
  ```
  [
    ["",    "Rebirth", "Rebirth"],
    ["Stat", "Isaac",   "Magdalene"],
    ["HP",   "❤❤❤",    "❤❤❤❤"],
  ]
  ```
  with `header_row_count=2`
- **THEN** result SHALL be:
  ```
  [
    ["Stat → Rebirth", "HP"],
    ["Isaac → Rebirth", "❤❤❤"],
    ["Magdalene → Rebirth", "❤❤❤❤"],
  ]
  ```
- **AND** empty header cells SHALL be omitted from the merge (e.g., "Rebirth" not " → Rebirth")

#### Scenario: transpose-empty-grid

- **WHEN** grid is `[]`
- **THEN** result SHALL be `[]`

### Requirement: boi-characters-strategy-config

The BOI wiki strategy at `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` SHALL include `table_options.transpose_wider_than: 10` in its `extraction` block, enabling transpose for the Characters page's 22-column stat table.

#### Scenario: characters-page-table-transposed

- **WHEN** converting the Characters page HTML with the updated BOI strategy
- **THEN** the character stat tables (22–20 columns) SHALL be transposed to ~15-column × 22-row orientation
- **AND** the output Markdown SHALL have characters as rows and stats as columns
- **AND** the unlock requirement table (2 columns, below threshold) SHALL NOT be transposed
