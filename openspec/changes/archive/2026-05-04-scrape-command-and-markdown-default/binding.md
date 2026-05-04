# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos` — Orbitos Spec Standard v0.3（见 `AGENTS.md` §6）
- `project_page_ref`: `repo://chrome-agent/AGENTS.md` — 仓库级治理文档，承载服务身份、能力框架、治理规则
- `additional_context_refs`:
  - `openspec/specs/global-capability-cli/spec.md` — CLI 命令面行为规范
  - `openspec/specs/strategy-guided-crawl/spec.md` — 当前 crawl 能力行为规范
  - `openspec/specs/output-lifecycle/spec.md` — 产物生命周期规范

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（在 `openspec/specs/` 下）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面（AGENTS.md、Obsidian vault）不得替代 spec delta 作为实现与验证依据；实现代码必须以 `openspec/specs/` 中的 frozen spec 为权威来源

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` — §2 能力框架中新增 `scrape` 命令的 capability 描述
  - `openspec/specs/global-capability-cli/spec.md` — CLI 命令面扩展（新增 `scrape` 命令签名）
  - `openspec/specs/strategy-guided-crawl/spec.md` — 默认输出格式从 HTML 改为 Markdown
  - 新增 `openspec/specs/scrape-command/spec.md` — scrape 命令完整行为规范
  - 新增 `openspec/specs/markdown-conversion-pipeline/spec.md` — 共享 Markdown 转换能力规范
- `writeback_owner`: chrome-agent maintainers
- `writeback_timing`: change 验证完成后，所有 spec freeze 后统一回写

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- AGENTS.md 中的能力表格只更新条目状态与链接，不内嵌详细规范文本

## 待确认项

- [x] 已确认标准页引用 — `repo://orbitos`
- [x] 已确认项目页引用 — `repo://chrome-agent/AGENTS.md`
- [x] 已确认回写目标与权限 — 均为仓库内文件，无需外部权限
- [x] 已确认异常处理与冲突策略 — 遵循 AGENTS.md §6 Spec and Change Governance
