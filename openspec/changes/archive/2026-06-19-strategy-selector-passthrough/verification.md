# Verification

## 验证结论

**PASS** — `strategy-selector-passthrough` 的 4 个 ADDED Requirements 全部实现并被测试覆盖；所有代码改动遵循 TDD（RED→GREEN）；KI-1（PostHog fetch 抓取失效）经端到端实测确认修复（`chrome-agent fetch` 原生消费策略选择器，397B → 6106B）。无 CRITICAL/WARNING 级测试缺口。

测试结果：
- Node.js：`node --test tests/fetch-strategy-selector.test.mjs` → **12/12 pass**（新增）
- Node.js 全量回归：`tests/{fetch-strategy-selector,chrome-agent-runtime,crawl-scrapling-pages-scope,sitemap-driven-crawl}.test.mjs` → **62/62 pass**
- Python 单元：`python3 scripts/test_runner.py unit` → **74/74 pass**
- 端到端冒烟：`chrome-agent fetch https://posthog.com/docs/feature-flags` → success，content.md = **6106B / 122 行**（修复前 397B 导航栏）

## 独立验证（reviewer subagent / `/opsx-verify`）

本 change 经独立 reviewer subagent 验证，结论与上述主 agent 自验一致（Ready for archive），但独立验证捕获了主 agent 自验遗漏的 2 个 WARNING：

1. **WARNING 1（采纳并修复）**：cloakbrowser_fetcher.py 不接受 `--ai-targeted`，旧代码对该 fetcher 硬编码 `--ai-targeted` 致使所有 `protection_level:high` 策略（boardgamegeek.com / wiki.supercombo.gg）fetch 失败。主 agent 初版的 helper cloakbrowser 分支"保留 legacy passthrough"延续了该 pre-existing bug。**已修复**：helper cloakbrowser 分支改为返回 `[]`（`scripts/lib/scrapling-extraction-args.mjs`），同时更新 design.md D6 与 helper 注释。修复后 cloakbrowser 路径不再收到 unrecognized arg，高防护站点现可正确 fetch。
2. **WARNING 2（维持现状，已记录）**：PostHog site-samples 因 cache 格式不匹配 skipped——属设计限制，与下方缺口 1 一致。E2E fetch 冒烟（6106B）作为等价证据。

另采纳 SUGGESTION 1（修正 design.md D1 签名 drift，从 `(strategy, matchingPage)` 改为实际 `(strategy, fetcher)` 并补充 refactor 理由）与 SUGGESTION 2（git add 新文件）。

## Spec-to-Implementation Coverage

规范真源：`specs/fetch-strategy-selector/spec.md`

| Requirement | 实现位置 | 测试证据 | 状态 |
| --- | --- | --- | --- |
| `strategy-content-selector-passthrough` | `buildScraplingExtractionArgs()` 分支 3（`scripts/lib/scrapling-extraction-args.mjs`）；`runFetch()`（cli:1916）、`convertTraversalToMarkdown()` 两处 file://+per-page（cli:1358/1375）、`runCrawlScrapling --phase convert`（cli:2679） | `test: helper: strategy with non-empty content selector ... returns -s args`；`test: runFetch builds fetch args via ...`；`test: crawl convert loop ... consumes the helper`；E2E fetch 冒烟 6106B | ✅ |
| `ai-targeted-fallback-when-no-selector` | helper 分支 4（fallback）；触发条件：选择器缺失/空/纯空白 或 strategy=null | `test: strategy WITHOUT content selector falls back`；`test: null strategy falls back` | ✅ |
| `shared-arg-builder-helper` | `scripts/lib/scrapling-extraction-args.mjs`（单一 export，fetch+crawl 共用）；mediawiki-api 分支返回 `[strategy.path]`；cloakbrowser 分支返回 `["--ai-targeted"]`（D6） | `test: mediawiki-api fetcher returns [strategy.path]`；`test: cloakbrowser fetcher returns legacy --ai-targeted`；`test: runFetch imports the shared helper module` | ✅ |
| `selector-injection-safety` | selector 作为 `["-s", selector]` 数组元素，经 `runScraplingFetch` 的 `spawnSync(cli, args[])` argv 数组传递，不经 shell 拼接（helper 顶部注释固化此约束） | `test: selector with special characters is a single discrete argv element`（断言 `div[class*='@container/reader-content']` 为单一未拆分元素） | ✅ |

### Scenario 覆盖（spec 的 9 个场景）

| Spec Scenario | 验证方式 | 结果 |
| --- | --- | --- |
| `fetch-with-strategy-content-selector` | E2E：`chrome-agent fetch posthog docs/feature-flags`（posthog 策略声明 `div[class*='@container/reader-content']`） | ✅ 6106B 含 h1+正文 |
| `crawl-with-strategy-content-selector` | 源码断言：`convertTraversalToMarkdown` 两处 + `runCrawlScrapling --phase convert` 均调用 helper（无字面量 `["--ai-targeted"]`） | ✅ |
| `selector-source-is-strategy-not-hardcoded` | helper 单测 + cli 无硬编码选择器（grep 确认 fetch/crawl 路径无字面量选择器） | ✅ |
| `fetch-strategy-without-content-selector` | helper 单测：strategy 无 content → `["--ai-targeted"]`，无 `-s` | ✅ |
| `fetch-no-strategy-match` | helper 单测：strategy=null → `["--ai-targeted"]` | ✅ |
| `helper-encapsulates-selector-decision` | 源码断言：runFetch + convert loop 均调用同一 helper，返回值完全决定 scrapling 参数 | ✅ |
| `helper-preserves-mediawiki-api-path` | helper 单测：mediawiki-api → `[strategy.path]`，不受 content 选择器影响 | ✅ |
| `selector-with-special-characters` | helper 单测：`div[class*='@container/reader-content']` 作为单一 argv 元素；E2E fetch 实测 scrapling 正确解析 | ✅ |

