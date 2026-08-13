# Design

## Context

`runCrawlScrapling`（cli.mjs:2471–2913）是 god module 里最大的内联编排：~440 行 async，混合队列初始化、逐页遍历、runDir 扫描聚合、manifest 构建、handoff 生成，直接 fs 操作 ~10 处。调查发现两个修正原方案的事实：

1. **helper 复用面广**：`selectFetcher`(10 调用)、`pagePatternMatches`(11)、`buildCrawlReport`(6)、`generateHandoff`(13) 被全 cli 共享，非 scrapling 专属。随 runCrawlScrapling 提取会撕裂调用面。
2. **已有先例**：`scripts/lib/scrapling-extraction-args.mjs`（lib 提取范式，含 spec 注释）+ `tests/crawl-scrapling-pages-scope.test.mjs`（scrapling crawl 测试基础设施）已存在，降低风险。

C10 真相（playbook line 152）：`chrome-agent-cli.mjs` 是 **trigger 非 destination**——改它后同步动作是重新复制 `chrome-agent-runtime.mjs` 到 `~/.agents/scripts/chrome-agent.mjs` + 刷 installed-hash，cli 本身从不到全局。

`specs/fetch/spec.md` 是行为真源。

## Goals / Non-Goals

**Goals:**

- runCrawlScrapling 从「仅 subprocess 可测」变为「deps.fs 注入 + helper 打桩可单元测试」
- 12 位置参数 → ctx 对象，3 调用点改写
- cli.mjs 减 ~440 行 + 4 专属 helper
- 归档 commit 闭合 C10（刷新全局 runtime 副本 + installed-hash）

**Non-Goals:**

- runCrawlMediawikiApi / runCrawlScraplingDiscovery / 其它 handler 提取
- 共享 helper 自身提取
- crawl 命令任何行为变更
- spawnSync 参数化（靠打桩 scrapling helper 间接隔离，YAGNI）

## Decisions

### D1：提取边界——只搬 runCrawlScrapling，不搬任何 helper

调查发现 runCrawlScrapling 依赖 ~26 个内部符号（fs + 绝对路径/结果构建器/scrapling/obscura/conversion helper）。原计划「搬 4 专属 helper + import 7 共享」会造成 cli.mjs ↔ crawl_scrapling.mjs **双向 import**（循环依赖，靠 hoisting 脆弱工作）。改为：**只提取 runCrawlScrapling 一个函数**，全部 ~26 个依赖经 `api` 对象注入。crawl_scrapling.mjs 是单函数模块，零循环依赖，所有 helper 留在 cli.mjs。

### D2：12 位置参数 → ctx 对象

`runCrawlScrapling(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints, opts)` → `runCrawlScrapling(ctx, opts, api)`，ctx 收编前 13 项，api 收编全部 helper 依赖。3 调用点（cli.mjs:2202/2365/2369）改为构造 ctx + api。

### D3：deps seam 粒度——完整 `api` bundle 注入（非仅 fs）

runCrawlScrapling 的 ~26 个依赖中，~16 个有副作用（fs、spawn 背的 scrapling/obscura fetch、port/server、convertTraversalToMarkdown）。原计划只注入 fs 不足以使其可测。改为扁平 `api` 对象：`api.fs` + 命名 helper 函数（selectFetcher/pagePatternMatches/writeTextFile/absoluteArtifact/makeResult/generateHandoff/buildCrawlReport/collectLinksFromHtml/runEngineFetch/convertTraversalToMarkdown/findAvailablePort/startObscuraServe/concurrentFetch/stopObscuraServe/runObscuraPreflight/collectMarkdownArtifacts/urlToStructuredPath/nextPaginationUrl/scraplingCacheDir/ensureDir/isScraplingCached/saveScraplingCache/scraplingSlugFromUrl/loadScraplingCache/runScraplingPreflight/log/buildScraplingExtractionArgs）。cli.mjs 构建一次 `crawlApi`，传递。

### D4：无循环依赖

crawl_scrapling.mjs 仅 `export async function runCrawlScrapling(ctx, opts, api)`，不从 cli.mjs import 任何东西。cli.mjs `import { runCrawlScrapling } from "./lib/crawl_scrapling.mjs"`。单方向依赖，零循环。`buildScraplingExtractionArgs` 已在 cli.mjs 从 `./lib/scrapling-extraction-args.mjs` import，复用。

### D5：测试 TDD——RED 证明可测性缺失，GREEN 证明 seam 建立

新 `tests/crawl_scrapling.test.mjs`（node:test）：构建 stub `api`——纯 helper 用真实实现（absoluteArtifact/makeResult/pagePatternMatches/scraplingSlugFromUrl 等从 cli.mjs re-export 或直接复制轻量纯逻辑），副作用 helper（fs/runEngineFetch/runScraplingPreflight/findAvailablePort/convertTraversalToMarkdown 等）打桩。断言 traversal 顺序、manifest 构建、handoff 生成、preflight 失败路径。提取前这些断言无法写（函数内联）→ 提取后可写 = RED→GREEN。

### D6：C10 同步在归档 commit 内

```bash
cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs
git rev-parse HEAD > ~/.agents/scripts/.chrome-agent-installed-hash
```
顺带闭合既有 installed-hash 漂移（`8111a3f` → 当前 HEAD）。验证：`chrome-agent doctor` 报 `repo_freshness: ok`。

## Risks / Migration

- **签名错配**：12 参数对象化 + 3 调用点改写，错配会运行时崩。缓解：dispatch 处回归（crawl 命令 dry-run）+ crawl-scrapling-pages-scope.test.mjs 集成回归。
- **共享 helper export 遗漏**：补 export 后若有内部调用点未同步会 import 失败。缓解：grep 逐个验证。
- **async/顶层 await**：runCrawlScrapling 内 `await findAvailablePort()` 等保持 async；新模块导出 async function。
- **行为保真**：crawl 产出字节级不变是硬约束。缓解：对比提取前后同一 target 的 manifest/report（若环境允许实跑；否则靠逻辑等价审查 + 测试覆盖）。
