# Proposal

## 问题定义

当前 `HtmlToMarkdownConverter._render_table()` 对包含 `colspan`/`rowspan` 属性的 HTML 表格采用简单 fallback 逻辑：将每行摊平为 `- cell1 | cell2 | cell3 | ...` 的列表项，完全丢失表头层级和行列对齐关系。

**具体案例**：BOI wiki Characters 页面的角色属性表（29 行 × 22 列），表头使用 `rowspan=3`/`colspan=13` 等合并单元格表达 DLC → 角色 → 子角色的三层结构，数据区每行对应一个属性维度（Health/Damage/Tears/...）。当前 fallback 输出完全不可读（参见 `outputs/test-100-fixed/characters/index.md`）。

**根因**：
1. `_is_simple_markdown_table()` 检测到 colspan/rowspan ≠ 1 或行宽不一致时返回 `False`
2. fallback 分支将多列表格摊平为一维列表，不保留任何结构化语义
3. 缺少 colspan/rowspan 感知的网格归一化解析能力

**经过 follow-up 修复（2026-05-20）确认的附加根因**（已在本次 change 中一并修复）：
4. `_BLOCK_TAGS` 不包含 `"article"` 和 `"section"`，导致 tabber `<section>` wrapper 被当作内联元素渲染，两个 `<article>` 的表格输出被空格拼接
5. `_build_table_grid` 使用 `node.css("tr")` 获取所有后代 `<tr>`（含嵌套子表格行），且 `_render_inline_children` 会递归渲染嵌套 `<table>` 为 cell 内容

## 范围边界

### 在范围内

- **converter 通用层**：新增 `_build_table_grid()` 方法，将任意 HTML `<table>`（含 colspan/rowspan）解析为等宽二维网格
- **converter 通用层**：新增 `_render_grid_as_table()` 方法，将网格渲染为标准 Markdown 表格
- **converter 通用层**：新增 `_transpose_grid()` 静态方法，支持行列转置
- **策略配置**：在 `extraction.table_options` 中新增 `transpose_wider_than`（列数阈值）配置项，超过阈值的表格自动转置
- **converter 重构**：`_render_table()` 切换为基于网格解析的新流程，删除旧的 `_is_simple_markdown_table()` 和 fallback 逻辑
- **BOI 策略**：为 Characters 页面配置 `table_options.transpose_wider_than: 10`，使 22 列表格转置为纵向表

### 在范围外

- 不增加 CSS-selector 级别的逐表选择性转置（v1 仅支持全局阈值）
- 不修改 wikitext 解析路径（`wikitext_to_md.py`）
- 不新增 Markdown 表格格式选项（如 GFM alignment、多行表头语法）

### 已处理

- ~~不处理 `<table>` 内部的嵌套表格~~（**已证伪**：MediaWiki server-rendered HTML 中确实存在嵌套 `<table>`，如 Characters 页面的 tabber `<article>` wrapper 结构。已通过 `_BLOCK_TAGS` 扩展 + `_build_table_grid` 直接子 `<tr>` 过滤 + `_render_cell_content` 跳过嵌套表格渲染三处修复解决）

## Capabilities

### New Capabilities

- `table-grid-parser`: colspan/rowspan-aware HTML table to normalized 2D grid parser in HtmlToMarkdownConverter
- `table-transpose-config`: strategy-driven table transpose via `extraction.table_options.transpose_wider_than` threshold config

### Modified Capabilities

- `pipeline-converters`: HtmlToMarkdownConverter._render_table() refactored to use grid-based parsing; old _is_simple_markdown_table() and fallback removed

## Capabilities 待确认项

- [x] 能力清单已与用户确认（转置阈值 `> 10 列`，converter 通用层增强 + strategy 配置驱动）

## Impact

| 影响面 | 说明 |
|--------|------|
| **converter.py** | 新增 ~80 行（`_build_table_grid`、`_render_grid_as_table`、`_transpose_grid`），删除 ~30 行（`_is_simple_markdown_table` + fallback），净增 ~50 行 |
| **strategy.md** | 新增 ~6 行 `extraction.table_options` 配置块 |
| **向后兼容** | 简单表（无 colspan/rowspan、等宽行）通过网格路径渲染，输出与旧逻辑一致 |
| **其他页面** | `transpose_wider_than` 默认不启用，仅显式配置的策略页面受影响；复杂表（如 Items list page 中的统计表）从网格解析中自动受益 |
| **测试** | 需新增 `converter_tests.py` 中的 colspan/rowspan/transpose 单元测试；需运行 `boi-100-baseline.sh` 验证回归 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/pipeline-converters/spec.md`
  - 项目页：`scripts/lib/extraction/converter.py`、`sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 回写目标：同上两个文件
