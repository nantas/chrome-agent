# Specification Delta

## Capability 对齐（已确认）

- Capability: `sitemap-driven-crawl`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 新增 sitemap-driven 静态文档站 crawl 管线。策略通过顶层 `discovery` 块声明 `method: sitemap` + 可选的 `sitemap_url`（默认 `<domain>/sitemap.xml`）。`runCrawl` 新增 sitemap 路由分支，分别实现 discovery-only（fetch + parse sitemap → page_pattern 过滤 → URL path auto-group → page_manifest.json + discovery_summary.json）和 extraction（线性遍历 manifest.visited → scrapling-get fetch → convertTraversalToMarkdown）。manifest 和 summary 格式对齐现有 skill Crawl Confirmation Gate 消费契约。错误全部走 handoff → Gate 停止，不做 fallback。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: strategy-discovery-block-schema

站点策略 frontmatter SHALL 支持顶层 `discovery` 块，用于声明 URL 发现方法与配置。`discovery` 块与 `api` 块互斥——静态文档站使用 `discovery`，MediaWiki 站点使用 `api.platform`。

Schema:

```yaml
discovery:
  method: "sitemap"         # 必填，当前唯一支持值
  sitemap_url: <url>        # 可选，默认 "https://<domain>/sitemap.xml"
```

当 `discovery.method` 为 `sitemap` 时，系统 SHALL 使用 sitemap.xml 作为 URL 发现源。

#### Scenario: sitemap-discovery-block-minimal

- **WHEN** 策略声明 `discovery: { method: sitemap }` 且未指定 `sitemap_url`
- **THEN** 系统使用 `https://<strategy.domain>/sitemap.xml` 作为默认 sitemap URL
- **AND** `selectFetcher` 忽略 `discovery.method`，按 protection_level / page_type 选择 scrapling 引擎（与无 `api.platform` 策略行为一致）

#### Scenario: sitemap-discovery-block-with-custom-url

- **WHEN** 策略声明 `discovery: { method: sitemap, sitemap_url: "https://example.com/custom-sitemap.xml" }`
- **THEN** 系统使用 `https://example.com/custom-sitemap.xml` 作为 sitemap URL
- **AND** 不尝试默认位置

#### Scenario: sitemap-discovery-block-replaces-api-block

- **WHEN** 策略同时包含 `discovery` 块和 `api` 块
- **THEN** 行为未定义（策略编写者 SHALL 确保互斥；实现层按 `api.platform == "mediawiki"` 优先于 `discovery.method == "sitemap"` 处理）

### Requirement: runCrawl-sitemap-routing

`runCrawl()` (`scripts/chrome-agent-cli.mjs`) SHALL 在 MediaWiki 分支之后、selector BFS 兜底之前，新增 sitemap 路由分支。

路由优先级：

```
1. api.platform == "mediawiki" → runCrawlMediawikiApi
2. discovery.method == "sitemap" && discoveryOnly → runCrawlSitemapDiscovery
3. discovery.method == "sitemap" && !discoveryOnly → runCrawlSitemapExtraction
4. discoveryOnly && no api.platform → runCrawlScraplingDiscovery (unchanged)
5. else → runCrawlScrapling (unchanged, with L1 fix)
```

#### Scenario: sitemap-route-dispatches-discovery

- **WHEN** 对含 `discovery.method: sitemap` 策略的站点执行 `chrome-agent crawl <url> --discovery-only`
- **THEN** 调用 `runCrawlSitemapDiscovery()`
- **AND** 不经过 `runCrawlScraplingDiscovery`

#### Scenario: sitemap-route-dispatches-extraction

- **WHEN** 对含 `discovery.method: sitemap` 策略的站点执行 `chrome-agent crawl <url>`
- **THEN** 调用 `runCrawlSitemapExtraction()`
- **AND** 不经过 `runCrawlScrapling`

#### Scenario: mediawiki-unchanged-by-sitemap-routing

- **WHEN** 对含 `api.platform: mediawiki` 策略的站点执行 crawl
- **THEN** 行为与变更前完全一致
- **AND** 不执行任何 sitemap 路径逻辑

### Requirement: sitemap-discovery-fetch-and-parse

`runCrawlSitemapDiscovery()` SHALL fetch `discovery.sitemap_url`（或默认位置），解析 XML 响应中的 `<urlset>` / `<sitemapindex>` 元素，提取所有 `<url><loc>` 值。

- 支持 `<urlset>` 扁平格式（一个 sitemap 文件含全部 `<url>`）
- 遇到 `<sitemapindex>` 时 SHALL 中止并生成 handoff（见 sitemap-index-handoff requirement）
- 忽略 `<url>` 下的 `<lastmod>`、`<changefreq>`、`<priority>` 子元素
- 忽略 namespace-prefixed 元素（`<news:news>`、`<image:image>` 等）

