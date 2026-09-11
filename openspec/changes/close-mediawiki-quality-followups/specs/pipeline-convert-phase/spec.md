# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-convert-phase`
- 来源: `proposal.md` / 用户确认 4-capability 划分（本会话交互确认）。
- 变更类型: modified
- 用户确认摘要: 按清单生成 4 个 spec delta（extract-kernel / pipeline-convert-phase / pipeline / strategy）。

## 规范真源声明

本文件是该 capability 在本次 change 中的行为规范真源；design/tasks/verification 必须引用本文件，页面回写不得替代 spec delta。

## MODIFIED Requirements

### Requirement: conversion-output-format
Each incrementally written `.md` file SHALL contain the full page content including YAML frontmatter, heading, body, and card stats. The format SHALL be identical to what Assembly phase would produce for individual pages.

标题判定：HTML 路径 SHALL 仅以 **H1**（首个非空行以 `# ` 前缀开头）判定"正文已有标题"；以小节标题（如 `## Infobox`、`## Overview`）开头的正文 SHALL 仍被前置 `# {title}`。正文为空时 SHALL 输出仅含标题的页面。

卡片图注入：hero 图 URL SHALL 从页面渲染后的标记中解析（`_resolve_hero_image_url`）：优先 infobox 容器（`extraction.infobox.selector`）内首个图片，其次正文首个图片；协议相对 `//` 归一为 `https:`；跳过非 `http(s)` 源（含 lazy-load `data:` 占位）；无可用图时 SHALL 省略注入而非输出死链。SHALL NOT 从 wiki 域名构造文件路径 URL（`/images/{name}` 与 `/Special:Redirect/file/{name}` 在 Cloudflare 保护的 Fandom 站上均返回 challenge 页）。

wikitext 路径回退：wikitext 页的 raw 内容不含 `html` 键而含 `rendered_html`（见 acquisition.py），hero 解析 SHALL 以 `html or rendered_html` 为输入，保持既有注入行为不回退。

语义版本：转换语义发生配置外变化时 SHALL bump `CONVERTER_CONTRACT_REVISION`（本次 2→4；跳过 3 是有意的——本地缓存已存在 rev-3 指纹的产物，直接提交 3 会导致 resume 静默复用旧 hero 形式的 markdown）。

#### Scenario: output-content-integrity
- **WHEN** a page is incrementally written
- **THEN** the file content SHALL match exactly what `run_assemble()` would produce for that page

#### Scenario: section-heading-still-gets-h1
- **WHEN** 转换后的正文首个非空行以 `## Infobox` 或 `## Overview` 开头
- **THEN** 输出 SHALL 在其前前置 `# {title}`，页面不缺失 H1 标题

#### Scenario: existing-h1-not-duplicated
- **WHEN** 正文首行已是 `# {title}` 形式的 H1
- **THEN** 输出 SHALL NOT 重复前置标题

#### Scenario: hero-image-resolved-from-markup
- **WHEN** 页面渲染 HTML 的 infobox 容器内存在 `src` 为 `https://static.wikia.nocookie.net/...` 的图片
- **THEN** hero 图 URL SHALL 为该 CDN URL（协议相对形式归一为 `https:`）
- **AND** SHALL NOT 为 wiki 域名下构造的 `/images/` 或 `/Special:Redirect/file/` 路径

#### Scenario: hero-image-omitted-when-unusable
- **WHEN** 页面无可用的 http(s) 图片（仅 `data:` 占位或无图）
- **THEN** 输出 SHALL 省略 hero 图注入，不产生死链

#### Scenario: wikitext-path-keeps-hero-injection
- **WHEN** wikitext 路径页的 raw 含 `rendered_html` 与非空 `images`（动态页）
- **THEN** hero 解析 SHALL 以 `rendered_html` 为输入并照常注入，不因 `html` 键缺失而静默丢弃

#### Scenario: revision-bump-invalidates-stale-markdown
- **WHEN** converter 语义变化且 `CONVERTER_CONTRACT_REVISION` 已 bump（2→4）
- **THEN** rev-3 指纹的既有缓存 SHALL 失配，页面 SHALL 重新转换而非复用旧 markdown
