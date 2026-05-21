# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/cli/cli-interface.md`
- `project_page_ref`: `docs/architecture/04-cli-reference.md`
- `additional_context_refs`: `docs/architecture/02-pipeline-flow.md`, `scripts/chrome-agent-cli.mjs`

## Source of Truth

- 行为规范真源：`specs/cli/cli-interface.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `openspec/specs/cli/cli-interface.md`, `docs/architecture/04-cli-reference.md`
- `writeback_owner`: 本 change
- `writeback_timing`: 实现完成后一次性回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本 change 为纯 CLI 内部行为调整，无跨仓库回写

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
