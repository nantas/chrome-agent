# Proposal

## 问题定义

`extract-crawl-scrapling-orchestrator` change（commit `04a35fb`）把 `runCrawlScrapling` 从 cli.mjs 抽到 `scripts/lib/crawl_scrapling.mjs`，并设计了一个注入式 `api` bundle 来避免循环依赖、实现可单测。但抽取过程中在 markdown artifact 收集分支留下一个**裸标识符调用**：

```javascript
// scripts/lib/crawl_scrapling.mjs:328
if (markdown) {                                   // markdown 默认 true
  finalArtifacts.push(...collectMarkdownArtifacts(runDir));   // ← 裸调用
  //                            ^^^^^^^^^^^^^^^^^^^^^^^^^
  //  该函数只存在于 cli.mjs 局部作用域 + api bundle，本模块未 import、非全局
}
```

该模块顶部只 `import path from "node:path"`，`collectMarkdownArtifacts` 未被 import、不是全局、也不在模块局部——所以在 `markdown === true`（**默认值**）路径上每次执行都抛 `ReferenceError: collectMarkdownArtifacts is not defined`。

**为什么现有测试没抓到**：`tests/crawl_scrapling.test.mjs` 的两个用例（`:95`、`:108`）都传 `{ markdown: false }`，恰好绕过崩溃分支。缺陷被测试盲区掩盖。

**根因**（架构层）：seam 模块的契约 `crawl-scrapling-orchestrator-is-a-seam-module` 规定了"helpers 通过 `api` bundle 注入"，但**从未规定调用点的 `api.` 前缀纪律**。闭包内的 `collectMarkdownArtifacts(...)` 在 cli.mjs 里永远能解析；在独立 ESM 模块里的裸 `collectMarkdownArtifacts(...)` 永远不能。seam 的间接层发明了一类新故障模式（bare-vs-`api.` 拼写），而契约没有约束它。

## 范围边界

**In scope**：
- 修复 `scripts/lib/crawl_scrapling.mjs:328` 的裸调用 → `api.collectMarkdownArtifacts(runDir)`
- 对 `crawl_scrapling.mjs` 全文做一次 bare-vs-`api.` 防御性扫描，确认无其它同类缺陷
- 新增 `markdown:true` 回归测试，覆盖崩溃分支
- 在 `fetch` 能力的 `crawl-scrapling-orchestrator-is-a-seam-module` 契约里补上调用点 `api.` 前缀纪律不变量（治本：防止该类拼写再次漏入）

**Out of scope**（留作后续 change）：
- 缩小 `api` bundle 表面（32 key → ~4 真协作方）——见再审查报告 New #2，是更大的 seam 重构，单独立项
- CV3 markdown post-ops 折入 kernel ——见再审查报告 New #1，属 convert 能力，单独立项
- cli.mjs 其余 6 个大 handler 的抽取（runExplore / runBootstrapStrategy / runBatch / runCrawlSitemapDiscovery / runCrawlSitemapExtraction / runCrawlMediawikiApi）

**不变性**：`markdown:false` 路径行为字节级不变；`crawlApi` bundle 定义与 `collectMarkdownArtifacts` helper 实现零改动（缺陷纯粹是调用点缺前缀）。

## Capabilities

### New Capabilities

_(无)_

### Modified Capabilities

- `fetch`: 给既有 `crawl-scrapling-orchestrator-is-a-seam-module` 契约补上调用点纪律不变量——seam 模块内所有经 `api` bundle 注入的 helper SHALL 通过 `api.` 前缀引用，禁止裸标识符调用；并要求 `markdown:true`（默认）分支有回归覆盖

## Capabilities 待确认项

- [x] 能力清单已与用户确认（仅 Modified `fetch`；用户指令"先修复 C4 的问题"，C4 = crawl seam 抽取引入的活跃缺陷，归属 fetch 能力）

## Impact

- **代码**：`scripts/lib/crawl_scrapling.mjs`（1 行调用点修复 + 注释订正）；`tests/crawl_scrapling.test.mjs` 或同级新测试文件（+1 用例 `markdown:true`）
- **规范**：`openspec/specs/` 下 `fetch` 能力的 `crawl-scrapling-orchestrator-is-a-seam-module` 需求新增调用点纪律 scenario（delta 形式）
- **运行时行为**：crawl 命令默认路径（`markdown:true`）从"抛 ReferenceError"恢复为"产出 markdown artifacts"——这是缺陷修复，不是行为变更（设计本意就是产出）
- **C10 全局同步**：**不触发**。本 change 不触碰 tracked files（`chrome-agent-runtime.mjs` / `chrome-agent-cli.mjs` / `skills/chrome-agent/SKILL.md`）
- **风险**：极低。调用点补前缀是单字符级修复；`collectMarkdownArtifacts` 已在 bundle 内、helper 实现已就绪

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`docs/GOVERNANCE.md` §3、ADR 0013 §4.4、`openspec/specs/crawl-scrapling-pages-scope/spec.md`
  - 项目页：架构再审查报告 Critical callout（`architecture-review-20260813-154550.html`）、`scripts/lib/crawl_scrapling.mjs:328`、`tests/crawl_scrapling.test.mjs:95,108`
  - 回写目标：`openspec/specs/` 下 `fetch` 能力 spec delta（C10 不触发）