#### Scenario: flat-urlset-parsed-successfully

- **WHEN** sitemap 返回 HTTP 200 + 有效 XML `<urlset>` 含 193 `<url><loc>` 条目
- **THEN** 提取出 193 个完整 URL
- **AND** 所有 URL 以 `https://` 开头

#### Scenario: sitemap-empty-but-valid

- **WHEN** sitemap 返回 HTTP 200 + 有效 XML `<urlset>` 含 0 个 `<url>` 条目
- **THEN** 生成 handoff：`sitemap_empty`
- **AND** `result: "failure"`

### Requirement: sitemap-url-filtering-by-page-pattern

从 sitemap 提取的 URL SHALL 通过 `structure.pages[].page_pattern` 过滤。只有匹配至少一个 page pattern 的 URL 才进入 manifest。

#### Scenario: matching-urls-included-non-matching-excluded

- **WHEN** sitemap 含 195 个 URL，其中 193 个匹配 `page_pattern: "regex:^https://docs\\.gameanalytics\\.com/.+"`，2 个不匹配（`/search`、`/robots.txt` 伪路径）
- **THEN** manifest 含 193 个 URL
- **AND** events 记录被过滤的 URL 数量（不暴露具体 URL）

#### Scenario: zero-urls-match-all-patterns

- **WHEN** sitemap 返回 N 个 URL 但无一匹配任何 `page_pattern`
- **THEN** 生成 handoff：`sitemap_no_pattern_match`
- **AND** `result: "failure"`
- **AND** 不产生空 manifest

### Requirement: sitemap-url-auto-grouping

过滤后的 URL SHALL 按 URL path 的第一层级段自动分组为 categories。每个 category 对应一个 `target_directory`，用于 `page_manifest.json` 条目分组和 `discovery_summary.json` 目录树构建。

- 第一层级段 = URL path 中第一个 `/` 后的完整段（如前缀 `event-tracking-and-integrations/`）
- 根路径 URL（`/`、`/search` 等）归入 `misc`
- Category name 从 path segment 派生：`-` → 空格，每词首字母大写（`event-tracking-and-integrations` → "Event Tracking And Integrations"）
- `target_filename` 从完整 URL path 的末段派生（`/unity` → `unity.md`，空或 `/` → `index.md`）
- 每个 URL 条目的 `page_type` 从 `page_pattern` 匹配的 `structure.pages[].id` 填充

#### Scenario: urls-grouped-by-first-path-segment

- **WHEN** 193 个 URL 按 path 第一段分组
- **THEN** 产出 5 个 categories：`event-tracking-and-integrations`（~116）、`products-and-features`（~61）、`events-metrics-and-filtering`（~9）、`getting-started`（~2）、`settings-and-billing`（~3）
- **AND** 每个 URL 条目的 `target_directory` 等于其第一段 path segment
- **AND** 根路径 URL 归入 `target_directory: "misc"`

#### Scenario: title-derivation-from-url

- **WHEN** URL 为 `https://docs.gameanalytics.com/event-tracking-and-integrations/sdks-and-collection-api/game-engine-sdks/unity`
- **THEN** 该条目的 `title` 为 `"unity"`（末段 slug）
- **AND** `target_filename` 为 `"unity.md"`

### Requirement: page-manifest-json-format

Sitemap discovery SHALL 产出 `page_manifest.json`，格式为：

```json
{
  "pages": [
    {
      "url": "https://...",
      "title": "unity",
      "target_directory": "event-tracking-and-integrations",
      "target_filename": "unity.md",
      "assigned_category": "Event Tracking And Integrations",
      "page_type": "doc_page"
    }
  ]
}
```

`page_manifest.json` SHALL 写在 `runDir` 下，路径通过 `manifest_path` 字段暴露在 `discovery_summary.json` 中。

#### Scenario: manifest-written-to-rundir

- **WHEN** sitemap discovery 成功完成
- **THEN** `page_manifest.json` 写入 `runDir`，路径为绝对路径
- **AND** `discovery_summary.json` 的 `manifest_path` 字段指向该文件

### Requirement: discovery-summary-json-format

`runCrawlSitemapDiscovery()` SHALL 产出 `discovery_summary.json`，格式对齐 MediaWiki pipeline 的 `build_discovery_summary()` 输出 schema：

```json
{
  "discovery_method": "sitemap",
  "site_title": "GameAnalytics Official Documentation",
  "domain": "docs.gameanalytics.com",
  "categories": [
    {
      "name": "Event Tracking And Integrations",
      "directory": "event-tracking-and-integrations",
      "type": "category_page",
      "is_index_page": false,
      "page_count": 116,
      "sample_pages": ["unity", "godot", "unreal", "flutter", "cocos2d"],
      "page_type": "doc_page"
    }
  ],
  "excluded": [],
  "unclassified": { "count": 0, "directory": "misc", "sample_pages": [] },
  "total_pages": 193,
  "estimated_time_minutes": 17,
  "manifest_path": "/abs/path/to/page_manifest.json",
  "warnings": [],
  "caveats": ["URLs sourced from sitemap.xml; pages without page_pattern match were excluded."],
  "failure_rate": 0.0
}
```

