# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-convert-phase`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: handoff P-2 修复——Convert 阶段逐页增量写 .md 文件

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: incremental-page-write
The `run_convert()` function SHALL write each successfully converted page's `.md` file to the output directory immediately after conversion, rather than batching all writes to the end of the phase.

#### Scenario: page-written-immediately-after-conversion
- **WHEN** `run_convert()` converts page "The_Sad_Onion" successfully
- **THEN** the file `<output_dir>/items/the_sad_onion.md` SHALL exist on disk immediately
- **AND** subsequent pages can be converted even if the process is interrupted

#### Scenario: directory-auto-created
- **WHEN** a page's `target_directory` is `"items"` and `<output_dir>/items/` does not exist
- **THEN** the directory SHALL be created before writing the file

#### Scenario: conversion-result-still-in-memory
- **WHEN** incremental write is enabled
- **THEN** the `results` dict SHALL still be populated in memory for downstream Assembly phase consumption
- **AND** the `extraction_results.json` SHALL still be written at the end of the convert phase

### Requirement: skip-already-converted-pages
Resume SHALL skip a page only when its completed state, expected output file, compatible raw input, and persisted conversion fingerprint all match the current request. The fingerprint SHALL cover raw conversion payload, semantic conversion configuration, acquisition mode, target/link context and converter contract revision. Missing legacy fingerprints SHALL require reconversion; filename presence alone SHALL NOT prove freshness. Disabled resume SHALL always reconvert valid inputs.

#### Scenario: resume-skip-converted-page
- **WHEN** resume is enabled and completed state, output, admitted raw input and fingerprint all match
- **THEN** the page SHALL skip conversion and be available to assembly as a valid result.

#### Scenario: changed-input-or-contract
- **WHEN** raw payload, extraction rules, target/link context, acquisition mode or converter revision changes, or a legacy completion lacks a fingerprint
- **THEN** resume SHALL NOT skip the page despite an existing Markdown file.

#### Scenario: force-reconvert-without-resume
- **WHEN** resume is disabled
- **THEN** every page with compatible raw content SHALL be converted regardless of completed state or existing output.

### Requirement: conversion-output-format
Each incrementally written `.md` file SHALL contain the full page content including YAML frontmatter, heading, body, and card stats. The format SHALL be identical to what Assembly phase would produce for individual pages.

标题判定：HTML 路径 SHALL 仅以 **H1**（首个非空行以 `# ` 前缀开头）判定"正文已有标题"；以小节标题（如 `## Infobox`、`## Overview`）开头的正文 SHALL 仍被前置 `# {title}`。正文为空时 SHALL 输出仅含标题的页面。

卡片图注入：hero 图 URL SHALL 从页面渲染后的标记中解析（`_resolve_hero_image_url`）：优先 infobox 容器（`extraction.infobox.selector`）内首个图片，其次正文首个图片；协议相对 `//` 归一为 `https:`，根相对 `/images/...` SHALL 以 `image_handling.base_url`（回退 wiki 域名，与 infobox 内核同序）补全为绝对 URL；跳过非 `http(s)` 源（含 lazy-load `data:` 占位）；无可用图时 SHALL 省略注入而非输出死链。SHALL NOT 从 wiki 域名构造文件路径 URL（`/images/{name}` 与 `/Special:Redirect/file/{name}` 在 Cloudflare 保护的 Fandom 站上均返回 challenge 页）。

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

#### Scenario: hero-image-root-relative-src-absolutized
- **WHEN** 渲染标记的图片 src 为根相对形式（wiki.gg 系 `/images/<name>.png`）
- **THEN** hero URL SHALL 以 `image_handling.base_url`（缺省时 wiki 域名）补全为绝对 URL 并照常注入

#### Scenario: hero-image-omitted-when-unusable
- **WHEN** 页面无可用的 http(s) 图片（仅 `data:` 占位或无图）
- **THEN** 输出 SHALL 省略 hero 图注入，不产生死链

