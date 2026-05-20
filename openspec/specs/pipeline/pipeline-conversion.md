# Pipeline Domain: Conversion — Merged Spec

## Source Attribution

| Source Spec | Type |
|------------|------|
| `pipeline-convert-phase` | frozen |
| `pipeline-converters` | frozen |
| `pipeline-fetch-phase` | frozen |
| `unified-link-fixer` | frozen |
| `page-assignment` | frozen |
| `page-content-cache` | frozen |
| `mediawiki-cleanup-script` | frozen |
| `tooltip-icon-link-merge` | frozen |

Paths have been updated to reflect the current directory structure.

---

# Pipeline Conversion Specification

## Purpose

Defines the fetch and convert phases, HTML-to-Markdown conversion, converter delegation, link fixing, page assignment, content caching, MediaWiki cleanup, and tooltip icon-link merge preprocessing.

---

## Requirements

### Requirement: fetch-phase-cli-entry

系统 SHALL 支持 `--phase fetch` CLI 参数。行为：使用 manifest 遍历页面，缓存跳过已有页面，获取缺失页面的原始内容并写入缓存。新增 `--re-fetch` flag 强制重新获取。

#### Scenario: fetch-with-cache-skip
- **WHEN** 执行 `--phase fetch --from-manifest <path>` 且某页面已缓存
- **THEN** SHALL 跳过该页面

#### Scenario: fetch-with-re-fetch
- **WHEN** 执行 `--phase fetch --re-fetch`
- **THEN** SHALL 忽略已有缓存，重新获取所有页面

### Requirement: fetch-phase-incremental

`--phase fetch` 支持增量获取：仅获取缓存缺失的页面。

#### Scenario: incremental-fetch
- **WHEN** manifest 中 1757 个已缓存、12 个缺失
- **THEN** SHALL 仅对 12 个缺失页面发起 API 请求

### Requirement: fetch-phase-error-handling

单个页面 fetch 失败 SHALL NOT 阻断其余页面。

#### Scenario: single-page-fetch-failure
- **WHEN** 页面 fetch 失败
- **THEN** 后续页面继续 fetch，日志记录失败原因

### Requirement: fetch-phase-rate-limiting

fetch phase SHALL 使用与当前 `run_phase_b()` 相同的 `RateLimitConfig` 和 `ThreadPoolExecutor` 并发控制。

### Requirement: fetch-phase-resume

fetch phase 通过缓存文件存在性判断是否已完成 fetch，无需额外状态追踪。

#### Scenario: resume-after-interruption
- **WHEN** 前次 fetch 中途被中断
- **THEN** 重新执行时 SHALL 跳过已有缓存的页面

### Requirement: fetch-phase-summary

fetch 完成后 SHALL 输出摘要：总页面数、成功数、跳过数、失败数。

### Requirement: convert-phase-cli-entry

系统 SHALL 支持 `--phase convert` CLI 参数。要求必须提供 `--from-manifest`。行为：从缓存读取原始内容，执行 HTML→Markdown 转换，完成后自动执行 assembly。

#### Scenario: convert-without-manifest
- **WHEN** 执行 `--phase convert` 但未提供 `--from-manifest`
- **THEN** SHALL 报错退出

#### Scenario: convert-with-manifest
- **WHEN** 执行 `--phase convert --from-manifest <path>`
- **THEN** SHALL 加载 manifest 并对每个页面执行转换

### Requirement: convert-from-cache

convert phase SHALL 从缓存文件读取原始内容，不发起 API 请求。

MediaWiki 路径：读取 `<cache_root>/<safe_title>.json`，构造 raw dict。
Scrapling 路径：读取 `<cache_root>/<slug>.html`。

#### Scenario: mediawiki-convert-from-cache
- **WHEN** convert 页面 `The Lamb` 且缓存存在
- **THEN** SHALL 读取 JSON 文件并执行转换，SHALL NOT 发起 HTTP 请求

### Requirement: convert-cache-miss-handling

缓存文件不存在时 SHALL 标记为 `"status": "error", "error": "cache_miss"`，SHALL NOT 回退到 API 请求。

### Requirement: convert-phase-no-network

convert phase SHALL NOT 发起任何网络请求。

### Requirement: convert-strategy-extraction-config

convert phase SHALL 使用 strategy 文件的 `extraction.*` 配置执行转换。修改 `extraction` 规则后重新执行 convert SHALL 产出反映新规则的输出。