## Task-to-Evidence Coverage

| Task | Evidence |
| --- | --- |
| 1.1 spec 范围确认 | 4 Requirements × 任务/测试映射表（见上）；本文件 Spec-to-Implementation 表 |
| 1.2 crawl per-URL 审计 | 结论：`convertTraversalToMarkdown` 无 strategy 参数 → 注入 `strategy` 到 opts；scrape 调用点(3014/3034)不传 strategy → 自动 ai-targeted 回退。实现在 cli:1335 opts + cli:2722/2746/4370 三处 crawl 调用点传 `strategy` |
| 1.3 前置约定 | node v24 + `node:test`；测试落 `tests/fetch-strategy-selector.test.mjs`（已创建） |
| 2.1 RED helper 单测 | `tests/fetch-strategy-selector.test.mjs`（先写，RED 确认 ERR_MODULE_NOT_FOUND） |
| 2.2 GREEN helper | `scripts/lib/scrapling-extraction-args.mjs`（创建）；7 个 helper 单测 pass |
| 2.3 RED runFetch 断言 | 同测试文件源码断言（RED 确认 helper 未接入） |
| 2.4 GREEN runFetch | cli:11 import + cli:1916 `buildScraplingExtractionArgs(strategy, fetcher)` |
| 2.5 crawl per-URL 解析 | cli:1335 `strategy = null` opt；循环内 per-URL `buildScraplingExtractionArgs(strategy, fetcher)` |
| 2.6 RED crawl 断言 | `test: crawl convert loop` + `test: runCrawlScrapling ... cache fastpath`（RED 确认） |
| 2.7 GREEN crawl | cli:1358（file://）、cli:1375（per-page）、cli:2679（--phase convert）+ 3 调用点传 strategy |
| 2.8 cloakbrowser -s 验证 | `cloakbrowser_fetcher.py` 既不接受 `-s` 也不接受 `--ai-targeted`（grep 确认）；helper cloakbrowser 分支返回 `["--ai-targeted"]`（D6 决策）；单测覆盖 |
| 3.1 PostHog site 回归 | `python3 scripts/test_runner.py site-samples --domain posthog.com` → 5 skipped（无 .cache 条目）；改由 E2E fetch 冒烟证明（见缺口说明） |
| 3.2 全量测试 | Node 62/62 + Python 74/74 + E2E fetch 冒烟 全绿 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| helper 实现 | `scripts/lib/scrapling-extraction-args.mjs` | shared-arg-builder-helper, 全 4 Requirement |
| helper 单测 | `tests/fetch-strategy-selector.test.mjs`（L1–L99，12 tests） | 全 4 Requirement |
| runFetch 接入 | `scripts/chrome-agent-cli.mjs:11, 1916` | passthrough (fetch) |
| crawl 接入 | `scripts/chrome-agent-cli.mjs:1358, 1375, 2679` + 调用点 2722/2746/4370 | passthrough (crawl) |
| 测试通过截图 | Node 62/62, Python 74/74（本 session 执行） | task 3.2 |
| E2E 冒烟 | `outputs/20260619T122822-fetch-posthog-com-docs-feature-flags/content.md`（6106B） | passthrough, KI-1 修复 |
| PostHog 策略（已修选择器） | `sites/strategies/posthog.com/strategy.md`（KI-1） | 触发场景 |

## 缺口与阻塞项

**无阻塞项。** 以下为已知边界（非缺陷）：

1. **PostHog site-samples 跳过**（task 3.1）：`python3 scripts/test_runner.py site-samples --domain posthog.com` 报 5 skipped——PostHog 为 scrapling 站点，`.cache/` 为 scrapling 格式（`<slug>.html`+`<slug>.meta.json`），而 Python site-samples runner 读取 `.cache/chrome-cdp/<domain>/*.json`（chrome-cdp/pipeline 格式）。两者缓存格式不匹配 → site-samples 对 PostHog 本就不适用（设计如此）。改由 **E2E fetch 冒烟**（6106B，原生消费策略选择器）作为等价回归证据，且更贴近本 change 修改的 JS scrapling 调用路径。
2. **scrape / batch / explore 路径未修复**（design 显式 Out of Scope）：`chrome-agent-cli.mjs:3461`（runBatch）仍硬编码 `["--ai-targeted"]`；explore 路径（L2678 已修为 crawl --phase convert；其余 explore 专用转换点若有同类模式留作后续 change）。本 change 的共享 helper 已就位，后续 change 可低成本启用。
3. **J3 测试完备检查**：新增模块 `scripts/lib/scrapling-extraction-args.mjs` 有对应测试 `tests/fetch-strategy-selector.test.mjs`（✅ 无 CRITICAL）；修改的 `scripts/chrome-agent-cli.mjs` 由同测试文件的源码结构断言覆盖（✅ 无 WARNING）。
