# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/agents-governance/spec.md`（治理规范）、`openspec/specs/capability-contracts/spec.md`（契约元模型）、`openspec/specs/engine-registry/spec.md`（引擎注册）
- `project_page_ref`: `AGENTS.md`（Section 8 引擎扩展治理）、`docs/governance-and-capability-plan.md`（能力路线图）
- `additional_context_refs`: `reports/2026-05-08-follow-up-issues.md`（触发本次变更的问题报告）、`scripts/mediawiki-api-extract/`（当前实现）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` Section 8 引擎概览表（如有引擎条目变更时更新）
  - `docs/playbooks/scrapling-fetchers.md`（如 fetcher 选型逻辑受影响时更新）
  - `README.md`（能力描述更新）
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 变更归档后同步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
