# Design

## Context

当前 `HtmlToMarkdownConverter._render_table()` 对含 colspan/rowspan 的表格采用列表化 fallback，产生不可读输出。本次 change 引入 colspan/rowspan 感知的网格解析器，并通过 strategy 配置支持宽表转置。

**输入规范**：
- `specs/table-grid-parser/spec.md` — 网格解析与渲染行为
- `specs/table-transpose-config/spec.md` — 策略驱动的转置行为
- `specs/pipeline-converters/spec.md` — converter 重构与删除项

## Goals / Non-Goals

**Goals:**

- 所有 HTML 表格（含 colspan/rowspan）渲染为标准 Markdown 表格
- 策略可配置转置阈值，超过 N 列的宽表自动转置
- 删除旧的 `_is_simple_markdown_table()` 和列表 fallback
- 简单表（无 colspan/rowspan）输出与重构前一致
- BOI Characters 页面角色属性表可读

**Non-Goals:**

- 不支持逐表选择性转置（v1 仅全局阈值）
- 不修改 wikitext 解析路径
- 不支持 GFM 对齐语法（`:---:`, `---:`）

## Decisions

### Decision 1: 网格构建算法 — col_spans 字典追踪

**选择**: 使用 `dict[int, tuple[int, str]]`（col_index → (remaining_rows, content)）追踪跨行单元格。
**备选**: 预分配 `list[list[str|None]]` 全网格 + 填充。
**理由**: selectolax 是流式遍历，不适合预知网格宽度。字典追踪配合两轮扫描（第一轮确定 max_cols 上限，第二轮逐格填充）更简洁。但最终简化为单轮：遍历时动态扩展 row 宽度，max_cols 在遍历完成后确定。
**实际实现**: 单轮遍历，每行使用 `col_spans` 字典检查已占用列，跳过 occupied columns，消费当前 `<th>`/`<td>`，将 colspan 内容写入当前行、rowspan 注册到 `col_spans`。

### Decision 2: 表头行数检测

**选择**: 遍历网格首行，检测是否有 `<th>` 标记。如果第一行的 `tr` 中包含 `<th>` 子元素，`header_row_count = 1`；否则 `header_row_count = 0`。
**备选**: 从 HTML 直接读取（在 `_render_table` 层判断，传入 grid 构建器）。
**理由**: `_build_table_grid()` 遍历 `<tr>` 时可同时判断每行是否有 `<th>`。对于多行表头（如 Characters 表格的 3 行 header），由调用方在 `_render_table()` 中通过原始 DOM 判断：连续的前 N 行均为 `<th>` 即 `header_row_count = N`。简化实现：在 `_render_table()` 中遍历 `<tr>` 子节点直到遇到首个含 `<td>` 的行，即确定 `header_row_count`。

**实现**: 
```python
header_row_count = 0
for row_node in node.css("tr"):
    if any(child.tag == "th" for child in self._child_nodes(row_node)):
        has_td = any(child.tag == "td" for child in self._child_nodes(row_node))
        if has_td:
            break  # mixed row — stop counting
        header_row_count += 1
    else:
        break
```

### Decision 3: 转置时表头合并方式

**选择**: 多行表头转置时，将同一列的多个 header 值用 ` → ` 连接，空值跳过。
**理由**: 
- ` → ` 在 Markdown 中不需要转义，视觉上清晰表达层级关系
- 例: `"Rebirth → Isaac → Judas"` 清晰表达 DLC → 角色 → 子角色 三层结构
- 空 header cell（如 row 1 col 0 的 `""`）在合并时跳过，不产生前导 ` → `

### Decision 4: 编辑器改动范围

**选择**: 所有新方法添加到 `HtmlToMarkdownConverter` 类内部，不创建独立模块。
**理由**:
- 新方法（`_build_table_grid`、`_render_grid_as_table`、`_transpose_grid`）是 converter 的紧密内部实现
- 保持与现有 `_render_inline_children()` 等方法的直接调用关系
- `_transpose_grid` 声明为 `@staticmethod`（不依赖实例状态），便于独立测试

