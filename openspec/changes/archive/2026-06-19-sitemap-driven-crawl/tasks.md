# Tasks

## 1. Spec A: crawl-scrapling-pages-scope (L1 bugfix)

### T1 — 修复 `runCrawlScrapling` 的 `pages` 绑定

- [x] **T1.1 (RED)** — 新增 `tests/crawl-scrapling-pages-scope.test.mjs`：构造最小 `strategy` + `doc`（含 `structure.pages` 3 条）+ `opts`，调用 `runCrawlScrapling`，断言不抛 `ReferenceError`，断言 `pages` 从 `doc.structure.pages` 解析
  - 文件：`tests/crawl-scrapling-pages-scope.test.mjs`（`node:test`，遵循 AGENTS.md §0.5 C5）
  - 证据：`node --test tests/crawl-scrapling-pages-scope.test.mjs` 失败（RED）
- [x] **T1.2 (GREEN)** — 在 `runCrawlScrapling` 函数体顶部（line 2315 附近，`opts` 解构之前）添加 `const pages = doc?.structure?.pages ?? []`
  - 文件：`scripts/chrome-agent-cli.mjs`
  - 对应 spec: `specs/crawl-scrapling-pages-scope/spec.md` § Requirement: runCrawlScrapling-pages-binding
  - 证据：`node --test tests/crawl-scrapling-pages-scope.test.mjs` 全绿

### T2 — 作用域一致性审查

- [x] **T2** — `grep -nE "pages\.(find|filter|map|length|forEach)\b" scripts/chrome-agent-cli.mjs`，逐处确认每个 `pages.*` 引用所在函数体内均有 `pages` 绑定
  - 文件：`scripts/chrome-agent-cli.mjs`
  - 证据：无跨函数标识符穿透；姊妹函数 `runCrawlScraplingDiscovery` 不受影响

### T3 — 删除废弃 change 目录

- [x] **T3** — 删除 `openspec/changes/crawl-scrapling-pages-scope/`
  - 理由：内容已完全吸收进本 change
  - 证据：`openspec/changes/crawl-scrapling-pages-scope/` 目录不再存在

## 2. Spec B: sitemap-driven-crawl (new capability)

### T4 — 策略文件更新（S-line）

- [x] **T4.1** — 更新 `sites/strategies/docs.gameanalytics.com/strategy.md` frontmatter：
  - 删除 `api:` 块（`platform` / `base_url` / `capabilities` / `homepage`）
  - 新增 `discovery: { method: sitemap }` 块（无需显式 `sitemap_url`，使用默认值）
  - `structure` / `extraction` / Markdown body 保持不变
- [x] **T4.2** — 更新 `sites/strategies/registry.json`：将 `docs.gameanalytics.com` 条目的 `api` 相关字段更新为 `discovery` 相关
  - 对应 spec: `specs/sitemap-driven-crawl/spec.md` § Requirement: strategy-discovery-block-schema

### T5 — `parseSitemapXml()` 工具函数（RED + GREEN）

- [x] **T5.1 (RED)** — `tests/sitemap-driven-crawl.test.mjs` 新增 parseSitemapXml 测试：
  - 扁平 `<urlset>` 含 5 `<url><loc>` → 返回 5 URL
  - 空 `<urlset>` → 返回 `[]`
  - `<sitemapindex>` → 返回 `{ isIndex: true }` 标记
  - 无效 XML → 返回 `{ error: "parse_error" }`
- [x] **T5.2 (GREEN)** — 在 `scripts/chrome-agent-cli.mjs` 新增 `parseSitemapXml(xmlString)`：
  - 使用 Node.js 内置或轻量 XML 解析（regex-based 或 `String.prototype.matchAll`）
  - 提取 `<urlset>` 下所有 `<url><loc>` 文本内容，trim + filter 非空
  - 检测 `<sitemapindex>` 根元素并返回 index 标记
  - 解析失败返回 error 对象
  - 对应 spec: `specs/sitemap-driven-crawl/spec.md` § Requirement: sitemap-discovery-fetch-and-parse

### T6 — `buildSitemapDiscoverySummary()` + auto-group 逻辑（RED + GREEN）

