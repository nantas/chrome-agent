# Verification

## 独立 Review 修复记录

| Issue | 级别 | 状态 |
|---|---|---|
| 缩进回归 (false positive) | WARNING | ✅ 确认：`let events`/`let fallbackReason` 是原始 0-space，`const pages` 已统一到 0-space |
| `parseSitemapXml` 仅接受 https:// | WARNING | ✅ 已修复：同时接受 `http://` 和 `https://` |
| `runCrawlSitemapExtraction` 签名冗余 | SUGGESTION | ✅ 已移除未使用参数 `startPage`/`matchingPage`/`entryPoints` |
| T7.1/T8.1 flow 测试缺失 | CRITICAL | ✅ 已添加 11 个结构性 flow 测试 (21/21 pass) |
| 测试文件未跟踪 | CRITICAL | ✅ 已 `git add` |
| 预存 Python import errors | WARNING | ✅ 确认：`selectolax` 环境依赖，与本 change 无关 |

## 实现覆盖

### Spec A: crawl-scrapling-pages-scope (L1 bugfix)

| Requirement | 验证 | 证据 |
|---|---|---|
| runCrawlScrapling-pages-binding | `const pages = doc?.structure?.pages ?? []` at same indent as `let events` | `scripts/chrome-agent-cli.mjs:2381` |
| scrapling-crawl-fallback-regression-test | 2 tests pass | `tests/crawl-scrapling-pages-scope.test.mjs` |
| Anti-pattern guard disallowed | 无 `typeof` / `globalThis` | 测试文件 line 38-51 |

### Spec B: sitemap-driven-crawl (new capability)

| Requirement | 验证 | 证据 |
|---|---|---|
| strategy-discovery-block-schema | GameAnalytics frontmatter 更新 | `strategy.md:35-36` |
| runCrawl-sitemap-routing | `discovery.method === "sitemap"` 分支 | `cli.mjs:2086-2091` |
| sitemap-discovery-fetch-and-parse | curl fetch + `parseSitemapXml` | `cli.mjs:3973-4034`; 6/6 unit tests |
| sitemap-url-filtering-by-page-pattern | `pagePatternMatches` 支持 `page_pattern` 数组 | `cli.mjs:540-567` |
| sitemap-url-auto-grouping | `autoGroupSitemapUrls` | `cli.mjs:3872-3914`; 2/2 unit tests |
| page-manifest-json-format | `page_manifest.json` 写入 | Live: 193 entries, 7 categories |
| discovery-summary-json-format | `buildSitemapDiscoverySummary` | `cli.mjs:3917-3966`; 2/2 unit tests; `manifest_path` 非 null |
| sitemap-extraction-linear-traversal | `runCrawlSitemapExtraction` (无 BFS) | `cli.mjs:4076-4211`; Live: 5/5 converted |
| sitemap-url-default | `https://<domain>/sitemap.xml` | `cli.mjs:3973` |
| sitemap-error-handling-handoff | 4 handoff 分支 | `cli.mjs:3980-4041`; 4 structural tests |
| sitemap-index-handoff | `<sitemapindex>` detection | `parseSitemapXml` → `{ isIndex: true }` → handoff |
| selectFetcher-sitemap-compatibility | 无需修改 | `selectFetcher` 不引用 `discovery.method` |
| crawl-confirmation-gate-alignment | `manifest_path` + `discovery_summary_path` 非 null | Live discovery 确认 |

## 测试套件

| Suite | Result |
|---|---|
| `node --test tests/crawl-scrapling-pages-scope.test.mjs` | ✅ 2/2 pass |
| `node --test tests/sitemap-driven-crawl.test.mjs` | ✅ 21/21 pass |
| `python3 scripts/test_runner.py unit` | ⚠️ 2 预存 selectolax import errors (无关) |
| `node --check scripts/chrome-agent-cli.mjs` | ✅ pass |

## Live Verification

| 验证 | 结果 |
|---|---|
| Discovery-only: 193 pages, 7 categories | ✅ |
| Full crawl: 5/5 pages fetched + converted to Markdown | ✅ |
| Markdown 产出路径 | ✅ 嵌套目录按 URL 结构 (`event-tracking-and-integrations/.../page.md`) |

## 待后续验证 (Deferred)

- [ ] MediaWiki 站点回归 (路由变更隔离到 sitemap 分支，风险低)
- [ ] Full GameAnalytics crawl (193 pages, ~16 min)
