# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/playbooks/chrome-agent-global-install.md` Case 6 + Installed Hash Semantics（C10 同步机制，cli.mjs 是 trigger 非 destination）、`docs/GOVERNANCE.md` §3（change 生命周期）、`docs/adr/0013-four-dimensional-domain-model.md` §4.4 Mirror Anti-Patterns（模块内联编排无 seam = 反模式）
- `project_page_ref`: 架构审查报告候选 4（cli.mjs god module，唯一可测 seam 是 subprocess）来源 `/var/folders/.../architecture-review-20260812-161301.html`；`scripts/lib/scrapling-extraction-args.mjs`（lib 模块提取先例，含 spec 注释范式）；`tests/crawl-scrapling-pages-scope.test.mjs`（scrapling crawl 现有测试基础设施）
- `additional_context_refs`: `scripts/chrome-agent-cli.mjs:2471-2913`（runCrawlScrapling 提取对象）、`:2126-2369`（3 处 dispatch 调用点）、`~/.agents/scripts/.chrome-agent-installed-hash`（当前 `8111a3f`，已与 HEAD 漂移）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `~/.agents/scripts/chrome-agent.mjs`（重新复制 runtime；C10：cli.mjs 是 trigger，同步动作=刷新 runtime 全局副本）；`~/.agents/scripts/.chrome-agent-installed-hash`（刷新至当前 HEAD，顺带闭合既有漂移）；`docs/architecture/04-cli-reference.md`（如 runCrawl 内部委托关系有文档则同步）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前；归档提交内一并完成 C10 同步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- runCrawlScrapling 的外部行为（crawl 命令产出）SHALL 字节级不变——这是纯结构重构，非行为变更
- C10 同步在归档 commit 内执行（cp runtime + 刷 hash），不另起提交

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（含 C10 全局同步）
- [x] 已确认异常处理与冲突策略（既有 installed-hash 漂移顺带闭合）
