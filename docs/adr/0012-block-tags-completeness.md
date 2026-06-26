# 0012 — Decision: `_BLOCK_TAGS` Completeness Rule

## 状态

已接受（历史决策，从 docs/decisions/ 迁移至 docs/adr/）

## Context

`HtmlToMarkdownConverter._has_block_children()` 通过检查节点的直接子元素是否在 `_BLOCK_TAGS` 集合中来决定渲染路径：

- 如果 `True` → `_render_blocks(children)`，子块用 `\n\n` 分隔
- 如果 `False` → `_render_inline_children(node)`，子内容用 `_join_inline_parts` 拼接（空格分隔）

当 `_BLOCK_TAGS` 缺少 HTML5 语义块级元素（如 `<article>`、`<section>`）时，`_has_block_children()` 对其父容器返回 `False`，将块级内容错误地路由到内联渲染路径，导致相邻块的输出被拼接。

**实际案例**：wiki.gg 的 tabber widget 使用 `<section>` → `<article>` 结构包裹标签页，每个 `<article>` 包含独立的 `<table>`。缺少 `"article"` 和 `"section"` 导致两个表格的 Markdown 输出被空格拼接，表格最后一行与第二个表格的表头合并。

## Decision

1. **`_BLOCK_TAGS` 必须包含所有 HTML5 语义块级元素**。当前集合：`article`, `blockquote`, `div`, `h1`-`h6`, `hr`, `ol`, `p`, `pre`, `section`, `table`, `ul`。

2. **新增 block 标签时遵循 HTML5 标准**：任何在 [HTML Living Standard — Flow content](https://html.spec.whatwg.org/multipage/dom.html#flow-content) 中列为 block-level 的语义元素都应加入 `_BLOCK_TAGS`。

3. **`_has_block_children()` 只检查直接子元素**，不递归。这要求 `_BLOCK_TAGS` 包含所有可能的中间容器元素（如 `<article>`、`<section>`、`<div>`），而不仅仅是终端块元素（如 `<table>`、`<p>`）。

## Consequences

- **新增 HTML5 元素时**：必须先检查是否需要加入 `_BLOCK_TAGS`，否则可能导致结构错乱
- **调试入口**：当表格输出出现意外的行合并时，第一步检查目标元素是否在 `_BLOCK_TAGS` 中，第二步检查 `_has_block_children()` 的返回值
- **Selectolax 限制**：`node.css("tr")` 等 CSS 选择器会匹配所有后代元素，结构遍历应优先使用 `_child_nodes()`
