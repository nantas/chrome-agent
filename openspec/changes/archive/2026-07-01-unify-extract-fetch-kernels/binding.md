# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/unified-html-preprocessing/spec.md`, `openspec/specs/pipeline-fetch-phase/spec.md`
- `project_page_ref`: `docs/architecture/00-target-architecture.md` (能力目标架构 §3.2 Fetch + §3.3 Extract), `docs/adr/0013-four-dimensional-domain-model.md`
- `additional_context_refs`: `docs/architecture/05-converter-architecture.md`, `docs/plans/4d-architecture-refactor.md`

## Source of Truth

- 行为规范真源：`specs/extract-kernel/spec.md` + `specs/fetch-kernel/spec.md`（本次 change 输出）
- 已有规范：`openspec/specs/unified-html-preprocessing/spec.md`（preprocessor 行为契约）、`openspec/specs/pipeline-fetch-phase/spec.md`（fetch phase 流程契约）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` §2 Capability Framework — 更新 Extract/Fetch 能力内核声明
  - `docs/architecture/01-overview.md` — 更新 Fetch 路径描述
  - `docs/architecture/05-converter-architecture.md` — 添加 `convert_page_full` 编排入口说明
- `writeback_owner`: 本 change 执行者
- `writeback_timing`: 所有 implementation tasks 完成后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
