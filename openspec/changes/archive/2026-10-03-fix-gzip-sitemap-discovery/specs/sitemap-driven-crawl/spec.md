# Specification Delta

## Capability 对齐（已确认）

- Capability: `sitemap-driven-crawl`
- 来源: `proposal.md` / 用户已确认方案
- 变更类型: modified
- 用户确认摘要: “确认，请按照方案创建 change”；范围为通用 gzip 支持、回归测试及失败报告证据链接修正。

## 规范真源声明

本文件是该 capability 在本 change 中的行为规范真源；design、tasks、verification 必须引用本文件，项目页面回写不能替代 delta spec。

## MODIFIED Requirements

### Requirement: sitemap-discovery-fetch-and-parse

`runCrawlSitemapDiscovery()` SHALL fetch `discovery.sitemap_url`（或默认位置），以原始字节读取响应、按 gzip magic bytes 检测并解压，再以 UTF-8 解码，解析 XML 响应中的 `<urlset>` 或 `<sitemapindex>` 元素。

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

系统 SHALL 对顶层及所有子 sitemap 使用相同解码规则，依据内容而非 URL 后缀决定解压；普通 XML 原样解析，原始下载文件保留为诊断证据。

#### Scenario: gzip-top-level-urlset
- **WHEN** 顶层 sitemap 响应为合法 gzip 压缩的 urlset
- **THEN** 解压后提取与明文 XML 相同的 URL

#### Scenario: gzip-index-and-mixed-children
- **WHEN** 顶层是 gzip sitemapindex，子文件同时包含 gzip 和普通 XML，且有重复 URL
- **THEN** 所有文件经过相同字节解码规则，合并去重后继续既有 include/exclude 过滤

#### Scenario: encoding-determined-by-bytes
- **WHEN** 无 .gz 后缀的 URL 返回 gzip，或 .gz URL 返回已经解压的 XML
- **THEN** 前者解压、后者直接解析，不漏解压或重复解压


### Requirement: sitemap-index-partial-failure-resilience

子 sitemap fetch、解压或 parse 失败时，系统 SHALL 继续处理其余子 sitemap，在 warnings 和 caveats 中记录失败的子 sitemap URL 及原因，不触发 handoff。

- 单个子 sitemap HTTP 404 / 超时 / decompress_error / parse error → warning + caveat → 继续
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

#### Scenario: corrupt-gzip-partial-failure
- **WHEN** 一个子 sitemap gzip 损坏，另一个子 sitemap 正常且有匹配 URL
- **THEN** 保留正常 URL，warnings/caveats 记录损坏文件 URL 与 decompress_error，failure_rate 反映失败比例
- **AND** 不因单个解压异常中断循环或触发全失败 handoff

#### Scenario: all-children-corrupt-gzip
- **WHEN** 所有子 sitemap 均因 gzip 损坏无法解压
- **THEN** 返回 sitemap_all_subs_failed handoff，每个子项记录 decompress_error


## ADDED Requirements

### Requirement: sitemap-decompression-failure-diagnostics
系统 SHALL 区分 gzip 解压失败和 XML 解析失败；顶层解压失败 SHALL 返回 `sitemap_decompress_error` handoff，子文件解压失败 SHALL 使用 `decompress_error` 原因进入既有部分/全部失败处理。失败不得静默当作空 sitemap 或 fallback 到 BFS。

#### Scenario: corrupt-top-level-gzip
- **WHEN** 顶层下载成功但 gzip 被截断或校验失败
- **THEN** 返回 failure 与 sitemap_decompress_error handoff，保留原始文件，不泄漏未捕获异常

#### Scenario: decoded-content-is-not-xml
- **WHEN** gzip 解压成功但内容为 HTML 或其他非 sitemap 文本
- **THEN** 沿用顶层 sitemap_parse_error 或子项 parse_error，不误报为解压失败

### Requirement: sitemap-handoff-existing-evidence
Sitemap discovery 失败时，handoff SHALL 链接本次实际存在的原始顶层及已下载子 sitemap 文件；文件未创建时不得伪造证据链接。manifest.json SHALL 仅在实际存在时列出。原始证据不得被解压文本覆盖。

#### Scenario: all-sub-sitemaps-failed-with-raw-files
- **WHEN** 子文件全部失败，运行目录含顶层及两个原始子文件但没有 manifest.json
- **THEN** handoff 链接上述三个存在的文件，不声称 manifest.json 已生成

#### Scenario: network-failure-before-file-created
- **WHEN** 获取失败且没有创建响应文件
- **THEN** handoff 仍报告获取失败，但不链接不存在的响应文件

#### Scenario: existing-manifest-and-logs-retained
- **WHEN** 失败目录包含已存在的 manifest.json 或日志/JSON 诊断文件
- **THEN** handoff 保留这些有效诊断入口，每个路径仅列出一次
