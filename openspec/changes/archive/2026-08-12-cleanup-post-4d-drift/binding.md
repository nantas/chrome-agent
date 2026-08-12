# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/GOVERNANCE.md` §3（change 生命周期）、`docs/adr/0013-four-dimensional-domain-model.md`（镜像等价契约来源）
- `project_page_ref`: `docs/architecture/00-target-architecture.md` §3.1（convert 等价测试声明）、§4.3（golden snapshot 契约）
- `additional_context_refs`: 架构审查报告候选 2/3/7（2026-08-12 improve-codebase-architecture 输出）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（本 change 的 delta）
- 非真源说明：`docs/plans/2026-05-19-structure-refactor-and-docs.md` 为历史计划，不回写

## 回写目标

- `writeback_targets`: `docs/architecture/01-overview.md`（目录树移除 discovery_summary.py）；`CONTEXT.md`（§shared lib 段落过期从句）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 归档时必须回填 delta 到 `openspec/specs/`（含 REMOVED 的删除）

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
