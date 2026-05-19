# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/global-capability-cli/spec.md` — CLI 命令面行为规范（crawl 命令的外部契约）
- `project_page_ref`: `docs/plans/2026-05-19-structure-refactor-and-docs.md` — 结构优化重构总体规划（Change 5 定义）
- `additional_context_refs`:
  - `openspec/specs/agents-governance/spec.md` — CLI 函数拆分治理约束（God Object 拆分模式）
  - `AGENTS.md` — Node.js 脚本约定（ESM、JSON-first、函数声明风格）

## Source of Truth

- 行为规范真源：`specs/global-capability-cli/spec.md`（外部接口契约，不因本次重构而变）
- 项目页面角色：上下文输入（Change 5 目标定义）、治理展示（进度追踪）、结果回写（完成后更新状态）
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md` — 更新 Phase 3 完成状态标记
- `writeback_owner`: chrome-agent maintainer
- `writeback_timing`: 验证通过后，在 writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本次为纯内部重构，不改变 CLI 外部接口，因此不产生 spec delta（`specs/` 章节仅声明"无行为变更"）

## 待确认项

- [x] 已确认标准页引用（`global-capability-cli` 为 CLI 外部契约）
- [x] 已确认项目页引用（结构优化重构规划 Change 5）
- [x] 已确认回写目标与权限（仅更新规划文档状态标记）
- [x] 已确认异常处理与冲突策略（纯内部重构，无行为变更）
