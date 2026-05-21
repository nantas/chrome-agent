# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
  - `specs/cli/spec.md` 覆盖两个 requirement：`maxPages-null-means-unlimited` 和 `maxPages-null-guard-in-conditions`
  - 实现范围：`scripts/chrome-agent-cli.mjs` 共 11 处改动，Python 端不改
- [x] 1.2 确认依赖前置条件与外部协作项
  - 无外部依赖，纯 JS 内部改动

## 2. 核心实现任务

- [x] 2.1 移除解构默认值（4 处）
  - 文件: `scripts/chrome-agent-cli.mjs`
  - L1979 `runCrawl()`: `maxPages = 3` → `maxPages = null`
  - L2071 `runCrawlMediawikiApi()`: `maxPages = 3` → `maxPages = null`
  - L2315 `runCrawlScrapling()`: `maxPages = 3` → `maxPages = null`
  - L2753 `runScrape()`: `maxPages = 10` → `maxPages = null`
  - 验证: grep `maxPages = [0-9]` 应无结果

- [x] 2.2 移除 main() 调用点默认值填充（2 处）
  - 文件: `scripts/chrome-agent-cli.mjs`
  - L3717: `parsed.maxPages ?? 3` → `parsed.maxPages`
  - L3739: `parsed.maxPages ?? 10` → `parsed.maxPages`
  - 验证: grep `maxPages \?\?` 应无结果

- [x] 2.3 修正条件判断为 null-safe（5 处）
  - 文件: `scripts/chrome-agent-cli.mjs`
  - L2118: `if (maxPages) {` → `if (maxPages != null) {` — MediaWiki spawnSync 传参
  - L2392: `visited.size < maxPages` → `(maxPages == null || visited.size < maxPages)` — Scrapling while 循环
  - L2444: `queue.length + visited.size < maxPages` → `(maxPages == null || queue.length + visited.size < maxPages)` — 分页入队
  - L2448: `queue.length + visited.size < maxPages` → `(maxPages == null || queue.length + visited.size < maxPages)` — 分页 URL 入队
  - L2812: `visited.size < maxPages` → `(maxPages == null || visited.size < maxPages)` — scrape while 循环
  - 验证: 所有 `maxPages` 使用点均已覆盖，无遗漏的裸比较

## 3. 收敛与验证准备

- [x] 3.1 整理需要进入 verification 的证据与检查点
  - grep 验证无残留默认值
  - grep 验证无残留 `?? 3` / `?? 10`
  - grep 验证所有 `maxPages` 使用点均做了 null-safe 处理
- [x] 3.2 标记需要进入 writeback 的摘要与状态变更
  - `openspec/specs/cli/cli-interface.md`: 更新 maxPages 行为声明
  - `docs/architecture/04-cli-reference.md`: 更新参数说明

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
