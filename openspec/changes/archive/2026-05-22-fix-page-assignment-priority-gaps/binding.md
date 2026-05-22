# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/page-assignment/` — 页面分配行为真源（优先级链、MW category 匹配、source_categories 分配）
- `project_page_ref`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — BOI 站点策略，包含 homepage.categories、assignment_priority、page_categories 等配置
  - `scripts/pipeline/pipeline/page_assigner.py` — page_assigner 实现
- `additional_context_refs`:
  - `openspec/changes/archive/2026-05-20-fix-pipeline-assignment-and-output/` — 前一次 change：S-1/S-2 修复 source_categories 匹配 + MW category aliases + page_categories fallback
  - `scripts/pipeline/pipeline/phases/discovery_homepage.py` — Phase 0 homepage discovery，source_categories 生成逻辑

## Source of Truth

- 行为规范真源：本 change 的 `specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — 更新 assignment_priority 顺序并补全缺失条目
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