`manifest_path` SHALL 为非 null 的绝对路径，使 skill Crawl Confirmation Gate Stage 2/3 可用。

#### Scenario: discovery-summary-consumable-by-confirmation-gate

- **WHEN** skill 读取 `discovery_summary.json`
- **THEN** `categories` 数组可被渲染为 discovery 树
- **AND** `manifest_path` 非 null，可传入 `--from-manifest` 继续 extraction
- **AND** `discovery_method: "sitemap"` 字段存在

#### Scenario: estimated-time-calculation

- **WHEN** `total_pages` 为 N
- **THEN** `estimated_time_minutes` = `max(ceil(N * 5 / 60), 1)`（每页 5 秒保守估计）

### Requirement: sitemap-extraction-linear-traversal

`runCrawlSitemapExtraction()` SHALL 从 `--from-manifest` 指定的 `page_manifest.json` 或 `manifest.json` 读取 `pages` / `visited` URL 列表，按序线性遍历：fetch → convert → 写 manifest。不走 BFS 扩散，不收集 `links_to`。

核心循环：
```
for (entry of manifest.pages) {
  page = pages.find(matches entry.url via page_pattern)
  fetcher = selectFetcher(strategy, page)
  html = runEngineFetch(repoRoot, fetcher, entry.url, htmlPath)
}
// 串行 convertTraversalToMarkdown(repoRoot, runDir, manifest, ...)
```

#### Scenario: linear-extraction-no-bfs

- **WHEN** 执行 `chrome-agent crawl <url> --from-manifest <page_manifest.json> --max-pages 200 --yes`
- **THEN** 遍历 193 个 URL
- **AND** 不对每个 fetch 结果运行 `links_to` 选择器收集新链接
- **AND** `visited` 集合大小等于 manifest 中 URL 数量（不从遍历过程扩展）

#### Scenario: extraction-respects-max-pages

- **WHEN** 执行 `--from-manifest <manifest> --max-pages 10`
- **THEN** 只遍历前 10 个 URL
- **AND** manifest 记录 `max_pages: 10`

#### Scenario: extraction-writes-manifest-and-outputs

- **WHEN** extraction 完成
- **THEN** `manifest.json` 写入 `runDir`，含 `visited` 数组 + `phase2` 转换结果
- **AND** Markdown 输出文件按 `urlToStructuredPath` 写入嵌套目录
- **AND** `result` 不为 `failure`

### Requirement: sitemap-url-default

当策略 `discovery.method: sitemap` 且未指定 `sitemap_url` 时，系统 SHALL 构造默认 URL：

```javascript
const sitemapUrl = doc?.discovery?.sitemap_url ?? `https://${doc.domain}/sitemap.xml`;
```

#### Scenario: default-sitemap-url-constructed

- **WHEN** 策略 `domain: "docs.gameanalytics.com"` + `discovery: { method: sitemap }`（无 `sitemap_url`）
- **THEN** 系统请求 `https://docs.gameanalytics.com/sitemap.xml`

#### Scenario: explicit-url-overrides-default

- **WHEN** 策略指定 `discovery.sitemap_url: "https://example.com/custom.xml"`
- **THEN** 系统请求 `https://example.com/custom.xml`
- **AND** 不请求默认位置

### Requirement: sitemap-error-handling-handoff

Sitemap 路径的所有可恢复错误 SHALL 走 handoff → Gate 停止流程，不做 fallback 到 selector BFS。

| 错误 | handoff_reason | 行为 |
|------|---------------|------|
| Sitemap HTTP 404 或网络不可达 | `sitemap_unreachable` | Gate 停止 |
| HTTP 200 但非有效 XML | `sitemap_parse_error` | Gate 停止 |
| 有效 XML 但 0 URL 匹配 page_pattern | `sitemap_no_pattern_match` | Gate 停止 |
| `<sitemapindex>` 格式 | `sitemap_index_unsupported` | Gate 停止 |

#### Scenario: sitemap-404-generates-handoff

- **WHEN** `discovery.sitemap_url` 返回 HTTP 404
- **THEN** 生成 handoff（reason: `sitemap_unreachable`）
- **AND** `result: "failure"`
- **AND** `next_action` 指示检查 sitemap URL 或使用 `discovery.sitemap_url` 显式指定路径

#### Scenario: sitemap-non-xml-generates-handoff

