# Design

## Context

`scripts/chrome-agent-cli.mjs`（4200 行）是 god module，`runScrape`（L2594-2803，210 行）是其最大的 command handler。本 change 按 `crawl-scrapling-orchestrator-is-a-seam-module` 已建立的模式，将 `runScrape` 抽到 `scripts/lib/scrape.mjs` 作为同型第二实例。

输入：`specs/fetch/spec.md` 的 `scrape-orchestrator-is-a-seam-module` requirement（行为规范真源）。范本：`scripts/lib/crawl_scrapling.mjs` + `tests/crawl_scrapling.test.mjs`。

`runScrape` 与 `runCrawlScrapling` 高度同构（同为 preflight → BFS queue → phase2 markdown → result synthesis），但有关键差异：
- 无前置 dispatcher：scrape 命令直达 CLI switch（L3667），不像 crawl 有 `runCrawl` 做前置 setup
- 无 strategy/doc 绑定：scrape 是无界遍历，不依赖站点策略，ctx 字段更少
- 专属 helper：`extractAllLinks`（BFS 链接发现）、`buildScrapeReport`（scrape report builder）

## Goals / Non-Goals

**Goals:**

- `runScrape` 移至 `scripts/lib/scrape.mjs`，签名 `runScrape(ctx, opts, api)`
- cli.mjs dispatch 点（L3667）构造 `scrapeApi` grouped concern bundle 并调用
- scrape 命令产出字节级不变（纯结构重构）
- 新增 `tests/scrape.test.mjs`：纪律测试三件套 + behavior 覆盖 BFS / partial_success / parallel-fallback / preflight-failure 路径
- cli.mjs 净减 ~210 行

**Non-Goals:**

- 不抽其他 handler（Discovery / Bootstrap / Batch 等留后续 change）
- 不改变 scrape 外部行为
- 不移动 shared helper（含 scrape 专属的 `extractAllLinks`/`buildScrapeReport`，均留 cli.mjs 经 bundle 注入）
- 不引入新 bundle group 形状（沿用 crawlApi 的 grouped concern 模式）

## Decisions

### D1: setup helper 归属 —— 移入 ctx（前置到 dispatch 点）

`runScrape` 当前在函数顶部调用 `buildRunPaths` / `ensureDir` / `shouldEmitReport`。两个选项：
- (a) 移入 bundle（`api.setup` group）
- (b) 前置到 dispatch 点（L3667），结果经 ctx 传入

**决策：(b)**。理由：对齐 `runCrawlScrapling` 范式（其 setup 由 `runCrawl` 前置完成，结果经 ctx 传入）；setup 是机械的 cli 耦合逻辑，不属于 orchestrator 核心关注点（BFS / 转换 / 结果合成）；这样 bundle 只含核心编排 helper，表面积更小、更易测。

ctx 最终字段：`{ repoRoot, repoRef, resolutionMode, targetUrl, runDir, reportPath, manifestPath, emitReport }`。dispatch 点（L3667）在调用 `runScrape` 前完成 `buildRunPaths` + `ensureDir(runDir)` + `manifestPath` 计算 + `shouldEmitReport`。

### D2: bundle group 形状 —— 沿用 crawlApi，scrape 特化

```javascript
const scrapeApi = {
  fs,
  log: console,
  report: { makeResult, absoluteArtifact, writeTextFile, buildScrapeReport },
  handoff: { generateHandoff, internalFailure },
  engine: { runEngineFetch, runScraplingPreflight },
  pool: { withObscuraPool, runObscuraPreflight },
  traversal: { extractAllLinks },
  convert: { convertTraversalToMarkdown, collectMarkdownArtifacts },
};
```

与 crawlApi 的差异（scrape 特化点）：
- `report.buildScrapeReport`（替换 `buildCrawlReport`）
- `traversal.extractAllLinks`（替换 `collectLinksFromHtml` + `nextPaginationUrl`）
- 无 `cache` group（scrape 不用 scrapling cache 生命周期）
- 无 `engine.selectFetcher`（scrape 用 `fetcherOverride || "get"`，固定取值）

### D3: `extractAllLinks` / `buildScrapeReport` 不移动

两者仅被 `runScrape` 调用，理论上可移入 `scrape.mjs`。但 spec 要求模块对 cli.mjs 零 import，移动任一会引入循环依赖风险（若未来其他 handler 复用）。决策：留 cli.mjs，经 bundle 注入。这是与 crawl 范本一致的边界纪律。

### D4: 纪律测试复刻范本，scrape 特化 group 名

`tests/scrape.test.mjs` 复刻 `tests/crawl_scrapling.test.mjs` 结构：
- `readScrapeApiGroups()`：解析 cli.mjs 的 `scrapeApi` bundle，返回 `{group: [helper]}`
- 测试 1：bare-call 检测（无裸标识符调用 bundled helper）
- 测试 2：flat-call 检测（无 `api.<helper>`，必须 `api.<group>.<helper>`）
- 测试 3-7：behavior（preflight failure → internalFailure；minimal BFS success → manifest 写入；markdown:true → collectMarkdownArtifacts；parallel:true → withObscuraPool 调用；partial_success 降级）
- 测试 8：无循环 import（模块不 import cli.mjs）

### D5: spec delta 用 ADDED Requirements

`scrape-orchestrator-is-a-seam-module` 是全新 requirement（非改写既有 requirement）。按 openspec 语义用 `## ADDED Requirements`。归档时若 `openspec archive` 因 spec 结构拒绝，按 handoff 记录的已知坑修复（改 `## Requirements` + 补 `## Purpose` 等）。

## Risks / Migration

**风险 R1：byte-identical 漂移**
- setup 前置到 dispatch 点时，若遗漏字段（如 `manifestPath` 计算位置变了）可能改变产出路径
- 缓解：tasks 中设置 golden-output 校验步骤，抽取前后对同一 target 跑 scrape 对比 manifest/report

**风险 R2：bundle group 漏 helper**
- 若 `scrapeApi` 漏了 `runScrape` 实际用到的某个 helper，运行时 `api.<group>.<x>` 为 undefined → TypeError
- 缓解：纪律测试 bare-call 检测会捕获（漏注入的 helper 若被 bare 调用则报 ReferenceError；若被 `api.x` 调用但 group 里没有，behavior 测试 stub 会暴露）

**风险 R3：C10 同步遗漏**
- cli.mjs 是 tracked file，归档前必须 cp runtime + 刷 installed-hash
- 缓解：tasks 末尾固定 C10 同步步骤，归档前 doctor 复核

**迁移**：无外部 API 变化。scrape 命令调用方式、参数、产出完全不变。这是 cli.mjs 内部结构重构，对 operator 和下游脚本零影响。
