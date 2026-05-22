# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/page-assignment/` — 页面分配行为规范真源（`assignment_priority` 优先级链、`page_categories` 补充映射）
- `project_page_ref`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — BOI 站点策略配置，本次 change 的唯一修改目标
- `additional_context_refs`:
  - `openspec/changes/archive/2026-05-20-fix-pipeline-assignment-and-output/` — 前一 change，实现了 `page_categories` 和 `mw_category_aliases` 机制，本次在其基础上补充映射条目

## Source of Truth

- 行为规范真源：`openspec/specs/page-assignment/`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — `assignment_priority` 追加 `Attributes`、`Completion Marks`；`page_categories` 追加 `Runes`、`Special cards`、`Mini-bosses`、`Item pools` 映射
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- BOI 策略文件的 `assignment_priority` 和 `page_categories` 字段以 spec delta 为权威格式

## 待确认项

- [x] 已确认标准页引用 — `page-assignment` spec
- [x] 已确认项目页引用 — BOI 策略文件
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略 — 配置变更，无回滚风险
