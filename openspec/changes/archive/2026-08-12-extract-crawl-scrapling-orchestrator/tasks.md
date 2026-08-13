# Tasks

> 涉及 `scripts/chrome-agent-cli.mjs`（提取）+ 新建 `scripts/lib/crawl_scrapling.mjs`（.mjs）+ `tests/crawl_scrapling.test.mjs`（node:test）+ C10 全局同步。代码任务拆 vertical slice（RED→GREEN）。

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/fetch/spec.md` 覆盖：`crawl-scrapling-orchestrator-is-a-seam-module`（3 scenario：可导入测试 / 输出字节级不变 / api bundle 一次性构建无循环依赖）
- [x] 1.2 确认提取边界：仅 runCrawlScrapling（2471–2913）一个函数迁移；全部 ~26 个依赖经 `api` bundle 注入（零循环依赖，无 helper 搬迁）

## 2. 核心实现任务

### Slice A — 提取 runCrawlScrapling + api bundle 注入

- [x] 2.1 (RED) `tests/crawl_scrapling.test.mjs`：构建 stub `api`（纯 helper 用真实/复制，副作用 helper 打桩）+ ctx，import 新模块（此时不存在 → FAIL）；断言 preflight 失败路径、traversal 顺序、manifest 构建
- [x] 2.2 (GREEN) 新建 `scripts/lib/crawl_scrapling.mjs`：迁入 runCrawlScrapling（签名 `runCrawlScrapling(ctx, opts, api)`），内部全部 ~26 个依赖改走 `api.*`，不动 helper 本身
- [x] 2.3 (GREEN) cli.mjs 删除原 runCrawlScrapling；构建一次 `crawlApi`（fs + 所有 helper + buildScraplingExtractionArgs）；3 调用点（2202/2365/2369）改为 `await runCrawlScrapling(ctx, opts, crawlApi)`；import 新模块
- [x] 2.4 (验证) `node --test tests/crawl_scrapling.test.mjs` GREEN；`node --test tests/crawl-scrapling-pages-scope.test.mjs` 集成回归绿；`node --check` cli.mjs + 新模块

### Slice B — 行为保真验证

- [x] 2.5 (验证) crawl 命令产出字节级不变：对同一 target/strategy 对比提取前后 manifest + report（若环境可实跑；否则逻辑等价审查 + 测试覆盖）；`chrome-agent doctor` 无回归

## 3. 收敛与验证准备

- [x] 3.1 证据清单：crawl_scrapling.test.mjs 由 RED→GREEN、crawl-scrapling-pages-scope 集成回归绿、cli.mjs 行数减少、共享 helper export grep 无遗漏
- [x] 3.2 回写摘要：全局 runtime 副本 + installed-hash（C10）；04-cli-reference（如有委托关系文档）

## 4. 验证与回写收敛（含 C10）

- [x] 4.1 生成 verification.md（spec→code 映射 + 全量测试复跑 + 行为保真证据 + C10 同步证据）
- [x] 4.2 生成 writeback.md（C10 同步动作记录；04-cli-reference 评估）
- [x] 4.3 执行 writeback：`cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs` + `git rev-parse HEAD > ~/.agents/scripts/.chrome-agent-installed-hash`；`chrome-agent doctor` 确认 `repo_freshness: ok`；`doctor --check capabilities`（C11）；归档 `archive/2026-08-12-extract-crawl-scrapling-orchestrator/`，回填 fetch delta 到 `openspec/specs/fetch/spec.md`