#### Scenario: extraction-config-change
- **WHEN** strategy 的 `extraction.cleanup_selectors` 新增选择器后重新执行 convert
- **THEN** 新 Markdown SHALL 应用新规则，SHALL NOT 发起 API 请求

### Requirement: convert-phase-summary

convert 完成后 SHALL 输出摘要：总页面数、成功转换数、缓存缺失数、失败数、重定向跳过数。

### Requirement: link-resolver-fallback-to-wiki-url

当 LinkResolver.resolve() 的 target 不在 manifest 中时（即所有查找策略均未匹配），SHALL 返回 `[display](https://{domain}/wiki/{target_slug})` 而非裸 `.md` 相对路径。此行为 SHALL 同时应用于 ExactTitleLinkResolver 和 ShortNameLinkResolver。

#### Scenario: unresolved-link-falls-back-to-wiki-url
- **WHEN** LinkResolver 处理 target "Ending 16" 且不在 manifest pages 中
- **THEN** SHALL 返回 `[Ending 16](https://{domain}/wiki/Ending_16)`

#### Scenario: manifest-match-still-relative-path
- **WHEN** target 在 manifest 中
- **THEN** SHALL 继续返回相对 .md 路径

### Requirement: convert-phase-redirect-detection

convert phase SHALL 在处理每个页面前检测 wiki 重定向标记。当 HTML 包含 `redirectMsg` class 时，SHALL 跳过该页面，不生成 .md 文件，在 pipeline state 中标记 `status: "redirect"`。redirect 映射 SHALL 被构建并注入到链接解析流程中。

#### Scenario: redirect-page-detected-and-skipped
- **WHEN** 页面 HTML 包含 `<div class="redirectMsg">`
- **THEN** SHALL 不生成 .md 文件
- **AND** SHALL 记录 redirect 映射 (source_title → target_title)

#### Scenario: redirect-links-resolved-via-map
- **WHEN** 其他页面链接到 redirect 源页面
- **THEN** SHALL 通过 redirect map 解析到目标页面（如目标在 manifest 中）或 wiki URL（如目标不在 manifest 中）

convert phase 完成后 SHALL 自动执行 assembly phase：写入 .md 文件、生成目录索引、执行链接修复。

### Requirement: public-conversion-api

`HtmlToMarkdownConverter.convert()` SHALL 作为公共函数暴露，接受 `html: str, wiki_domain: str, extraction_config: dict`，返回 `str`。

#### Scenario: public-api-standalone-call
- **WHEN** 外部代码调用 `convert_html_to_markdown(html, wiki_domain, extraction_config)`
- **THEN** SHALL 返回 Markdown 字符串，无需实例化 `HtmlToMarkdownConverter`

### Requirement: infobox-rendering-delegation

`HtmlToMarkdownConverter._render_infobox_table()` SHALL 将 infobox 渲染逻辑委托给共享模块 `lib/extraction/infobox.py`。

### Requirement: sample-converter-delegation

`sample_converter.py` SHALL 将 HTML→Markdown 转换委托给 `HtmlToMarkdownConverter`，不再使用 `markdownify.markdownify()`。

#### Scenario: explore-path-output-consistent
- **WHEN** `sample_converter.py::convert()` 处理的页面与 pipeline 处理相同页面
- **THEN** 两者输出 SHALL 有相同的 infobox 表格和内容结构

### Requirement: markdownify-dependency-cleanup

`sample_converter.py` 不再调用 `markdownify.markdownify()` 后，SHALL 移除相关 import 和依赖。

### Requirement: fix-links-in-directory

系统 SHALL 提供 `fix_links_in_dir(output_dir, domain, manifest_pages)` 扫描目录下所有 .md 文件，统一修复链接格式。

#### Scenario: convert-wiki-path-links
- **WHEN** .md 文件中存在 `/wiki/Title` 或 `https://domain/wiki/Title` 格式链接
- **THEN** SHALL 根据 manifest 查找目标文件，转换为相对 .md 路径

#### Scenario: preserve-fragment-anchors
- **WHEN** 链接包含 fragment
- **THEN** SHALL 剥离 fragment 用于查找，转换后附加

#### Scenario: strip-query-params
- **WHEN** 链接包含 query 参数
- **THEN** SHALL 剥离 query 参数用于查找

#### Scenario: fix-double-md-suffix
- **WHEN** 链接以 `.md.md` 结尾
- **THEN** SHALL 去除双重后缀

