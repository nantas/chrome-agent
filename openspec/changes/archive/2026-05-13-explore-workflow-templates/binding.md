# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos` (Orbitos Spec Standard v0.3)
- `project_page_ref`: 无（本次变更新建 explore 工作流，不涉及现有项目页面绑定）
- `additional_context_refs`:
  - `repo://chrome-agent/AGENTS.md`
  - `repo://chrome-agent/docs/playbooks/`
  - `repo://chrome-agent/sites/strategies/`
  - `repo://chrome-agent/sites/anti-crawl/`

## Source of Truth

- 行为规范真源：`specs/explore-workflow/spec.md`
- 项目页面角色：不适用（无对应项目页面）
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` — 更新 explore 工作流路由规则
  - `docs/playbooks/explore-workflow-conduct.md` — 新建操作手册
  - `README.md` — 能力描述更新 (如适用)
- `writeback_owner`: chrome-agent 治理
- `writeback_timing`: implementation 阶段完成后回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [ ] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
