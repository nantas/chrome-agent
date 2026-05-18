# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/global-workflow-skill/spec.md`（修改：新增 Handoff Gate 章节）
  - `openspec/specs/handoff-emission/spec.md`（新增：handoff 文档生命周期与格式规范）
- `project_page_ref`:
  - （暂无特定项目页，handoff 文档本身将成为 chrome-agent 仓库内的问题记录入口）
- `additional_context_refs`:
  - `scripts/chrome-agent-cli.mjs`（handoff 文档生成逻辑新增点）
  - `skills/chrome-agent/SKILL.md`（Handoff Gate 新增点）
  - `AGENTS.md`（可能新增 handoff 工作流说明）
  - `docs/playbooks/scrapling-fetchers.md`（现有 playbook，不影响）
  - `docs/decisions/README.md`（视新增设计决策而定）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md`（新增 handoff 工作流说明）
  - `skills/chrome-agent/SKILL.md`（新增 Handoff Gate 章节）
- `writeback_owner`: chrome-agent
- `writeback_timing`: 验证通过后执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（1 个新增 + 1 个修改）
- [x] 已确认项目页引用（暂无）
- [x] 已确认回写目标与权限（AGENTS.md + SKILL.md）
- [x] 已确认异常处理与冲突策略