#### Scenario: wikitext-path-keeps-hero-injection
- **WHEN** wikitext 路径页的 raw 含 `rendered_html` 与非空 `images`（动态页）
- **THEN** hero 解析 SHALL 以 `rendered_html` 为输入并照常注入，不因 `html` 键缺失而静默丢弃

#### Scenario: revision-bump-invalidates-stale-markdown
- **WHEN** converter 语义变化且 `CONVERTER_CONTRACT_REVISION` 已 bump（2→4）
- **THEN** rev-3 指纹的既有缓存 SHALL 失配，页面 SHALL 重新转换而非复用旧 markdown
## ADDED Requirements

### Requirement: cdp-path-uses-shared-kernel

The CDP execution path (`scripts/pipeline/pipeline/phases/convert_html.py`) SHALL use `scripts.lib.extraction.converter.convert_html_to_markdown()` with `wiki_domain=""` (empty string) for generic HTML-to-Markdown conversion. It SHALL NOT import or use `scripts.lib.extraction.html_to_markdown`.

The shared kernel (`scripts.lib.extraction.converter`) SHALL accept an empty `wiki_domain` and skip wiki-specific link handling (absolutization, `/wiki/` path resolution) when `wiki_domain` is empty.

#### Scenario: cdp-path-calls-converter
- **WHEN** `convert_html.py` converts an HTML page from the chrome-cdp cache
- **THEN** the conversion SHALL go through `HtmlToMarkdownConverter(wiki_domain="")`
- **AND** SHALL NOT go through `html_to_markdown()` (regex-based)
- **AND** no wiki-specific link resolution (no `/wiki/` prefixing, no host-based absolutization) SHALL be applied

#### Scenario: kernel-rejects-non-string-domain
- **WHEN** `HtmlToMarkdownConverter.__init__` receives `wiki_domain=None`
- **THEN** it SHALL raise `TypeError`
- **AND** `convert_html_to_markdown()` SHALL accept `wiki_domain=""` as a valid generic HTML signal

#### Scenario: cdp-converted-output-equivalent-to-pipeline
- **WHEN** the same HTML sample is converted via pipeline path (`convert.py` → `HtmlToMarkdownConverter`)
- **AND** also converted via CDP path (`convert_html.py` → `HtmlToMarkdownConverter`)
- **THEN** the two `.md` outputs SHALL be identical

### Requirement: mirror-equivalence-golden-snapshot
Self-contained `tests/test_convert_equivalence.py` SHALL prove matching-context byte equivalence through production and explore entries against the shared full-page kernel, as defined by `convert/spec.md`. It SHALL NOT depend on external cached fixtures.

#### Scenario: golden-snapshot-diff-is-zero
- **WHEN** embedded HTML and matching rules/context pass through both paths
- **THEN** the core Markdown SHALL be identical after removing only declared wrappers.

#### Scenario: golden-snapshot-fails-on-drift
- **WHEN** either mirror omits infobox, preprocessing or shared post-ops
- **THEN** the proof SHALL fail and identify the diverging path.

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_

## ADDED Requirements

### Requirement: conversion-cache-admission
Conversion SHALL use the shared admission rules before resume acceptance or dispatch. Incompatible/missing raw content SHALL produce a per-page error with remediation to run fetch; conversion-only execution SHALL NOT implicitly fetch or fall back to another acquisition mode. Failed pages SHALL NOT enter successful assembly or remain marked completed for the current request.

#### Scenario: offline-incompatible-cache
- **WHEN** convert-only runs with an HTML strategy and a wikitext-only hybrid cache
- **THEN** the page SHALL fail with `cache_incompatible` and expected/actual mode diagnostics, without network acquisition or old-mode conversion.

#### Scenario: stale-output-after-fetch-failure
- **WHEN** a page has an old Markdown file and replacement or forced fetch failed, even when its old cache was compatible
- **THEN** resume and assembly SHALL NOT treat that old file as a successful page of the current run.

## MODIFIED Requirements
