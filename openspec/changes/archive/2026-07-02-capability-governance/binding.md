# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/explore-workflow/spec.md`, `openspec/specs/governance/spec.md`
- `project_page_ref`: `docs/architecture/00-target-architecture.md`, `docs/plans/4d-architecture-refactor.md`
- `additional_context_refs`: `docs/GOVERNANCE.md`, `AGENTS.md`, `C10N7EX7.md`

## Source of Truth

- 行为规范真源：`specs/capability-registry/spec.md` + `specs/explore-workflow/spec.md` + `specs/governance/spec.md`（本次 change 输出）
- 数据真源：`configs/capability-registry.yaml`（新增，脚本可读的能力注册表）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` §0.5 — 新增 C11 约束
  - `docs/GOVERNANCE.md` — 新增 §7 派生文档同步原则
  - `docs/playbooks/capability-extension.md` — 新增操作手册
  - `docs/architecture/02-pipeline-flow.md` — 更新 discover 引用（若涉及）
- `writeback_owner`: 本 change 执行者
- `writeback_timing`: 所有 implementation tasks 完成后

## 同步约束

- `capability-registry.yaml` 是能力注册的 SSOT
- `doctor --check capabilities` 交叉校验 registry ↔ code ↔ specs ↔ AGENTS.md
- openspec change 归档前必须 `doctor --check capabilities` 通过

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
