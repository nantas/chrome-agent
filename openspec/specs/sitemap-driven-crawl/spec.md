# sitemap-driven-crawl Specification

## Purpose
TBD - created by archiving change sitemap-driven-crawl. Update Purpose after archive.
## Requirements
### Requirement: strategy-discovery-block-schema

站点策略 frontmatter SHALL 支持顶层 `discovery` 块，用于声明 URL 发现方法与配置。`discovery` 块与 `api` 块互斥——静态文档站使用 `discovery`，MediaWiki 站点使用 `api.platform`。

Schema:

```yaml
discovery:
  method: "sitemap"             # 必填，当前唯一支持值
  sitemap_url: <url>            # 可选，默认 "https://<domain>/sitemap.xml"
  exclude_patterns:             # 可选，URL 排除规则（在 page_pattern include 后应用）
    - "exact:/docs/references/**"
    - "regex:^/docs/v\\d+/.*"
```

`exclude_patterns` 与 `structure.pages[].page_pattern` 使用相同的 `exact:` / `regex:` 前缀语法。

当 `discovery.method` 为 `sitemap` 时，系统 SHALL 使用 sitemap.xml 作为 URL 发现源。sitemap index 格式已支持，无需在策略中额外声明。

#### Scenario: sitemap-discovery-block-minimal

- **WHEN** 策略声明 `discovery: { method: sitemap }` 且未指定 `sitemap_url`
- **THEN** 系统使用 `https://<strategy.domain>/sitemap.xml` 作为默认 sitemap URL
- **AND** `selectFetcher` 忽略 `discovery.method`，按 protection_level / page_type 选择 scrapling 引擎（与无 `api.platform` 策略行为一致）

#### Scenario: sitemap-discovery-block-with-custom-url

- **WHEN** 策略声明 `discovery: { method: sitemap, sitemap_url: "https://example.com/custom-sitemap.xml" }`
- **THEN** 系统使用 `https://example.com/custom-sitemap.xml` 作为 sitemap URL
- **AND** 不尝试默认位置

#### Scenario: sitemap-discovery-block-with-exclude-patterns

- **WHEN** 策略声明 `discovery: { method: sitemap, exclude_patterns: ["exact:/docs/references/**"] }`
- **THEN** 系统在 page_pattern include 过滤后应用 exclude_patterns
- **AND** 匹配 `/docs/references/**` 的 URL 被排除

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

`runCrawlSitemapDiscovery()` SHALL fetch `discovery.sitemap_url`（或默认位置），解析 XML 响应中的 `<urlset>` 或 `<sitemapindex>` 元素。

- 支持 `<urlset>` 扁平格式（一个 sitemap 文件含全部 `<url>`）——提取所有 `<url><loc>` 值
- 支持 `<sitemapindex>` 格式——提取所有子 sitemap `<loc>` URL，逐个 fetch + parse + 去重合并
- 忽略 `<url>` 下的 `<lastmod>`、`<changefreq>`、`<priority>` 子元素
- 忽略 namespace-prefixed 元素（`<news:news>`、`<image:image>` 等）

#### Scenario: flat-urlset-parsed-successfully

- **WHEN** sitemap 返回 HTTP 200 + 有效 XML `<urlset>` 含 193 `<url><loc>` 条目
- **THEN** 提取出 193 个完整 URL
- **AND** 所有 URL 以 `http://` 或 `https://` 开头

#### Scenario: sitemap-index-parsed-and-resolved

- **WHEN** sitemap 返回 HTTP 200 + `<sitemapindex>` 含 `<sitemap><loc>https://example.com/sitemap-0.xml</loc></sitemap>` 含 100 个 URL
- **THEN** 系统 fetch sitemap-0.xml，提取 100 个 URL
- **AND** 100 个 URL 继续走 include/exclude 过滤 → auto-group 流程

#### Scenario: sitemap-empty-but-valid

- **WHEN** sitemap 返回 HTTP 200 + 有效 XML `<urlset>` 含 0 个 `<url>` 条目
- **THEN** 生成 handoff：`sitemap_empty`
- **AND** `result: "failure"`

### Requirement: sitemap-url-filtering-by-page-pattern

从 sitemap 提取的 URL SHALL 经过两阶段过滤：

1. **Include**：通过 `structure.pages[].page_pattern` 过滤。只有匹配至少一个 page pattern 的 URL 才进入下一阶段。
2. **Exclude**（新增）：通过 `discovery.exclude_patterns` 过滤（如已配置）。匹配任意 exclude pattern 的 URL 被移除。

两阶段后剩余的 URL 进入 auto-group 分组。

#### Scenario: matching-urls-included-non-matching-excluded

- **WHEN** sitemap 含 195 个 URL，其中 193 个匹配 `page_pattern: "regex:^https://docs\\.gameanalytics\\.com/.+"`，2 个不匹配（`/search`、`/robots.txt` 伪路径）
- **THEN** include 阶段后剩 193 个 URL
- **AND** events 记录被过滤的 URL 数量

#### Scenario: exclude-pattern-removes-after-include

- **WHEN** page_pattern 保留 200 个 URL，`exclude_patterns: ["exact:/docs/references/**"]` 匹配其中 50 个 URL
- **THEN** 最终 150 个 URL 进入 auto-group
- **AND** events 分别记录 include 过滤数和 exclude 过滤数

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

遇到 `<sitemapindex>` XML 格式时，系统 SHALL 解析并迭代子 sitemap（见 `sitemap-index-resolve-and-merge`），不再生成 handoff。

#### Scenario: sitemap-index-resolved-not-handoff

