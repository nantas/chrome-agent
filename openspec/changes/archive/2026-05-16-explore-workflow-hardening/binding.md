# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/explore/spec.md`
- `spec_standard_ref`: `openspec/specs/explore-workflow/spec.md`
- `spec_standard_ref`: `openspec/specs/explore-backend-detection/spec.md`
- `spec_standard_ref`: `openspec/specs/sample-self-check/spec.md`
- `spec_standard_ref`: `openspec/specs/strategy-scaffold-generation/spec.md`
- `spec_standard_ref`: `openspec/specs/pipeline-converters/spec.md`
- `spec_standard_ref`: `openspec/specs/doctor-repo-freshness/spec.md`
- `spec_standard_ref`: `openspec/specs/agents-governance/spec.md`
- `spec_standard_ref`: `openspec/specs/markdown-conversion-pipeline/spec.md`
- `spec_standard_ref`: `openspec/specs/pipeline-strategy-schema/spec.md`
- `project_page_ref`: Obsidian `projects/chrome-agent/explore-workflow-hardening`（治理展示与结果回写）
- `additional_context_refs`: `AGENTS.md`, `~/.agents/skills/chrome-agent/SKILL.md`

## Source of Truth

- 行为规范真源：`specs/explore/spec.md`、`specs/explore-workflow/spec.md`、`specs/pipeline-converters/spec.md` 等上述 spec 文件
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `openspec/specs/explore/spec.md`（实施完成后同步 implementation status）
  - `openspec/specs/explore-workflow/spec.md`（实施完成后同步 implementation status）
  - `openspec/specs/pipeline-converters/spec.md`（实施完成后同步 implementation status）
  - `openspec/specs/doctor-repo-freshness/spec.md`（实施完成后同步 implementation status）
  - Obsidian `projects/chrome-agent/explore-workflow-hardening`（回写结论、状态、摘要、链接）
- `writeback_owner`: chrome-agent 仓库 maintainer
- `writeback_timing`: 本 change 的 `verification` 完成后执行回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用：所有变更目标 spec 均已列出
- [x] 已确认项目页引用：Obsidian 项目页面路径已明确
- [x] 已确认回写目标与权限：spec 回写遵循 Orbitos Change v0.3 writeback 协议
- [ ] `setup_phase` 目标暂未实现完成状态标记，回写时保留现有 Capability/Requirement/Scenario 结构，增补 `implementation_status` 字段