- [x] **T6.1 (RED)** — `tests/sitemap-driven-crawl.test.mjs` 新增 buildSitemapDiscoverySummary 测试：
  - 输入 10 个 URL（5 种 path 前缀）→ categories 含 5 个组，page count 正确
  - 根路径 URL → 归入 `misc`
  - `sample_pages` 不超过 5
  - `estimated_time_minutes` 计算正确
  - `manifest_path` 非 null
- [x] **T6.2 (GREEN)** — 在 `scripts/chrome-agent-cli.mjs` 新增 `buildSitemapDiscoverySummary(domain, description, pages, outputDir)`：
  - grouped by `target_directory`（URL path 第一段，auto-derived）
  - category name 从 segment slug 派生
  - `target_filename` 从 URL 末段派生
  - `page_type` 通过 `pagePatternMatches` 匹配 `structure.pages`
  - 输出格式完全对齐 `specs/sitemap-driven-crawl/spec.md` § Requirement: discovery-summary-json-format
  - 对应 spec: § Requirement: sitemap-url-auto-grouping + § Requirement: discovery-summary-json-format

### T7 — `runCrawlSitemapDiscovery()` 函数（RED + GREEN）

- [x] **T7.1 (RED)** — `tests/sitemap-driven-crawl.test.mjs` 新增 discovery 流程测试：
  - mock sitemap fetch 返回 fixture XML → 断言 `page_manifest.json` + `discovery_summary.json` 写入 runDir
  - mock sitemap 404 → 断言 `result: "failure"`，handoff 生成
  - mock 非 XML 响应 → 断言 handoff
  - mock 空 sitemap → 断言 handoff
- [x] **T7.2 (GREEN)** — 在 `scripts/chrome-agent-cli.mjs` 新增 `runCrawlSitemapDiscovery(repoRoot, repoRef, resolutionMode, runDir, reportPath, emitReport, targetUrl, strategy, doc, opts)`：
  - `sitemapUrl = doc?.discovery?.sitemap_url ?? "https://${doc.domain}/sitemap.xml"`
  - `sitemapResult = runEngineFetch(repoRoot, "get", sitemapUrl, tempPath)`
  - HTTP non-200 / fetch fail → handoff（`sitemap_unreachable`）
  - `parseSitemapXml(content)` → parse error → handoff（`sitemap_parse_error`）
  - `<sitemapindex>` → handoff（`sitemap_index_unsupported`）
  - page_pattern 过滤 → 0 match → handoff（`sitemap_no_pattern_match`）
  - auto-group → `page_manifest.json` + `discovery_summary.json`
  - 返回 `makeResult("crawl", ...)` with `discovery_summary_path` + `manifest_path`
  - 对应 spec: § sitemap-discovery-fetch-and-parse + § sitemap-url-filtering + § sitemap-error-handling-handoff

### T8 — `runCrawlSitemapExtraction()` 函数（RED + GREEN）

- [x] **T8.1 (RED)** — `tests/sitemap-driven-crawl.test.mjs` 新增 extraction 流程测试：
  - mock `--from-manifest` 含 3 个 URL → 断言 3 次 fetch + convert
  - 断言 `visited` 大小 = 3（无 BFS 扩散）
  - 断言 `manifest.json` 写入 runDir，含 `phase2` 统计
- [x] **T8.2 (GREEN)** — 在 `scripts/chrome-agent-cli.mjs` 新增 `runCrawlSitemapExtraction(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, fromManifest, opts)`：
  - 读取 `fromManifest`（`page_manifest.json` 或 `manifest.json`）
  - 解析 `pages` / `visited` 列表
  - 线性遍历（带 `maxPages` 限制）：
    - `page = pages.find(matches url via pagePatternMatches)`
    - `fetcher = selectFetcher(strategy, page)`
    - `runEngineFetch(repoRoot, fetcher, url, htmlPath)`
  - 串行 `convertTraversalToMarkdown(repoRoot, runDir, manifest, ...)`
  - 写 `manifest.json`（含 `visited` + `phase2`）
  - **不走 BFS 扩散，不收集 `links_to`**
  - **函数体内 SHALL 有自己的 `const pages = doc?.structure?.pages ?? []` 绑定**（与 L1 修复一致）
  - 对应 spec: § sitemap-extraction-linear-traversal

