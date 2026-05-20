# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/page-assignment/` — 页面分配行为真源（优先级链、MW category 匹配、source_categories 分配）
  - `openspec/specs/pipeline-orchestration/` — Pipeline 编排与 phase dispatch 行为真源
  - `openspec/specs/pipeline-cli-entry/` — CLI 参数定义与透传行为真源
  - `openspec/specs/pipeline-resume/` — Pipeline 状态管理与增量恢复行为真源
  - `openspec/specs/pipeline-convert-phase/` — Phase Convert 行为真源（增量落盘）
- `project_page_ref`:
  - `handoffs/20260519-crawl-bindingofisaacrebirth-wiki-gg/handoff.md` — 5 个 Issue (S-1/S-2/S-3/P-1/P-2) 的原始报告
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — BOI 站点策略，包含 homepage.categories、assignment_priority、page_categories 等配置
- `additional_context_refs`:
  - `openspec/changes/fix-pipeline-quality-gaps/` — 前一次管线质量修复 change（已归档），解决了 Phase 统一、Phase 0 功能缺口等问题
  - `scripts/pipeline/pipeline/page_assigner.py` — 当前 page_assigner 实现（S-1/S-2 根因所在）
  - `scripts/pipeline/pipeline/phases/discovery_homepage.py` — Phase 0 homepage discovery 实现
  - `scripts/chrome-agent-cli.mjs` — CLI 入口（P-1 根因所在）

## Source of Truth

- 行为规范真源：本 change 的 `specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：handoff 文档的 5 个 Issue 作为问题清单输入，所有行为决策以 specs/ 为准

## 回写目标

- `writeback_targets`:
  - `handoffs/20260519-crawl-bindingofisaacrebirth-wiki-gg/handoff.md` — 追加修复状态，标记 S-1/S-2/S-3/P-1/P-2 解决状态
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — 添加 `mw_category_aliases` 字段到 homepage.categories 条目
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- handoff 中的 Issue 编号（S-1/S-2/S-3/P-1/P-2）在回写时映射到 spec requirement 名称
- BOI 策略文件的 `mw_category_aliases` 字段以 spec delta 为权威格式

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
