# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `repo://chrome-agent/openspec/specs/site-strategy-schema/spec.md` — 站点策略文件 schema 与受控词汇表
  - `repo://chrome-agent/openspec/specs/anti-crawl-schema/spec.md` — 反爬策略文件 schema
  - `repo://chrome-agent/openspec/specs/strategy-guided-crawl/spec.md` — crawl 能力的行为规范
- `project_page_ref`:
  - `repo://my-wiki/docs/workflow-experience/vampire-survivors-wiki-scrape.md` — 本次策略构建的经验来源
- `additional_context_refs`:
  - `repo://chrome-agent/sites/README.md` — 策略库目录与格式规范
  - `repo://chrome-agent/docs/playbooks/scrapling-fetchers.md` — fetcher 选择参考
  - `repo://chrome-agent/configs/engine-registry.json` — 引擎注册表

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（具体为 `site-strategy-schema`, `anti-crawl-schema`, `strategy-guided-crawl`）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  1. `sites/strategies/vampire.survivors.wiki/strategy.md` — 新建站点策略文件
  2. `sites/strategies/vampire.survivors.wiki/_attachments/clean-mediawiki.sh` — 清洗脚本
  3. `sites/strategies/vampire.survivors.wiki/_attachments/extract-links.py` — 链接提取脚本
  4. `docs/patterns/mediawiki-extraction.md` — 通用 MediaWiki 提取模式参考
  5. `sites/strategies/registry.json` — 策略索引（新增条目）
  6. `AGENTS.md`（section 7 Strategy Library Governance）— 策略库治理规则
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 变更归档时（archive）同步到 AGENTS.md，策略文件立即写入仓库

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- `registry.json` 为索引摘要，与 frontmatter 不一致时以 frontmatter 为准
- 新增站点策略必须同时更新 `registry.json`

## 待确认项

- [x] 已确认标准页引用（site-strategy-schema, anti-crawl-schema, strategy-guided-crawl）
- [x] 已确认项目页引用（vampire-survivors-wiki-scrape 经验文档）
- [x] 已确认回写目标与权限（仓库内文件，无需外部权限）
- [x] 已确认异常处理与冲突策略（frontmatter 权威 + registry 索引同步）
