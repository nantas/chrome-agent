# Specification Delta

## Capability 对齐（已确认）

- Capability: `sitemap-driven-crawl`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 在现有 sitemap discovery pipeline 基础上追加两个增量能力：(1) sitemap index 解析与迭代合并——`parseSitemapXml()` 检测 `<sitemapindex>` 时提取子 sitemap URL 列表，`runCrawlSitemapDiscovery()` 逐个 fetch + parse + Set 去重 + 合并；(2) `discovery.exclude_patterns` 字段——在 page_pattern include 过滤后应用 exclude 规则，解决 PostHog references 等场景。子 sitemap 部分失败时继续处理（warnings + caveats），不 handoff。grill-me Q1-Q6 全部对齐。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 父 spec: `openspec/changes/sitemap-driven-crawl/specs/sitemap-driven-crawl/spec.md`（上游契约，除本文件声明的 MODIFIED 项外，其余行为保持不变）

## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_

## Out of Scope (Deferred)

### Deferred: non-standard-sitemap-formats

News sitemap、image sitemap、video sitemap 等 Google 扩展格式不作特殊处理。当前实现忽略 namespace-prefixed 元素，仅提取 `<url><loc>`。

### Deferred: recursive-sitemap-index

Sitemap index 的递归嵌套（index → index → urlset）不支持。仅支持一层 index → urlset 解析。

### Deferred: parallel-sub-sitemap-fetch

v1 串行 fetch 子 sitemap。并发 fetch 延后。
