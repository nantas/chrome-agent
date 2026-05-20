# Design

## Context

pipeline 的 convert 阶段和 link resolution 存在两个独立但相关的 gap：
1. `LinkResolver.resolve()` 在 manifest 外的 fallback 生成不存在的 `.md` 路径
2. wiki 重定向页被完整转换后产出空文件

参考实现：`fandom_html_to_markdown.py` 的 `_resolve_wiki_link()` 已正确处理 fallback 到 wiki URL。

## Goals / Non-Goals

**Goals:**
- 不在 manifest 中的 wiki 内部链接回退到原始 wiki URL
- convert 阶段检测 redirect 页面，跳过产出，不生成空 .md 文件
- redirect 映射可被后续 link resolution 使用（指向 redirect 源的链接自动解析到目标）

**Non-Goals:**
- 在 discovery/fetch 阶段通过 API `redirects` 参数预过滤（后续 change）
- 修改 manifest 构建流程
- 修改 fandom converter（已有正确行为）

## Decisions

### D1: Redirect 检测在 convert phase 入口处执行

**选择**：在 `convert.py` 的页面处理循环中，对每个页面的 `rendered_html` 做 redirect 检测，优先于 `convert_single_page()` 调用。

**理由**：
- 检测逻辑简单（字符串匹配 `redirectMsg`），开销可忽略
- 在最上层拦截，避免空内容传播到后续 assembly 和 validation 阶段
- 可在此处提取 redirect 目标标题，构建 redirect map 供 link resolution 使用

**替代方案**：在 `HtmlToMarkdownConverter` 内部检测 — 会导致 converter 需要了解 redirect 语义，职责不清晰。

### D2: Redirect 映射注入 LinkResolver

**选择**：convert phase 构建 `redirect_map: dict[str, str]`（source_title → target_title），作为参数传入 `LinkResolver.convert_links()`。

**理由**：
- LinkResolver 已有 manifest 查找逻辑，redirect 解析是自然扩展
- 注入方式与现有 manifest_pages 参数模式一致
- 保持 LinkResolver 无状态（每次调用传入映射）

### D3: Fallback URL 使用构造时的 domain

**选择**：两个 LinkResolver 的 `__init__` 已接收 `domain` 参数，直接使用 `self._domain` 构建 fallback URL。

**理由**：
- 无需新增参数或全局状态
- domain 在 pipeline 启动时已确定并传入

### D4: Redirect 页面不生成任何文件

**选择**：redirect 页面完全不写入 .md 文件，pipeline state 中标记 `status: "redirect"`。

**理由**：
- 空文件无价值，且会被 validation 标记为 `empty_or_frontmatter_only`
- 不生成文件比生成占位文件更清晰
- 指向 redirect 源的链接通过 redirect map + resolver fallback 自动修正

## Risks / Migration

| 风险 | 缓解措施 |
|------|---------|
| redirect 检测误判（非标准 redirect HTML） | 检测条件放宽：匹配 `redirectMsg` class 或 `<a href="/wiki/...">` 在 redirectMsg 容器内 |
| redirect 链断裂（目标也不在 manifest 中） | D2 + resolver fallback 双重保障：先查 redirect map 到目标，再走正常 manifest 查找，最后 fallback 到 wiki URL |
| `link_fixer.py` 的 step 4 仍试图修复 resolver fallback 生成的 URL | wiki URL 以 `https://` 开头，fixer 的 `fix_unresolved_md_link` 只处理不以 `http` 开头的路径，天然跳过 |
| 现有 baseline 数值变化 | 正向变化：empty files 减少、broken links 减少。需 `--update-baseline` 更新 |
