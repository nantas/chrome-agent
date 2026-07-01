# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/discovery-phase-unification/spec.md`, `openspec/specs/pipeline-orchestration/spec.md`
- `project_page_ref`: `docs/architecture/00-target-architecture.md` (能力目标架构 §3.4 Discover), `docs/adr/0013-four-dimensional-domain-model.md`
- `additional_context_refs`: `docs/architecture/07-explore-workflow.md`, `docs/plans/4d-architecture-refactor.md`

## Source of Truth

- 行为规范真源：`specs/discover-kernel/spec.md`（本次 change 输出）
- 已有规范：`openspec/specs/discovery-phase-unification/spec.md`（pipeline discover 阶段历史规范）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` §2 Capability Framework — 更新 Discover 能力声明（pipeline 不再有 discover 阶段）
  - `docs/architecture/07-explore-workflow.md` — 新增 discover 步骤说明
  - `docs/architecture/01-overview.md` — 更新目录结构（pipeline phases 去 discovery）
- `writeback_owner`: 本 change 执行者
- `writeback_timing`: 所有 implementation tasks 完成后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
