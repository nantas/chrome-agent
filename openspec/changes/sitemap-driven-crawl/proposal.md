# Proposal

## 问题定义

`chrome-agent crawl` 命令对非 MediaWiki 的静态文档站点（Docusaurus / Hugo / Jekyll / MkDocs / VitePress）存在两类阻断性缺陷，导致整个静态站点生态的 crawl 能力不可用：

**L1 — 直接崩溃（P-line bug）**：`runCrawlScrapling()` 函数体内多处引用 `pages` 标识符，但该变量仅在外层 `runCrawl()` 作用域定义。JS 函数作用域规则下无法穿透，抛出 `ReferenceError: pages is not defined`，在第一个待抓取页面处理时即崩溃。影响范围：所有非 MediaWiki 站点的 crawl 命令。

**L2 — 根本性能力缺失（S-line + P-line）**：即使修复 L1，非 MediaWiki 静态文档站仍无可用 crawl 路径。问题表现：

- **sitemap 被完全忽略**：策略声明 `api.platform: sitemap` + `base_url: sitemap.xml`，但 `runCrawl` 只识别 `api.platform: mediawiki`，其余全部走 selector-driven BFS。sitemap 提供的 193 个确定性 URL 被丢弃
- **discovery 能力断层**：`runCrawlScraplingDiscovery()` 硬编码 `discovery_method: "first_level_links"`，产出 `manifest_path: null`。skill 层的 Crawl Confirmation Gate（Stage 2 读 discovery_summary、Stage 3 调 `--from-manifest`）在 scrapling 路径上是断的
- **BFS 覆盖不足**：selector-driven BFS 从首页导航出发，默认 `maxPages=3`，无法覆盖多层级文档树（如 4 层深的 SDK 文档路径）

**实证故障案例**：对 `docs.gameanalytics.com`（Docusaurus v3.10.1，193 页，sitemap.xml 完整暴露）执行 `crawl` 命令崩溃。用户最终用 30 行 Python 脚本（requests + bs4 + html2text）绕过 chrome-agent。

## 范围边界

**In scope：**
1. 修复 `runCrawlScrapling` 的 `pages` 变量作用域 bug（L1）
2. 新增 `discovery.method: sitemap` 策略配置块，解耦 discovery 声明与 `api` 块
3. 新增 sitemap discovery 管线：fetch sitemap.xml → parse → page_pattern 过滤 → URL path auto-group → 产出 `page_manifest.json` + `discovery_summary.json`
4. 新增 `runCrawlSitemapDiscovery` + `runCrawlSitemapExtraction` 函数，对齐 MediaWiki path 的 discovery → confirmation → extraction 三阶段契约
5. `runCrawl` 路由逻辑新增 `discovery.method: sitemap` 分支
6. `discovery_summary.json` 格式对齐现有 skill Confirmation Gate（mirrors `build_discovery_summary()` 输出 schema）
7. GameAnalytics 策略 frontmatter 改写：删除 `api:` 块，新增 `discovery:` 块
8. `sitemap_url` 默认值推导（`<domain>/sitemap.xml`），可选显式覆盖
9. 错误处理：sitemap 404 / 非 XML / 0 匹配 → handoff → Gate 停止，不做 fallback
10. 单元测试（node:test）+ live E2E 验证（GameAnalytics full crawl）+ MediaWiki 回归

**Out of scope (Deferred)：**
- Sitemap index 嵌套（`<sitemapindex>` → 多个子 sitemap）：v1 只支持扁平 `<urlset>`
- `runCrawlScrapling` 的 JS 运行时异常 handoff 发射
- `discovery.method: recursive_bfs` / `discovery.method: first_level_links` 的其他 discovery 方法
- 非 Docusaurus SSG 的特殊 sitemap 格式兼容（news-sitemap / image-sitemap / video-sitemap）

## Capabilities

### New Capabilities

- `sitemap-driven-crawl`: Sitemap-driven static documentation site crawl pipeline — discovery (fetch + parse sitemap.xml → page_pattern filter → URL path auto-group → page_manifest.json + discovery_summary.json) → extraction (linear traversal → scrapling-get fetch → convertTraversalToMarkdown), with manifest contract alignment to enable Crawl Confirmation Gate in scrapling path.

### Modified Capabilities

- `crawl-scrapling-pages-scope`: Fix `ReferenceError: pages is not defined` in `runCrawlScrapling()` — add local `const pages = doc?.structure?.pages ?? []` binding in function body. Affects all non-MediaWiki selector-driven BFS crawl paths. Root cause: `pages` defined in `runCrawl` closure (line 2018), referenced but not bound in `runCrawlScrapling` (lines 2374, 2429, 2574, 2597).

## Capabilities 待确认项

- [x] 能力清单已与用户确认（grill-me 8 轮决策对齐）
- [x] `discovery` 块顶层设计确认（vs 挂在 `structure` 下）
- [x] `sitemap_url` 默认值策略确认
- [x] 错误处理 fallback 策略确认（handoff-only, no silent degradation）
- [x] GameAnalytics 策略改写确认
- [x] L1 fix 方案确认（方案 A：函数体顶部 local binding）

## Impact

| 维度 | 影响 |
|------|------|
| **P-line** | `scripts/chrome-agent-cli.mjs`：修复 `runCrawlScrapling`（1 行）+ 新增 `runCrawlSitemapDiscovery`（~80 行）+ `runCrawlSitemapExtraction`（~80 行）+ `buildSitemapDiscoverySummary`（~60 行）+ `parseSitemapXml`（~30 行）+ `runCrawl` 路由分支（~5 行）+ `discovery_summary.json` 写入逻辑 |
| **S-line** | `sites/strategies/docs.gameanalytics.com/strategy.md`：删除 `api:` 块，新增 `discovery:` 块<br>`sites/strategies/registry.json`：更新 `docs.gameanalytics.com` 条目 |
| **Docs** | `docs/architecture/03-strategy-schema.md`：新增 `discovery` 块 schema<br>`docs/architecture/02-pipeline-flow.md`：新增 sitemap→scrapling 路径<br>`docs/architecture/04-cli-reference.md`：CLI 路由图更新<br>`docs/architecture/06-engine-selection.md`：决策树更新 |
| **Skill** | `~/.agents/skills/chrome-agent/SKILL.md`：无需修改（confirmation gate 消费 discovery_summary.json 格式不变） |
| **Tests** | `tests/sitemap-driven-crawl.test.mjs`（新）+ `tests/crawl-scrapling-pages-scope.test.mjs`（新） |
| **废弃** | `openspec/changes/crawl-scrapling-pages-scope/`：内容已吸收，删除目录 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 binding.md §标准与项目页面绑定 + §回写目标
