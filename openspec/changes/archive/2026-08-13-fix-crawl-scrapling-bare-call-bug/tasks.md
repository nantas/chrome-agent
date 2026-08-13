# Tasks

> 规范真源：`specs/fetch/spec.md` · MODIFIED `crawl-scrapling-orchestrator-is-a-seam-module`（新增 Call-site discipline 段 + 2 个 scenario：`all-bundled-helpers-called-via-api-prefix`、`markdown-true-branch-produces-artifacts-not-reference-error`）。
> 代码改动极小（单行修复 + 2 个测试用例），但仍按 vertical slice 拆分以满足 TDD 约束。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 spec 覆盖范围：`fetch` 能力的 `crawl-scrapling-orchestrator-is-a-seam-module` requirement 已写完 MODIFIED block（含 5 个 scenario）
- [x] 1.2 确认依赖前置：`collectMarkdownArtifacts` 已在 `crawlApi` bundle（`cli.mjs:2136`）注入，helper 实现（`cli.mjs:1324`）就绪，无需新增 bundle 成员
- [x] 1.3 防御性扫描已完成：对全部 28 个 bundled key × ~40 个调用点做静态分类，确认**唯一**裸调用是 `crawl_scrapling.mjs:328` 的 `collectMarkdownArtifacts`，无 sibling 缺陷（证据见 design.md D1）

## 2. 核心实现任务

### Slice A — 钉死契约：静态纪律检查测试（RED → GREEN）

覆盖 spec scenario `all-bundled-helpers-called-via-api-prefix`。

- [x] 2.1.A RED：在 `tests/crawl_scrapling.test.mjs`（或同级新文件 `tests/crawl-scrapling-api-discipline.test.mjs`）新增 `node:test` 用例：从 `scripts/chrome-agent-cli.mjs` 的 `crawlApi` 对象定义处程序化抽取 bundled key 清单 → 读 `scripts/lib/crawl_scrapling.mjs` 源码 → 对每个 key 断言"模块内不存在非 `api.` 前缀、非声明（function/const/let/var/import）、非注释行的裸调用"。当前运行：该测试**会失败**（捕获 line 328 的 `collectMarkdownArtifacts` 裸调用）。
  - 完成标准：`node --test` 跑该用例，失败信息明确指向 line 328 的裸调用。
- [x] 2.2.A GREEN：修复 `scripts/lib/crawl_scrapling.mjs:328`，`...collectMarkdownArtifacts(runDir)` → `...api.collectMarkdownArtifacts(runDir)`。重跑 2.1.A：**通过**。
  - 完成标准：静态纪律检查用例通过；diff 仅 line 328 一行（+ 注释若需订正）。

### Slice B — 关闭盲区：`markdown:true` 分支回归测试（RED → GREEN）

覆盖 spec scenario `markdown-true-branch-produces-artifacts-not-reference-error`。

- [x] 2.1.B RED：在 `tests/crawl_scrapling.test.mjs` 新增 `markdown: true` 用例。构造完整 stub `api`（在现有 `markdown:false` 用例的 stub 基础上补 `convertTraversalToMarkdown` → `{ ok:true, mergedPath:..., failed:[] }`、`collectMarkdownArtifacts` → `[固定 artifact 对象]`、`runEngineFetch`/`isScraplingCached` 等驱动到 final-artifact 块所需的成员）。断言：(a) `runCrawlScrapling` 不抛、(b) `result.artifacts` 含 stub `collectMarkdownArtifacts` 返回的 artifact。当前运行（Slice A 修复前）：**抛 ReferenceError**；（Slice A 修复后、本断言加入前）：应通过。
  - 完成标准：`node --test` 跑该用例，通过；断言 artifacts 非空且含 stub 返回项。
- [x] 2.2.B GREEN：Slice A 的 line 328 修复已使本用例转绿；本子任务确认无需额外实现改动。若 stub 构造中发现 traversal 链路需补 stub 成员，在此补齐 stub（不改产线代码）。
  - 完成标准：`node --test tests/crawl_scrapling.test.mjs` 全量绿（原有 2 用例 + 新增 2 用例）。

## 3. 收敛与验证准备

- [x] 3.1 跑全量 crawl 相关测试：`node --test tests/crawl_scrapling.test.mjs tests/crawl-scrapling-pages-scope.test.mjs tests/fetch-strategy-selector.test.mjs`，确认无回归
- [x] 3.2 烟测（可选但推荐）：对一个小目标跑 `chrome-agent crawl`（默认 `markdown:true`），确认不再抛 ReferenceError 且产出 markdown 文件；记录命令与结果到 verification.md
- [x] 3.3 确认 `markdown:false` 路径字节级不变（现有 2 个用例仍绿 = 证据）
- [x] 3.4 确认 C10 不触发：`git diff --name-only` 仅含 `scripts/lib/crawl_scrapling.mjs` + 测试文件，不含 tracked files

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 `verification.md`（覆盖 spec-to-implementation 映射：5 个 scenario 各自的证据；task-to-evidence：Slice A/B 的测试输出）
- [x] 4.2 基于 verification.md 生成 `writeback.md`：回写目标 = `openspec/specs/` 下 fetch 能力 spec delta（归档时提升）；C10 不触发（记录已核实）；无项目页回写（架构审查报告是外部临时文件）
- [x] 4.3 归档前 `openspec status` apply-ready；归档提交把 spec delta 提升为 frozen，关闭 change
