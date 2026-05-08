# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: repo://orbitos/openspec/specs/orbitos-change-v1/spec.md
- `project_page_ref`: repo://chrome-agent/docs/plans/2026-05-08-rate-limit-config-gap-problem-report.md
- `additional_context_refs`:
  - `repo://chrome-agent/openspec/specs/site-strategy-schema/spec.md`
  - `repo://chrome-agent/openspec/specs/anti-crawl-schema/spec.md`
  - `repo://chrome-agent/openspec/specs/mediawiki-api-extraction/spec.md`
  - `repo://chrome-agent/docs/decisions/`

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面（docs/plans/ 中的 problem report）不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `docs/decisions/2026-05-08-rate-limit-config-architecture.md`（新建 ADR）
  - `sites/anti-crawl/rate-limit-api.md`
  - `sites/anti-crawl/registry.json`
  - `sites/strategies/slaythespire.wiki.gg/strategy.md`
  - `sites/strategies/registry.json`
- `writeback_owner`: chrome-agent repo maintainer
- `writeback_timing`: change 归档前（所有 tasks 完成后）

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
