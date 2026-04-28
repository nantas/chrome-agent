# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `20_项目/chrome-agent/chrome-agent.md`
- `additional_context_refs`:
  - `repo://chrome-agent` (当前执行仓库)
  - `docs/plans/2026-03-30-chrome-agent-goal-scope-realignment-design.md` (之前 re-scope 规划)
  - `openspec/specs/scrapling-first-browser-workflow/spec.md` (已验证的 Scrapling-first 规范)
  - `docs/decisions/2026-04-23-scrapling-first-workflow.md` (Scrapling-first 决策记录)

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写，不替代 spec delta
- 非真源说明：项目页面（Obsidian）不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `repo://orbitos` 下的项目页面：`20_项目/chrome-agent/chrome-agent.md`
  - Writeback 明细页面：`20_项目/chrome-agent/Writeback记录.md`
- `writeback_owner`: `spec-ops` 或当前 agent 中的 design 角色
- `writeback_timing`: 本 change 的 `verification` 阶段完成后

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 执行仓库路径使用 `repo://<repo_id>` 语义，不记录宿主机绝对路径
- 项目页面只保留治理入口、最新状态摘要与回写规则；阶段规划与运行细节下沉到子页

## 待确认项

- [ ] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
