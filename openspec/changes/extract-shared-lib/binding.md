# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/pipeline/pipeline-core.md`（管线编排行为规范）；`openspec/specs/agents-governance/spec.md`（治理约束：Python 3.9 兼容、包命名规范）
- `project_page_ref`: `docs/plans/2026-05-19-structure-refactor-and-docs.md`（结构重构总体规划，Change 1 定义）
- `additional_context_refs`: `docs/decisions/`（架构决策记录）；`AGENTS.md` §4 目录结构治理、§9 Python 脚本约定

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - Obsidian vault: `chrome-agent/Changes/2026-05-19-extract-shared-lib.md`（change 状态与结论回写）
  - 项目页面: `chrome-agent/Architecture/Change 1 — 提取共享库 lib/`（能力变更描述）
- `writeback_owner`: 执行 agent（pi）
- `writeback_timing`: change 完成验证后立即回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [ ] 已确认标准页引用
- [x] 已确认项目页引用（基于规划文档 `docs/plans/2026-05-19-structure-refactor-and-docs.md`）
- [ ] 已确认回写目标与权限（Obsidian vault 路径待确认）
- [ ] 已确认异常处理与冲突策略
