# page-content-cache Specification

## Purpose
持久化页面原始内容缓存层，按 `<platform>/<domain>/<safe_title>` 组织，存储 API 原始响应或 Scrapling 原始 HTML，支持跨 session 复用。platform 值直接从 strategy 配置读取（`api.platform` 或固定 `"scrapling"`），零映射转换。

## Requirements

### Requirement: cache-root-location
The system SHALL 使用 `<repo_root>/.cache/<platform>/<domain>/` 作为所有页面缓存的根目录。

`<platform>` 的推导规则：
- 若 strategy 存在 `api.platform` 字段，SHALL 直接使用其值（如 `"mediawiki"`）
- 若 strategy 不存在 `api.platform` 字段（Scrapling 路径），SHALL 使用固定值 `"scrapling"`

`<domain>` SHALL 来自 strategy 的 `domain` 字段。

#### Scenario: mediawiki-cache-path
- **WHEN** strategy 的 `api.platform` 为 `"mediawiki"` 且 `domain` 为 `"bindingofisaacrebirth.wiki.gg"`
- **THEN** 缓存根目录 SHALL 为 `<repo_root>/.cache/mediawiki/bindingofisaacrebirth.wiki.gg/`

#### Scenario: scrapling-cache-path
- **WHEN** strategy 无 `api.platform` 字段且 `domain` 为 `"example.com"`
- **THEN** 缓存根目录 SHALL 为 `<repo_root>/.cache/scrapling/example.com/`

### Requirement: mediawiki-cache-file-format
MediaWiki API 路径的页面缓存文件 SHALL 为 JSON 格式（`.json` 后缀），文件名使用 title 的 MediaWiki 风格 sanitize（空格→`_`）。

每个缓存文件 SHALL 包含以下字段：
- `title`: 页面标题（string）
- `wikitext`: wikitext 原文，无可为 `null`（string|null）
- `html`: `action=parse&prop=text` 返回的渲染 HTML，无可为 `null`（string|null）
- `rendered_html`: 与 `html` 同值（`html_rendered` 策略时）或 `null`（string|null）
- `images`: 页面关联图片列表（list|null）
- `fetched_at`: ISO 8601 获取时间戳（string）
- `content_acquisition`: 所用 acquisition 策略 ID（string，如 `"html_rendered"`）
- `base_url`: API 端点 URL（string）

#### Scenario: html-rendered-cache-entry
- **WHEN** 以 `html_rendered` 策略 fetch 页面 `The Lamb`
- **THEN** 缓存文件路径 SHALL 为 `.cache/mediawiki/<domain>/The_Lamb.json`
- **AND** `html` 和 `rendered_html` SHALL 为渲染后的 HTML 字符串
- **AND** `wikitext` SHALL 为 `null`
- **AND** `content_acquisition` SHALL 为 `"html_rendered"`

#### Scenario: wikitext-only-cache-entry
- **WHEN** 以 `wikitext_only` 策略 fetch 页面 `The Lamb`
- **THEN** `wikitext` SHALL 包含 wikitext 原文
- **AND** `html` 和 `rendered_html` SHALL 为 `null`
- **AND** `content_acquisition` SHALL 为 `"wikitext_only"`

### Requirement: scrapling-cache-file-format
Scrapling 路径的页面缓存 SHALL 包含两个文件：
- `<slug>.html`：Scrapling 下载的原始 HTML
- `<slug>.meta.json`：元数据 JSON，包含 `url`、`fetched_at`、`fetcher` 字段

`<slug>` SHALL 从 URL 路径推导，使用与当前 `urlToStructuredPath()` 一致的命名逻辑。

#### Scenario: scrapling-cache-entry
- **WHEN** Scrapling fetch URL `https://example.com/docs/intro`
- **THEN** 缓存 SHALL 包含 `docs_intro.html` 和 `docs_intro.meta.json`
- **AND** `meta.json` SHALL 记录 `fetcher` 为实际使用的 Scrapling fetcher 名称

### Requirement: cache-existence-check
The system SHALL 提供 `is_cached(domain, title) -> bool` 检查指定页面是否已有缓存。

MediaWiki 路径：检查 `<cache_root>/<safe_title>.json` 文件存在。
Scrapling 路径：检查 `<cache_root>/<slug>.html` 和 `<cache_root>/<slug>.meta.json` 均存在。

#### Scenario: cached-page-detection
- **WHEN** `.cache/mediawiki/bindingofisaacrebirth.wiki.gg/The_Lamb.json` 存在
- **THEN** `is_cached("bindingofisaacrebirth.wiki.gg", "The Lamb")` SHALL 返回 `true`

#### Scenario: uncached-page-detection
- **WHEN** 缓存文件不存在
- **THEN** `is_cached` SHALL 返回 `false`

### Requirement: cache-list-pages
The system SHALL 提供 `list_cached_pages(domain) -> set[str]` 返回指定 domain 下所有已缓存页面的 title 集合。

#### Scenario: list-cached-pages
- **WHEN** `.cache/mediawiki/bindingofisaacrebirth.wiki.gg/` 包含 `The_Lamb.json` 和 `Isaac.json`
- **THEN** `list_cached_pages` SHALL 返回 `{"The Lamb", "Isaac"}`

### Requirement: cache-cross-session-reuse
缓存文件 SHALL 不绑定到特定 pipeline run 或 output 目录。同一 repo 内任意 session 的 fetch/convert 操作 SHALL 使用同一缓存目录。

#### Scenario: cross-session-convert
- **WHEN** session A 执行 `--phase fetch` 填充缓存
- **AND** session B 执行 `--phase convert --from-manifest <path>` 数天后
- **THEN** session B SHALL 读取到 session A 写入的缓存文件

### Requirement: cache-gitignore
`.cache/` 目录 SHALL 被 `.gitignore` 排除，不进入版本管理。