- **WHEN** sitemap URL 返回 HTTP 200 但内容不是有效 XML（如 HTML 登录页）
- **THEN** 生成 handoff（reason: `sitemap_parse_error`）
- **AND** `result: "failure"`

#### Scenario: sitemap-no-backstop-fallback

- **WHEN** sitemap 路径出现任何 handoff 错误
- **THEN** 系统不得回退到 selector-driven BFS
- **AND** 不得静默产生空 manifest 或空 output

### Requirement: sitemap-index-handoff

遇到 `<sitemapindex>` XML 格式时，系统 SHALL 生成 handoff 而非自动递归解析子 sitemap。

#### Scenario: sitemap-index-detected

- **WHEN** sitemap XML 根元素为 `<sitemapindex>`
- **THEN** 生成 handoff（reason: `sitemap_index_unsupported`）
- **AND** handoff summary 写明 "Sitemap index detected. Nested sitemaps are not yet supported."

### Requirement: selectFetcher-sitemap-compatibility

`selectFetcher()` SHALL 忽略 `discovery.method`。当策略不含 `api.platform` 时，fetcher 选择逻辑 SHALL 按 `protection_level` + `page_type` + `anti_crawl_refs` 决定，与现有 behavior 一致。

#### Scenario: sitemap-strategy-uses-scrapling-get-fetcher

- **WHEN** 策略 `protection_level: low` + `discovery.method: sitemap` + 无 `api.platform`
- **THEN** `selectFetcher(strategy, page)` 返回 `"get"`（scrapling-get）
- **AND** 不受 `discovery.method` 值影响

### Requirement: crawl-confirmation-gate-alignment

Sitemap discovery SHALL 产出与 MediaWiki pipeline 等价的 discovery 契约，使 skill Crawl Confirmation Gate（`~/.agents/skills/chrome-agent/SKILL.md` §Crawl Confirmation Gate）无需修改即可消费：

1. Stage 1（`--discovery-only`）→ `discovery_summary_path` 非 null
2. Stage 2（读 `discovery_summary.json`）→ `categories` 数组含 `name`/`page_count`/`sample_pages`/`directory`
3. Stage 3（`--from-manifest <manifest_path>`）→ `manifest_path` 非 null

#### Scenario: confirmation-gate-stage2-renders-categories

- **WHEN** skill 读取 sitemap 产出的 `discovery_summary.json`
- **THEN** `categories` 数组可被渲染为带 page count 和 sample pages 的树
- **AND** 与 MediaWiki 路径产出格式兼容

#### Scenario: confirmation-gate-stage3-proceeds-to-extraction

- **WHEN** skill 执行 `chrome-agent crawl <url> --from-manifest <page_manifest.json> --format json`
- **THEN** `runCrawlSitemapExtraction()` 读取 manifest 并开始 linear extraction
- **AND** `manifest_path` 在 discovery result 中为非 null

## MODIFIED Requirements

_None_

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_

## Out of Scope (Deferred)

### Deferred: sitemap-index-support

Sitemap index（`<sitemapindex>` 嵌套多子 sitemap）解析支持延后。v1 只支持扁平 `<urlset>`，遇到 index 格式生成 handoff。需独立 change（建议命名 `sitemap-index-support`）。

### Deferred: non-standard-sitemap-formats

News sitemap、image sitemap、video sitemap 等 Google 扩展格式不作特殊处理。当前实现忽略 namespace-prefixed 元素，仅提取 `<url><loc>`。

### Deferred: sitemap-discovery-method-fallback

Selector-driven BFS 作为 sitemap 失败时的 fallback 路径延后。当前实现：sitemap 失败 = handoff = Gate 停止。如需 fallback，需独立 change。

## Verification Plan

1. **单元测试**：
   - `node --test tests/sitemap-driven-crawl.test.mjs` 覆盖：sitemap XML 解析、page_pattern 过滤、auto-group 分组、discovery_summary.json 生成、linear extraction 循环
2. **Live E2E**（目标站点 = 故障来源）：
   ```bash
   chrome-agent crawl https://docs.gameanalytics.com/ --max-pages 200 --yes --format json
   ```
   断言：`result == "success"` 或 `"partial_success"`；`visited` 接近 193；`engine_path` 包含 `sitemap`；Markdown 产物存在
3. **Confirmation Gate 验证**：
   ```bash
   chrome-agent crawl https://docs.gameanalytics.com/ --discovery-only --format json
   ```
   断言：`discovery_summary_path` 非 null；`manifest_path` 非 null
4. **MediaWiki 回归**：
   对已 freeze 的 MediaWiki 站点（如 `bindingofisaacrebirth.wiki.gg`）执行 crawl，确认行为不变
5. **Error path 验证**（可选，可手动）：
   对不含 sitemap 的站点写假策略 → 断言 handoff 生成
