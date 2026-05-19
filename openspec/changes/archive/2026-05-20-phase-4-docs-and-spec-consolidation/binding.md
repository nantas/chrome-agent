# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/governance/governance.md`（合并后的治理域 spec，原 agents-governance 已合并至此）
- `project_page_ref`: `AGENTS.md`
- `additional_context_refs`:
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md` — Phase 4 详细设计规划
  - `docs/governance-and-capability-plan.md` — 项目路线图与能力全景
  - `sites/README.md` — 策略库治理

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：AGENTS.md 不得替代 spec delta 作为实现与验证依据；回写只移入结论与链接，不复制整份 spec

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` — 瘦身：删除已迁移至 `docs/architecture/` 的段落，替换为索引链接
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md` — 标注 Phase 4 完成状态
  - `README.md` — 补充 `docs/architecture/` 目录引用
- `writeback_owner`: 实施者
- `writeback_timing`: Step 4 完成后一次性回写

## 同步约束

- AGENTS.md 与 `docs/architecture/` 不一致时，以 `docs/architecture/` 为准（架构文档为唯一真源）
- Spec 合并（D2）中新 spec 文件与旧 spec 不一致时，以新 spec 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若 AGENTS.md 中存在过时代码路径引用，必须在 Step 0 修复后、Step 4 瘦身前完成同步

## 待确认项

- [x] 已确认标准页引用：`agents-governance`
- [x] 已确认项目页引用：`AGENTS.md` 为主要治理文档，`docs/plans/2026-05-19-structure-refactor-and-docs.md` 为详细设计依据
- [x] 已确认回写目标与权限：三个文件均为本仓库内直接可写
- [x] 已确认异常处理与冲突策略：Step 0 先修复过时内容，Step 4 再瘦身，避免冲突窗口