- **WHEN** sitemap XML 根元素为 `<sitemapindex>`
- **THEN** 系统提取子 sitemap URL，迭代 fetch + parse + 合并
- **AND** 不生成 `sitemap_index_unsupported` handoff
- **AND** 如所有子 sitemap 成功且 URL 集合非空，继续 discovery 流程

#### Scenario: sitemap-index-all-failed-handoff

- **WHEN** sitemap index 的所有子 sitemap 均 fetch/parse 失败
- **THEN** 生成 handoff（reason: `sitemap_all_subs_failed`）

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

### Requirement: sitemap-index-resolve-and-merge

当 `parseSitemapXml()` 检测到 `<sitemapindex>` 根元素时，系统 SHALL 提取所有 `<sitemap><loc>` URL，返回 `{ isIndex: true, sitemaps: ["https://...", ...] }`。`runCrawlSitemapDiscovery()` SHALL 迭代每个子 sitemap URL：curl fetch → `parseSitemapXml()` parse → 收集 URL → `Set` 去重 → 合并为统一 URL 列表。

- 子 sitemap 提取仅用 `<loc>` 元素，忽略 `<lastmod>` 等字段
- 合并时使用 `Set` 按 URL 去重（首次出现保留）
- 合并后 URL 列表继续走 page_pattern include → exclude_patterns → auto-group 流程
- 不支持递归嵌套（index → index → urlset）

#### Scenario: sitemap-index-extracts-subsitemap-urls

- **WHEN** `parseSitemapXml()` 输入为 `<sitemapindex><sitemap><loc>https://example.com/sitemap-0.xml</loc></sitemap></sitemapindex>`
- **THEN** 返回 `{ isIndex: true, sitemaps: ["https://example.com/sitemap-0.xml"] }`

#### Scenario: multi-sitemap-index-merged

- **WHEN** sitemap index 列出 3 个子 sitemap（sitemap-0.xml = 100 页, sitemap-1.xml = 50 页, sitemap-2.xml = 30 页）
- **THEN** 最终合并 URL 列表含 180 个唯一 URL
- **AND** URL 全集走 page_pattern 和 exclude_patterns 过滤

#### Scenario: cross-sitemap-deduplication

- **WHEN** sitemap-0.xml 和 sitemap-1.xml 均包含 `https://example.com/docs/index`
- **THEN** 合并后该 URL 仅出现一次
- **AND** 去重不影响其他 URL

### Requirement: sitemap-index-partial-failure-resilience

子 sitemap fetch 或 parse 失败时，系统 SHALL 继续处理其余子 sitemap，在 warnings 和 caveats 中记录失败的子 sitemap URL 及原因，不触发 handoff。

- 单个子 sitemap HTTP 404 / 超时 / parse error → warning + caveat → 继续
- 所有子 sitemap 均失败 → handoff（reason: `sitemap_all_subs_failed`）

#### Scenario: one-sub-sitemap-fails-others-succeed

- **WHEN** sitemap-0.xml (100 pages, OK) + sitemap-1.xml (404)
- **THEN** 合并 URL 列表含 100 个 URL
- **AND** `warnings` 包含 `"Sub-sitemap sitemap-1.xml failed: HTTP 404"`
- **AND** `caveats` 包含 `"1/2 sub-sitemaps failed"`
- **AND** `result` 为 `"success"` 或 `"partial_success"`
- **AND** `failure_rate` 反映失败占比

#### Scenario: all-sub-sitemaps-fail

- **WHEN** 全部子 sitemap 均 fetch/parse 失败
- **THEN** 生成 handoff（reason: `sitemap_all_subs_failed`）
- **AND** `result: "failure"`

### Requirement: sitemap-exclude-patterns-filtering

`discovery` 块 SHALL 支持可选 `exclude_patterns` 字段：一个 page_pattern 字符串数组。在 page_pattern include 过滤之后、auto-group 之前，系统 SHALL 应用 exclude_patterns 规则，移除匹配任意 exclude pattern 的 URL。

- `exclude_patterns` 与 `page_pattern` 使用相同的 `exact:` / `regex:` 前缀语法
- 执行顺序：include（page_pattern）→ exclude（exclude_patterns）→ auto-group
- `exclude_patterns` 为空数组或未定义时，行为不变（不过滤）
- 排除后 URL 数量为 0 → handoff（reason: `sitemap_no_pattern_match`）

#### Scenario: exclude-references-category

- **WHEN** 策略含 `exclude_patterns: ["exact:/docs/references/**"]`
- **AND** 原始 URL 集合含 `/docs/references/posthog-js`、`/docs/cdp/overview`
- **THEN** `/docs/references/posthog-js` 被排除
- **AND** `/docs/cdp/overview` 保留
- **AND** events 记录排除的 URL 数量

#### Scenario: multiple-exclude-patterns

- **WHEN** 策略含 `exclude_patterns: ["exact:/docs/references/**", "regex:^/docs/v\\d+/.*"]`
- **THEN** 匹配任意一个 pattern 的 URL 均被排除
- **AND** 不匹配任何 exclude pattern 的 URL 保留

#### Scenario: exclude-patterns-empty-no-op

- **WHEN** 策略未定义 `exclude_patterns` 或值为 `[]`
- **THEN** 不排除任何 URL
- **AND** 行为与变更前完全一致

#### Scenario: all-urls-excluded

- **WHEN** `exclude_patterns` 匹配所有 URL
- **THEN** 最终 URL 数量为 0
- **AND** 生成 handoff（reason: `sitemap_no_pattern_match`）

