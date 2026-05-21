# Design

## Context

`infobox.py` 的 `_extract_selectolax()` 是 pipeline 路径下 infobox 表格渲染的唯一实现。它接收 `render_inline_children_fn` 回调来渲染单元格内容，但调用时未传入 `source_dir`，导致所有链接基于根目录计算相对路径。

## Goals / Non-Goals

**Goals:**
- Infobox 表格内的 wiki 内部链接使用正确的相对路径（与正文一致）
- 参数透传，保持向后兼容（默认值 `""`）

**Non-Goals:**
- 修改 BS4 路径（explore 专用，不经过 pipeline）
- 修改 `link_fixer.py`
- 修改 `_to_markdown_link()` 本身

## Decisions

### D1: source_dir 在 infobox 调用链中逐层透传

**选择**：从 `_render_infobox_table()` → `extract_infobox()` → `_extract_selectolax()` → `render_inline_children_fn()` 逐层加参数。

**理由**：
- 最小改动，4 处签名修改，无逻辑变更
- 与已有 `source_dir` 在 converter 中的透传模式一致
- 默认值 `""` 保持现有调用方不受影响

### D2: 不修改 BS4 路径

**选择**：`_extract_bs4()` 不接收 `source_dir`，`extract_infobox()` 只在 selectolax 分支透传。

**理由**：
- BS4 路径用 `base_url` 拼接完整 URL，不涉及相对路径计算
- explore 路径不需要 manifest 感知的链接解析

## Risks / Migration

| 风险 | 缓解措施 |
|------|---------|
| 外部调用方 `extract_infobox()` 签名变更 | 新参数有默认值 `""`，无破坏性 |
| 遗漏其他调用点 | LSP references 确认 `extract_infobox` 和 `_extract_selectolax` 的所有调用方 |
| source_dir 为空时的行为 | 与变更前一致，空字符串 = 根目录 |
