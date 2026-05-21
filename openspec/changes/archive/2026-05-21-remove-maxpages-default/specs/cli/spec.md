# Specification Delta

## Capability 对齐（已确认）

- Capability: `cli`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: modified
- 用户确认摘要: 用户确认方案 A——移除所有 JS 层 `maxPages` 硬编码默认值，null = 不限制

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: maxPages-null-means-unlimited
`runCrawl()`、`runCrawlMediawikiApi()`、`runCrawlScrapling()`、`runScrape()` 中 `maxPages` 解构默认值 SHALL 为 `null`，表示不限制页面数。`main()` 调用这些函数时 SHALL 直接透传 `parsed.maxPages`，不填充默认值。

#### Scenario: external-caller-no-maxPages
- **WHEN** 外部代码调用 `runCrawl()` 且 `opts` 不含 `maxPages` 字段
- **THEN** 解构得到 `maxPages = null`，函数 SHALL 不限制抓取页面数

#### Scenario: external-caller-with-maxPages
- **WHEN** 外部代码调用 `runCrawl()` 且 `opts.maxPages = 50`
- **THEN** 函数 SHALL 限制抓取最多 50 页

#### Scenario: cli-no-max-pages-flag
- **WHEN** CLI 用户执行 `crawl` 或 `scrape` 且不传 `--max-pages`
- **THEN** `parsed.maxPages` 为 `null`，透传后不限制抓取页面数

#### Scenario: cli-with-max-pages-flag
- **WHEN** CLI 用户执行 `crawl --max-pages 50`
- **THEN** `parsed.maxPages` 为 `50`，函数 SHALL 限制抓取最多 50 页

### Requirement: maxPages-null-guard-in-conditions
所有使用 `maxPages` 进行比较的条件判断 SHALL 正确处理 `null` 语义：
- `spawnSync` 传参条件 SHALL 使用 `if (maxPages != null)` 而非 `if (maxPages)`
- while 循环条件 SHALL 使用 `(maxPages == null || visited.size < maxPages)` 替代 `visited.size < maxPages`
- 分页入队条件 SHALL 同样使用 null-safe 写法

#### Scenario: mediawiki-pipeline-null-maxPages
- **WHEN** `runCrawlMediawikiApi()` 中 `maxPages` 为 `null`
- **THEN** SHALL 不传 `--max-pages` 参数给 Python pipeline

#### Scenario: mediawiki-pipeline-with-maxPages
- **WHEN** `runCrawlMediawikiApi()` 中 `maxPages` 为 `50`
- **THEN** SHALL 传 `--max-pages 50` 给 Python pipeline

#### Scenario: scrapling-while-loop-null
- **WHEN** `runCrawlScrapling()` 中 `maxPages` 为 `null` 且队列非空
- **THEN** while 循环 SHALL 继续执行，不受 `visited.size` 上限约束

#### Scenario: scrapling-pagination-null
- **WHEN** `maxPages` 为 `null` 且存在分页链接
- **THEN** 分页入队条件 SHALL 不阻止入队

#### Scenario: scrape-while-loop-null
- **WHEN** `runScrape()` 中 `maxPages` 为 `null` 且队列非空
- **THEN** while 循环 SHALL 继续执行，不受 `visited.size` 上限约束