### T9 — `runCrawl` 路由 + `selectFetcher` 适配

- [x] **T9** — 在 `runCrawl()`（line 1977）中新增 sitemap 路由分支：
  - 文件：`scripts/chrome-agent-cli.mjs`
  - 插入位置：MediaWiki 分支（line 2039）之后、selector BFS 分支（line 2043）之前
  - 代码：
    ```javascript
    const discoveryMethod = doc?.discovery?.method;
    if (discoveryMethod === "sitemap") {
      if (discoveryOnly) {
        return runCrawlSitemapDiscovery(repoRoot, repoRef, resolutionMode, runDir, reportPath, emitReport, targetUrl, strategy, doc, opts);
      }
      const sitemapManifestPath = opts.fromManifest || path.join(runDir, "page_manifest.json");
      return runCrawlSitemapExtraction(repoRoot, repoRef, resolutionMode, runDir, reportPath, sitemapManifestPath, emitReport, targetUrl, strategy, doc, opts.fromManifest, opts);
    }
    ```
  - `selectFetcher` 无需修改（`discovery.method` 不在其判断逻辑中）
  - 对应 spec: § runCrawl-sitemap-routing + § selectFetcher-sitemap-compatibility

### T10 — 单元测试汇总

- [x] **T10** — `node --test tests/crawl-scrapling-pages-scope.test.mjs` 全绿
- [x] **T10** — `node --test tests/sitemap-driven-crawl.test.mjs` 全绿
- [x] **T10** — C9 义务：修改 `scripts/chrome-agent-cli.mjs` → `python3 scripts/test_runner.py unit` 全部通过，无回归

### T11 — Live E2E：GameAnalytics full crawl

- [x] **T11.1** — Discovery-only:
  ```bash
  chrome-agent crawl https://docs.gameanalytics.com/ --discovery-only --format json
  ```
  断言：`result == "success"`；`discovery_summary_path` 非 null；`manifest_path` 非 null
- [x] **T11.2** — Full crawl (--max-pages 200):
  ```bash
  chrome-agent crawl https://docs.gameanalytics.com/ --max-pages 200 --yes --format json
  ```
  断言：`result == "success"` 或 `"partial_success"`；`engine_path` 含 `sitemap`；`visited` ≈ 193；Markdown 产出文件存在
  对应 spec: § Requirement: crawl-confirmation-gate-alignment + verification plan item 3

### T12 — MediaWiki 回归

- [x] **T12** — 对已 freeze 的 MediaWiki 站点执行 crawl：
  ```bash
  chrome-agent crawl <bindingofisaacrebirth.wiki.gg or similar> --max-pages 3 --yes --format json
  ```
  断言：仍走 MediaWiki API pipeline（`engine_path` 含 `mediawiki`）；`result` 不为 failure
  对应 spec: § Scenario: mediawiki-unchanged-by-sitemap-routing

## 3. 收敛与验证准备

- [x] **T13** — 更新 `verification.md`（基于实现结果，覆盖 spec-to-implementation 与 task-to-evidence）
- [x] **T14** — 更新 `writeback.md`，执行回写：
  - 架构文档：`02-pipeline-flow.md` / `03-strategy-schema.md` / `04-cli-reference.md` / `06-engine-selection.md`
  - 已有 `sites/strategies/docs.gameanalytics.com/strategy.md` + `registry.json`（T4 已完成）
- [x] **T15** — 提交 PR，关联本 spec

## 4. 任务依赖图

```
T1 (pages fix)
  └─ T2 (scope audit)
       ├─ T3 (删除旧 change)
       └─ T5 (parseSitemapXml) ── T7 (discovery) ── T9 (routing)
               │                      │
               └─ T6 (summary) ───────┘
                                        │
T4 (S-line 策略)                        ├─ T10 (unit tests)
                                        │
T8 (extraction) ────────────────────────┘
                                        │
                              T11 (live E2E) + T12 (regression)
                                        │
                              T13 (verification) → T14 (writeback) → T15 (PR)
```
