# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec `scrape-orchestrator-is-a-seam-module`（`specs/fetch/spec.md`）的实现范围：抽 `runScrape` 到 `scripts/lib/scrape.mjs`，签名 `runScrape(ctx, opts, api)`，bundle 用 named concern groups，纪律测试三件套
- [x] 1.2 确认依赖前置：`crawl_scrapling.mjs` 范本已就位、`internalFailure` builder 已就位（L2243）、`withObscuraPool` 已就位（L1041）、`extractAllLinks`/`buildScrapeReport` 为 scrape 专属纯函数（L2532/L2568）
- [x] 1.3 确认基线绿：node 86/86 + python 123/123 + doctor ok（已验证）

## 2. 核心实现任务（vertical slice）

### Slice A: orchestrator 模块抽取 + behavior 测试

- [x] 2.1 **[RED]** 写 `tests/scrape.test.mjs` 的 behavior 测试骨架（import `runScrape` from `../scripts/lib/scrape.mjs`），断言：preflight failure → internalFailure 路径；minimal BFS success → manifest 写入。此时模块不存在，测试 RED。
  - 覆盖 spec scenario: `orchestrator-extractable-and-importable`、`preflight-failure-emits-handoff-via-internalfailure`
- [x] 2.2 **[GREEN]** 创建 `scripts/lib/scrape.mjs`，实现 `runScrape(ctx, opts, api)`：
  - 从 cli.mjs L2594-2803 移植主体逻辑
  - 所有 helper 调用改为 `api.<group>.<helper>` 形式（`api.report.makeResult` / `api.engine.runScraplingPreflight` / `api.engine.runEngineFetch` / `api.traversal.extractAllLinks` / `api.convert.convertTraversalToMarkdown` / `api.convert.collectMarkdownArtifacts` / `api.pool.withObscuraPool` / `api.handoff.internalFailure` / `api.report.buildScrapeReport` / `api.report.absoluteArtifact` / `api.report.writeTextFile` / `api.fs.existsSync` / `api.fs.readdirSync`）
  - setup（buildRunPaths/ensureDir/shouldEmitReport）从函数体移除，改由 ctx 传入 runDir/reportPath/manifestPath/emitReport
  - 顶部 `import path from "node:path"`（仅依赖 node builtin，无 cli.mjs import）
  - 覆盖 spec scenario: `orchestrator-extractable-and-importable`、`scrape-output-byte-identical`、`markdown-true-branch-produces-artifacts`
- [x] 2.3 **[GREEN 补齐]** 在 `tests/scrape.test.mjs` 补齐剩余 behavior 测试：
  - `markdown:true` 路径 → `api.convert.collectMarkdownArtifacts` 被调用且 artifacts 非空（覆盖 `markdown-true-branch-produces-artifacts`）
  - `parallel:true` 路径 → `api.pool.withObscuraPool` 被调用（覆盖 `parallel-fallback-delegates-to-withobscurapool`）
  - `partial_success` 降级（traversal 有 failures 时 result 为 partial_success）
  - 无循环 import 断言（覆盖 `api-bundle-built-at-dispatch-site` 的 import 侧）

### Slice B: cli.mjs dispatch 接线

- [x] 2.4 **[RED]** 在 `tests/scrape.test.mjs` 加 dispatch 测试：解析 cli.mjs 源码，断言 `scrapeApi` bundle 存在且为 grouped concern objects（`readScrapeApiGroups()` 返回非空 groups）。此时 bundle 未构造，测试 RED。
  - 覆盖 spec scenario: `api-bundle-built-at-dispatch-site`
- [x] 2.5 **[GREEN]** 修改 `scripts/chrome-agent-cli.mjs`：
  - 在 L3667 dispatch 点（`case "scrape":`）构造 `scrapeApi` bundle（按 design D2 的 group 形状）
  - 前置 setup：`buildRunPaths` + `ensureDir(runDir)` + `manifestPath` + `shouldEmitReport`
  - 改 `runScrape(repoRoot, repoRef, ...)` 调用为 `runScrape({ repoRoot, repoRef, resolutionMode, targetUrl: parsed.target, runDir, reportPath, manifestPath, emitReport }, opts, scrapeApi)`
  - 删除 L2594-2803 的内联 `runScrape` 定义
  - 顶部 `import { runScrape } from "./lib/scrape.mjs"`
  - 覆盖 spec scenario: `api-bundle-built-at-dispatch-site`

### Slice C: 纪律测试（静态不变量）

- [x] 2.6 **[GREEN]** 在 `tests/scrape.test.mjs` 加纪律测试（复刻 `tests/crawl_scrapling.test.mjs` 的三件套，scrape 特化）：
  - `readScrapeApiGroups()`：解析 cli.mjs 的 `scrapeApi` bundle，返回 `{group: [helper]}`
  - bare-call 检测：`scrape.mjs` 中无裸标识符调用 bundled helper（覆盖 `all-bundled-helpers-called-via-api-prefix`）
  - flat-call 检测：`scrape.mjs` 中无 `api.<helper>`，必须 `api.<group>.<helper>`（覆盖 `seam-surface-uses-named-concern-groups`）

## 3. 收敛与验证准备

- [x] 3.1 byte-identical 校验：对同一 target 跑 scrape（抽取前后），对比 manifest.json + report + merged markdown 字节一致
- [x] 3.2 测试基线复核：node --test tests/*.test.mjs 全绿（预期 86→~94），python 123/123 不变
- [x] 3.3 spec coverage 自检：逐 scenario 核对 `specs/fetch/spec.md` 的 8 个 scenario 均有测试覆盖
- [x] 3.4 标记 C10 同步待办（cli.mjs 是 tracked file，归档前执行）

## 4. 验证与回写收敛

- [ ] 4.1 派 subagent 跑 `/opsx-verify`：独立核对 spec-to-implementation 一致性、纪律测试有效性、byte-identical 不变性（历史教训：4 次验证均抓到真实问题，不跳过）
- [ ] 4.2 C10 同步（归档前执行）：
  - `cp scripts/chrome-agent-cli.mjs ~/.agents/scripts/chrome-agent.mjs`（或按 `docs/playbooks/chrome-agent-global-install.md` Case 6 的正确路径）
  - 刷新 `~/.agents/scripts/.chrome-agent-installed-hash` 至当前 `git rev-parse HEAD`
  - `node scripts/chrome-agent-cli.mjs doctor` 复核 freshness
- [ ] 4.3 `openspec archive extract-scrape-orchestrator`（若遇 spec 结构拒绝，按 handoff 已知坑修复：改 `## ADDED Requirements` → 合并入库；或 `--skip-specs`）
