# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/standards/openspec/orbitos-spec-standard-v0.3.md`
- `project_page_ref`: `repo://chrome-agent/AGENTS.md`
- `additional_context_refs`: `repo://chrome-agent/README.md`, `repo://chrome-agent/openspec/specs/output-lifecycle/spec.md`

## Source of Truth

- 行为规范真源：`openspec/specs/output-lifecycle/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `repo://chrome-agent/AGENTS.md`, `repo://chrome-agent/README.md`
- `writeback_owner`: `chrome-agent maintainers`
- `writeback_timing`: `verification 完成且结论稳定后执行一次性回写`

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
