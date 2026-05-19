# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: 无直接 spec 约束（本次为纯结构性重构，不改变行为规范）
- `project_page_ref`: `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 4
- `additional_context_refs`:
  - `openspec/changes/split-orchestrator-rename-package/` (Change 3 前序)
  - `openspec/changes/extract-shared-lib/` (Change 1+2 前序)

## Source of Truth

- 行为规范真源：本次无新增 spec，不涉及 `specs/` 变更
- 项目页面角色：`docs/plans/2026-05-19-structure-refactor-and-docs.md` 作为规划上下文输入
- 非真源说明：规划文档描述了目标状态，本 change 的 design.md 为实现决策的权威来源

## 回写目标

- `writeback_targets`:
  - `docs/plans/2026-05-19-structure-refactor-and-docs.md` — 更新 Change 4 状态为已完成
  - `AGENTS.md` §9 Python 脚本约定 — 如包路径或 phase 文件引用需要更新
- `writeback_owner`: 实施者
- `writeback_timing`: 变更验证通过后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准（本次不涉及）
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 文件重命名后需确认 `AGENTS.md` 中所有 phase 文件路径引用已更新

## 待确认项

- [x] 已确认标准页引用（无 spec 变更）
- [x] 已确认项目页引用（规划文档 § Change 4）
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略（死代码删除需 LSP references 验证零引用）