#### Scenario: fix-unresolved-relative-links
- **WHEN** 相对链接对应文件不存在
- **THEN** SHALL 尝试在 manifest 中查找匹配页面并修正路径

### Requirement: cli-fix-links-subcommand

CLI SHALL 提供 `fix-links` 子命令。

#### Scenario: cli-fix-links
- **WHEN** 执行 `python3 -m scripts.pipeline fix-links <dir> --domain <d> --manifest <path>`
- **THEN** SHALL 扫描并修复链接，输出修复统计

### Requirement: priority-chain-assignment

系统 SHALL 按优先级链将页面分配到输出目录：manual overrides → category page members → MW category tag matching。

### Requirement: mw-category-batch-lookup

系统 SHALL 通过 `action=query&prop=categories` 批量查询 MW 分类标签（每批 50 个 title）。

### Requirement: assignment-priority-ordering

`api.homepage.assignment_priority` 为有序列表，较早条目优先级更高。

### Requirement: manifest-enrichment

分配完成后，每个 manifest 页面条目 SHALL 包含 `assigned_category`、`mw_categories`、`assignment_method`。

### Requirement: excluded-categories-not-in-input

`assign_pages()` SHALL 不接收已被排除分类的页面数据。

### Requirement: cache-root-location

系统 SHALL 使用 `<repo_root>/.cache/<platform>/<domain>/` 作为缓存根目录。`<platform>` 从 `api.platform` 读取（Scrapling 路径使用 `"scrapling"`），`<domain>` 来自 strategy 的 `domain` 字段。

#### Scenario: mediawiki-cache-path
- **WHEN** `api.platform` 为 `"mediawiki"` 且 `domain` 为 `"bindingofisaacrebirth.wiki.gg"`
- **THEN** 缓存根目录为 `<repo_root>/.cache/mediawiki/bindingofisaacrebirth.wiki.gg/`

### Requirement: mediawiki-cache-file-format

MediaWiki 缓存为 JSON 格式（`.json` 后缀），文件名使用 MediaWiki 风格 sanitize。包含字段：`title`、`wikitext`、`html`、`rendered_html`、`images`、`fetched_at`、`content_acquisition`、`base_url`。

### Requirement: scrapling-cache-file-format

Scrapling 缓存包含 `<slug>.html`（原始 HTML）和 `<slug>.meta.json`（元数据）。

### Requirement: cache-existence-check

系统 SHALL 提供 `is_cached(domain, title) -> bool`。

### Requirement: cache-list-pages

系统 SHALL 提供 `list_cached_pages(domain) -> set[str]`。

### Requirement: cache-cross-session-reuse

缓存文件不绑定特定 pipeline run，同一 repo 内任意 session 的 fetch/convert 可使用同一缓存。

### Requirement: cache-gitignore

`.cache/` 目录 SHALL 被 `.gitignore` 排除。

### Requirement: Site-Strategy 分流

系统 SHALL 提供基于站点标识符的 cleanup 脚本，应用对应 rule profile（`vampire-survivors`、`balatro`、`generic-mediawiki`）。

### Requirement: 噪音规则聚类

Cleanup 规则按四个集群组织：navigation、template、link、table。每个集群的规则可按 profile 独立启用/禁用。

### Requirement: 站点 Profile 映射

系统定义站点标识符到启用规则的映射：`vampire-survivors`、`balatro`、`generic-mediawiki` 各有不同规则集。

### Requirement: merge-tooltip-icon-text-links

系统 SHALL 提供 `merge_tooltip_links(html: str) -> str`，识别 MediaWiki tooltip 模式，将 icon+text 配对链接合并为单个组合链接。

处理步骤：
1. 移除 `<span class="tooltip" ...>` 开标签
2. 移除 `<span style="--tb-icon-size: ...">` 开标签
3. 移除所有 `</span>` 闭标签
4. 识别连续相同 href 的 `<a>` 配对（第一个含 `<img>`，第二个含文本）
5. 合并为 `<a href="URL"><img.../> Text</a>`

#### Scenario: merge-standard-tooltip-item-link
- **WHEN** 处理标准 tooltip pattern
- **THEN** 输出 SHALL 为合并后的单个 `<a>` 标签

#### Scenario: no-merge-different-href
- **WHEN** 两个连续 `<a>` 的 href 不同
- **THEN** SHALL 不合并

### Requirement: merge-before-image-conversion

tooltip merge SHALL 在 `convert_images_to_md()` 之前执行。
