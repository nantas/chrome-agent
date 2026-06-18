# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/scrapling-bulk-fetch-contract/` (empty dir, 本次 ADD)
  - `openspec/specs/strategy-guided-crawl/` (empty dir, 本次 ADD)
  - `openspec/specs/pipeline-discovery-summary/` (empty dir, 本次 ADD)
- `project_page_ref`:
  - `docs/architecture/02-pipeline-flow.md` (管线数据流，需更新 scrapling fallback 路径描述)
  - `docs/architecture/04-cli-reference.md` (CLI 路由图，需新增 sitemap 分支)
  - `docs/architecture/06-engine-selection.md` (引擎选择决策树，需新增 sitemap discovery)
  - `docs/architecture/03-strategy-schema.md` (策略 schema，需新增 `discovery` 块定义)
- `additional_context_refs`:
  - `sites/strategies/docs.gameanalytics.com/strategy.md` (目标站点策略，本 change 内改写 frontmatter)
  - `sites/strategies/registry.json` (策略注册表，本 change 内更新条目)
  - `scripts/chrome-agent-cli.mjs` (主要修改目标文件)
  - `~/.agents/skills/chrome-agent/SKILL.md` (skill 层 Crawl Confirmation Gate 消费 discovery_summary.json)
  - 废弃 change: `openspec/changes/crawl-scrapling-pages-scope/` (内容已吸收进本 change)

## Source of Truth

- 行为规范真源：`specs/sitemap-driven-crawl/spec.md` (新能力) + `specs/crawl-scrapling-pages-scope/spec.md` (L1 bugfix)
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `sites/strategies/docs.gameanalytics.com/strategy.md` — 更新 frontmatter：删除 `api:` 块，新增 `discovery:` 块
  - `sites/strategies/registry.json` — 更新 `docs.gameanalytics.com` 条目
  - `docs/architecture/04-cli-reference.md` — CLI 路由图新增 sitemap 分支
  - `docs/architecture/06-engine-selection.md` — 引擎决策树新增 sitemap discovery
  - `docs/architecture/03-strategy-schema.md` — schema 文档新增 `discovery` 块
  - `docs/architecture/02-pipeline-flow.md` — 管线流新增 sitemap→scrapling 路径
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: 实现完成并通过全部验证后，由 `/opsx-apply` 流程执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- GameAnalytics 策略文件 (frontmatter) 的字段真源为本 change 中的 `specs/sitemap-driven-crawl/spec.md` 定义的 discovery schema
- 废弃 change `crawl-scrapling-pages-scope` 不执行 writeback，直接删除目录

## 待确认项

- [x] 已确认标准页引用（新增三个 capability spec）
- [x] 已确认项目页引用（4 份架构文档 + 1 份策略 + registry）
- [x] 已确认回写目标与权限
- [x] 已确认废弃 change 处理策略
