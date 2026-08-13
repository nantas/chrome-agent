# Design

## Context

`extract-crawl-scrapling-orchestrator` change（commit `04a35fb`）把 `runCrawlScrapling` 抽成独立 ESM 模块 `scripts/lib/crawl_scrapling.mjs`，用注入式 `api` bundle 承接 ~28 个 cli.mjs helper。该模块顶部只 `import path from "node:path"`，所有 helper 经 `api.` 前缀访问——除了一处：line 328 的 `...collectMarkdownArtifacts(runDir)` 漏了 `api.` 前缀。这是闭包迁移到独立模块时典型的"标识符穿透失效"：原 cli.mjs 闭包内裸调用永远解析，独立模块内裸调用永不解析。`markdown` 默认 `true`，所以默认 crawl 路径每次都抛 `ReferenceError`；两个现有测试都跑 `markdown:false`，恰好绕过崩溃分支。

规范真源：`specs/fetch/spec.md` 的 MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`——补了两条新不变量（调用点 `api.` 前缀纪律 + `markdown:true` 分支回归覆盖）。

## Goals / Non-Goals

**Goals:**
- 消除默认 crawl 路径的 `ReferenceError`：line 328 裸调用 → `api.collectMarkdownArtifacts(runDir)`
- 防止同类拼写再次漏入：在 spec 契约里钉死调用点纪律，并加一个静态检查测试（grep 模块源码，发现任何 bundled helper 的裸调用即失败）
- 关闭测试盲区：新增 `markdown:true` 回归用例，断言产出 markdown artifacts 而非捕获异常

**Non-Goals:**
- 缩小 `api` bundle 表面（32 key → ~4 真协作方）——再审查报告 New #2，更大 seam 重构，另立 change
- CV3 markdown post-ops 折入 kernel——再审查报告 New #1，属 convert 能力，另立 change
- 抽取 cli.mjs 其余 6 个大 handler——原 C4 候选的剩余部分，另立 change
- 改动 `crawlApi` bundle 定义或 `collectMarkdownArtifacts` helper 实现——缺陷纯粹是调用点缺前缀

## Decisions

**D1 — 修复范围 = 单行 + 注释订正。** 防御性扫描（对全部 28 个 bundled key × 全模块 ~40 个调用点做静态分类）证实：**唯一**的裸调用是 line 328 的 `collectMarkdownArtifacts`，其余 27 个 key 全部正确使用 `api.` 前缀。无 sibling 缺陷。修复即 line 328 补 `api.` 前缀；顺带订正 line 329 注释里"found by api.collectMarkdownArtifacts"的措辞一致性（注释已正确，无需改；仅确认）。`crawlApi` bundle 定义不动、`collectMarkdownArtifacts` helper 实现不动。

**D2 — 回归测试 = 两个新用例。** 现有 `tests/crawl_scrapling.test.mjs` 两个用例都 `markdown:false`。新增：
- `markdown:true` 用例：注入完整 stub `api`（含 `collectMarkdownArtifacts` 返回固定 artifact 数组），驱动 `runCrawlScrapling` 到达 final-artifact 装配块，断言 (a) 不抛、(b) `finalArtifacts` 包含 stub 返回的 markdown artifacts。复用现有测试的 stub 构造模式。
- 静态纪律检查用例：读 `scripts/lib/crawl_scrapling.mjs` 源码 + 从 `cli.mjs` 的 `crawlApi` 定义抽取 bundled key 清单，对每个 key 扫描模块内是否存在非 `api.`/非声明/非 import 的裸调用，发现即失败。这是"契约可执行化"——把 spec 的 `all-bundled-helpers-called-via-api-prefix` scenario 变成跑得了的断言。

**D3 — 不引入 lint 依赖。** D2 的静态检查用纯 `node:test` + `fs.readFileSync` + 正则实现（与 D1 扫描脚本同一逻辑），不引入 eslint-plugin-import 之类。ponytail：stdlib 够用就不加依赖。已知 ceiling：正则无法理解 `const { foo } = api` 解构（本模块未用此模式；若将来引入，静态检查需同步更新）。

**D4 — spec delta 用 MODIFIED 而非 ADDED。** 既有 `crawl-scrapling-orchestrator-is-a-seam-module` requirement 已在 fetch 能力下冻结（来自 extract change）。本次在其完整 requirement block 上追加"Call-site discipline"段 + 两个新 scenario（`all-bundled-helpers-called-via-api-prefix`、`markdown-true-branch-produces-artifacts-not-reference-error`），保留原 3 个 scenario 不变。这给契约一个单一定义点，而非两条平行 requirement。

## Risks / Migration

**风险**：
- *极低。* D1 是单字符级修复；`collectMarkdownArtifacts` 已在 bundle 内、helper 就绪、签名不变。修复后默认路径从"抛错"恢复为"产出"，这正是设计本意——不是行为变更。
- D2 的 `markdown:true` 用例需要构造能驱动到 line 328 的 stub `api`（traversal + convert 链路）。现有 `markdown:false` 用例的 stub 可作起点，但需补 `convertTraversalToMarkdown`、`collectMarkdownArtifacts` 两个 stub 返回值。若 stub 构造成本超预期，退路是用 `markdown:false` 路径 + 直接单测 `collectMarkdownArtifacts` 的 bundle 注入（但那样就绕过了崩溃分支，不满足 spec——不可取）。

**迁移**：无。外部调用方（cli.mjs 的 3 个 dispatch 点、crawl 命令用户）零感知；`markdown:false` 行为字节级不变。

**C10 全局同步**：不触发。本 change 仅改 `scripts/lib/crawl_scrapling.mjs` + 测试，不触碰 tracked files（runtime.mjs / cli.mjs / SKILL.md）。`collectMarkdownArtifacts` 已在 `crawlApi` bundle 注入，无需改 cli.mjs。

**验证锚点**：`node --test tests/crawl_scrapling.test.mjs`（含新用例）；`openspec status` apply-ready；可选 `chrome-agent doctor` 烟测默认 crawl 路径不再抛 ReferenceError。
