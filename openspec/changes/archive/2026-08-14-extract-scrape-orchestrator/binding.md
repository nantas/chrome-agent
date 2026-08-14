# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/playbooks/chrome-agent-global-install.md` Case 6 + Installed Hash Semantics（C10 同步机制，cli.mjs 是 trigger 非 destination）、`docs/GOVERNANCE.md` §3（change 生命周期）、`docs/adr/0013-four-dimensional-domain-model.md` §4.4 Mirror Anti-Patterns（模块内联编排无 seam = 反模式）、`openspec/specs/fetch/spec.md` requirement `crawl-scrapling-orchestrator-is-a-seam-module`（本次是同类 seam 模式的第二实例，遵循既有纪律）
- `project_page_ref`: 架构再审查报告候选 D（cli.mjs god module handler 抽取，交接 `outputs/handoffs/20260814-arch-review-remaining-work/handoff.md`）；`scripts/lib/crawl_scrapling.mjs`（seam 模块范本，runScrape 与其同构）；`tests/crawl_scrapling.test.mjs`（纪律测试三件套范本：bare-call + flat-call + behavior 注入）；`openspec/changes/archive/2026-08-12-extract-crawl-scrapling-orchestrator/`（同类先例 change，binding/proposal/specs/design/tasks 结构复刻）
- `additional_context_refs`: `scripts/chrome-agent-cli.mjs:2594-2803`（runScrape 提取对象，210 行）、`:3667`（唯一 dispatch 调用点）、`:2532`（extractAllLinks，scrape 专属纯函数）、`:2568`（buildScrapeReport，scrape 专属 report builder）、`~/.agents/scripts/.chrome-agent-installed-hash`（需在归档时刷新至当时 HEAD）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `~/.agents/scripts/chrome-agent.mjs`（重新复制 runtime；C10：cli.mjs 是 trigger，同步动作=刷新 runtime 全局副本）；`~/.agents/scripts/.chrome-agent-installed-hash`（刷新至当前 HEAD）；`docs/architecture/04-cli-reference.md`（若 scrape 命令内部委托关系有文档则同步）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前；归档提交内一并完成 C10 同步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- runScrape 的外部行为（scrape 命令产出）SHALL 字节级不变——这是纯结构重构，非行为变更
- seam 表面 SHALL 沿用 runCrawlScrapling 已建立的 grouped concern bundle 模式（api.fs / api.report / api.handoff / api.engine / api.cache / api.pool / api.traversal / api.convert），不引入新的 bundle 形状
- C10 同步在归档 commit 内执行（cp runtime + 刷 hash），不另起提交

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（含 C10 全局同步）
- [x] 已确认异常处理与冲突策略（extractAllLinks / buildScrapeReport 经 api 注入保留在 cli.mjs，不移动）
