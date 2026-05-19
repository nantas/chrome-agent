# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/agents-governance/spec.md`（仓库治理规范）、`openspec/specs/engine-registry/spec.md`（引擎注册不涉及）、`docs/plans/2026-05-19-structure-refactor-and-docs.md`（重构总体规划）
- `project_page_ref`: `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3（拆分 orchestrator + 重命名包的设计描述）
- `additional_context_refs`: `AGENTS.md` § Pipeline Strategy Schema 治理、§ Python 3.9 兼容性、§ `__main__.py` re-invoke 模式；`openspec/changes/fix-pipeline-quality-gaps/`（前置 change）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `docs/plans/2026-05-19-structure-refactor-and-docs.md`（更新 Change 3 状态为已完成）；`AGENTS.md`（更新 §9 Python 脚本约定中的包路径引用、`_STRATEGY_REGISTRY` 权威来源路径）
- `writeback_owner`: 实施者（agent 或人工）
- `writeback_timing`: Change 3 验证通过后、合并前

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
