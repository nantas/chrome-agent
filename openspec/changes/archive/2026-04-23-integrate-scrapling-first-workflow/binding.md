# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
- `project_page_ref`: `/Users/nantasmac/projects/agentic/chrome-agent/AGENTS.md`
- `additional_context_refs`: `/Users/nantasmac/projects/agentic/chrome-agent/README.md`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/decisions/2026-03-17-browser-tooling-workflow.md`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/playbooks/browser-tooling-evaluation.md`, `/Users/nantasmac/projects/obsidian-mind/30_研究/AI_Agent/网页爬取/Scrapling.md`

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `/Users/nantasmac/projects/agentic/chrome-agent/AGENTS.md`, `/Users/nantasmac/projects/agentic/chrome-agent/README.md`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/decisions/`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/playbooks/`, `/Users/nantasmac/projects/agentic/chrome-agent/sites/`
- `writeback_owner`: current repository maintainer operating through Codex/OpenSpec
- `writeback_timing`: after implementation and verification confirm the Scrapling-first workflow and its fallback boundaries

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