### Decision 5: strategy schema 扩展方式

**选择**: 在 `extraction` 块中新增 `table_options` 子对象，不在 `api` 块中修改。
**理由**:
- `extraction` 已有 `selectors`、`image_handling`、`cleanup`、`infobox` 等提取相关配置
- 表格渲染属于提取行为，归属于 `extraction` 语义上最自然
- 与现有 `infobox` 配置并列为 `extraction` 的子配置

### Decision 7: `_BLOCK_TAGS` 扩展 — 添加 `article` 和 `section`

**选择**: 将 `"article"` 和 `"section"` 加入 `_BLOCK_TAGS` 集合。
**备选**: 仅在 `_has_block_children` 中特殊处理，或仅在 `_render_block` 中添加 article/section 路由。
**理由**: HTML5 语义元素 `<article>` 和 `<section>` 是明确的 block-level 容器。wiki.gg 的 tabber widget 使用 `<section>` → `<article>` 结构包裹标签页内容，每个 `<article>` 内包含独立的 `<table>`。若这些标签不在 `_BLOCK_TAGS` 中，`_has_block_children(section)` 返回 `False`，导致 `<section>` 被当作内联元素渲染，两个 `<article>` 的表格输出被 `_join_inline_parts` 用空格拼接，产生不可预期的行合并。
**实际实现**: 修改 `_BLOCK_TAGS` 集合定义（一行改动）。

### Decision 8: 嵌套表格处理 — 三管齐下

**选择**: 通过三个独立机制防止嵌套表格污染外层 grid：
1. `_build_table_grid` 只收集直接子 `<tr>`（`_child_nodes` 遍历），替代 `node.css("tr")` 的全后代查找
2. 新增 `_render_cell_content` 方法，在检测到 cell 内包含嵌套 `<table>` 时跳过其递归渲染，仅保留非表格内联子元素的文本内容
3. 当跳过嵌套表格时记录 WARNING 级别日志

**备选**: 方案 A（仅过滤 cell 内容）、方案 B（在 `_render_inline` 中传递上下文标志）。
**理由**: `node.css("tr")` 使用 selectolax CSS 选择器会匹配所有后代 `<tr>`，包括嵌套表格的行。仅过滤 cell 内容不足以保证 grid 结构正确性（嵌套行仍会混入 grid）。传递上下文标志方案改动面大且脆弱。`_child_nodes` 遍历 + cell 内容过滤是安全、最小化的方案。
**风险**: 嵌套表格数据丢失 — 但 Characters 页面中嵌套表格的数据已在独立的 Tainted Characters 表格中完整捕获，无信息损失。

### Decision 6: 安全上限

**选择**: `max_cols` 上限设为 200，超出则 log warning 并截断。
**理由**: 实际 wiki 表格都不会超过 50 列，200 已足够安全。极端情况下防止无限循环或内存问题。

## Risks / Migration

| 风险 | 影响 | 缓解 |
|------|------|------|
| 复杂表网格构建 bug 导致输出为空 | 页面丢失表格内容 | 单元测试覆盖 Characters 表（22 列）、混合 colspan/rowspan、空表、单列表；回归测试用 `boi-100-baseline.sh` |
| `_is_simple_markdown_table` 删除影响简单表 | 简单表输出变化 | 网格路径对简单表输出与旧逻辑等价；单元测试验证 |
| 转置后列数变化导致表过宽 | 转置后表可能仍有 15+ 列 | 这是预期行为（纵向表天然适合 Markdown 宽度）；若仍过宽，后续可加 `max_transposed_cols` 限制 |
| 策略新增字段导致旧版本 parser 报错 | 向前兼容 | `table_options` 为可选字段，未配置时行为不变 |
| `header_row_count` 检测不准确 | 混合 th/td 行被误判 | 使用 has_td 检测终止点；对于奇葩表格（首行 td 但后面又 th），宁可保守（header_row_count=0） |
