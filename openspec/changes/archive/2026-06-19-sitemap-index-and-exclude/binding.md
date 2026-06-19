# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/sitemap-driven-crawl/spec.md` (现存，sitemap base capability)
- `project_page_ref`:
  - `AGENTS.md` — 治理入口
  - `docs/architecture/03-strategy-schema.md` — discovery block schema
  - `docs/architecture/02-pipeline-flow.md` — pipeline 路径描述
  - `docs/architecture/06-engine-selection.md` — 引擎选择决策树
- `additional_context_refs`:
  - `openspec/changes/sitemap-driven-crawl/` — 父 capability 的完整 change artifacts
  - `sites/strategies/docs.gameanalytics.com/strategy.md` — 参考策略模板

## Source of Truth

- 行为规范真源：`specs/sitemap-index-and-exclude/spec.md` (本 change)
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据
- 父 capability `sitemap-driven-crawl` 的 spec 为上游契约，本 change 的 spec 在其基础上追加 `sitemap index` 和 `exclude_patterns` 两个增量能力

## 回写目标

- `writeback_targets`:
  - `docs/architecture/03-strategy-schema.md` — 新增 `exclude_patterns` 字段文档
  - `docs/architecture/02-pipeline-flow.md` — sitemap index 解析路径描述
  - `docs/architecture/06-engine-selection.md` — sitemap index 分支
  - `skills/chrome-agent/SKILL.md` — sitemap index 状态更新（已支持）
  - `~/.agents/skills/chrome-agent/SKILL.md` — 同步
  - `sites/strategies/posthog.com/strategy.md` — 新增 PostHog 策略
  - `sites/strategies/registry.json` — 注册 PostHog 策略
- `writeback_owner`: chrome-agent maintainer
- `writeback_timing`: 实现完成后，验证通过后立即回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- PostHog 策略文件为本次 change 的产物之一，在 change 内直接创建
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用 (父 capability `sitemap-driven-crawl`)
- [x] 已确认项目页引用 (4 architecture docs + skill + strategy)
- [x] 已确认回写目标与权限 (repo-local, 无外部依赖)
- [x] 已确认异常处理与冲突策略 (spec 优先)
