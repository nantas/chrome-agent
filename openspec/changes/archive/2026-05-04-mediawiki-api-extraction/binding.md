# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `repo://chrome-agent/openspec/specs/site-strategy-schema/spec.md` — 站点策略 schema（本次 MODIFIED，新增 api 字段）
  - `repo://chrome-agent/openspec/specs/mediawiki-extraction-patterns/spec.md` — MediaWiki 噪音分类学与清洗模式（本次引用，作为 fallback 参考）
  - `repo://chrome-agent/openspec/specs/strategy-guided-crawl/spec.md` — crawl 能力的行为规范（本次引用，作为集成点）
  - `repo://chrome-agent/openspec/specs/engine-contracts/spec.md` — 引擎选择映射（本次引用，明确 API 路径不是新引擎）
- `project_page_ref`:
  - `repo://my-wiki/docs/workflow-experience/balatro-wiki-structured-crawl.md` — API 路线的实际踩坑经验与问题总结
  - `repo://my-wiki/docs/workflow-experience/vampire-survivors-wiki-scrape.md` — Scrapling 路线的对比基准
  - `repo://my-wiki/tools/balatro-wiki-converter/` — 现有 API 提取工具链实现（html2md.py, batch_convert.py, organize.py, fetch_pages.py）
- `additional_context_refs`:
  - `repo://chrome-agent/sites/strategies/balatrowiki.org/strategy.md` — 本次策略扩展的验证目标
  - `repo://chrome-agent/sites/strategies/vampire.survivors.wiki/strategy.md` — 对比站点的策略文件
  - `repo://chrome-agent/sites/strategies/vampire.survivors.wiki/_attachments/clean-mediawiki.sh` — 现有 Scrapling 后处理工具（与 API 路径互补，不替代）
  - `repo://chrome-agent/sites/strategies/registry.json` — 策略索引（本次需补充 balatrowiki.org 条目）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（本次新增 `mediawiki-api-extraction`，修改 `site-strategy-schema`）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；balatro-wiki-structured-crawl.md 提供经验证据但不定义行为规范

## 回写目标

- `writeback_targets`:
  1. `openspec/specs/site-strategy-schema/spec.md` — MODIFIED：新增 api 字段及其子字段规范
  2. `openspec/specs/mediawiki-api-extraction/spec.md` — NEW：API 提取管线行为规范
  3. `scripts/mediawiki-api-extract` — NEW：CLI 工具（Phase A+B+C 实现）
  4. `sites/strategies/balatrowiki.org/strategy.md` — MODIFIED：增加 api 字段
  5. `sites/strategies/vampire.survivors.wiki/strategy.md` — MODIFIED：增加 api 字段
  6. `sites/strategies/registry.json` — MODIFIED：补充 balatrowiki.org 条目 + 现有条目增加 backend 字段
  7. `AGENTS.md` — MODIFIED：crawl 路径增加 MediaWiki API 路由分支
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: CLI 工具和策略文件在实现阶段立即写入仓库；AGENTS.md 在变更归档时同步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- `registry.json` 为索引摘要，与 frontmatter 不一致时以 frontmatter 为准
- API 管线与 Scrapling 管线为**互补关系**：API 失败时 fallback 到 Scrapling，不得因 API 可用就禁用 Scrapling

## 待确认项

- [x] 已确认标准页引用（site-strategy-schema, mediawiki-extraction-patterns, strategy-guided-crawl, engine-contracts）
- [x] 已确认项目页引用（balatro-wiki-structured-crawl 经验文档 + converter 工具链）
- [x] 已确认回写目标与权限（全部在 chrome-agent 仓库内，无需外部权限）
- [x] 已确认异常处理与冲突策略（API fallback → Scrapling；specs 为行为真源）
