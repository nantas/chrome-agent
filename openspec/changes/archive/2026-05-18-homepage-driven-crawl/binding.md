# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/mediawiki-api-extraction-pipeline/spec.md`（pipeline 行为真源）、`openspec/specs/pipeline-strategy-schema/spec.md`（策略 schema 真源）、`openspec/specs/pipeline-converters/spec.md`（converter 行为真源）
- `project_page_ref`: `/Users/nantasmac/projects/my-wiki/docs/workflow-experience/binding-of-isaac-wiki-crawl.md`（本次 change 的问题来源与验证场景）
- `additional_context_refs`:
  - `openspec/specs/unified-link-fixer/spec.md` — link_fixer 已修复部分问题，converter 需对齐
  - `openspec/specs/strategy-guided-crawl/spec.md` — 现有 crawl 能力边界
  - `openspec/specs/incremental-reprocess/spec.md` — 现有 reprocess 能力，resume 需扩展

## Source of Truth

- 行为规范真源：本 change 的 `specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；本次 change 从项目页面提取问题清单，但所有行为决策以 specs/ 为准

## 回写目标

- `writeback_targets`:
  - `/Users/nantasmac/projects/my-wiki/docs/workflow-experience/binding-of-isaac-wiki-crawl.md` — 更新 P-line / S-line 问题解决状态
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — 添加 `api.homepage` 配置块与 KI-7
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 项目页面中的问题编号（P-1~P-6, S-1~S-4）在回写时映射到 spec requirement 名称
- 策略文件的 `api.homepage` 配置以 spec delta 为权威格式

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
