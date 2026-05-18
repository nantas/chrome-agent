# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/api-error-semantics/spec.md`
  - `openspec/specs/homepage-driven-discovery/spec.md`
  - `openspec/specs/pipeline-strategy-schema/spec.md`
  - `openspec/specs/pipeline-cli-entry/spec.md`
  - `openspec/specs/page-assignment/spec.md`
- `project_page_ref`:
  - `repo://my-wiki:docs/workflow-experience/binding-of-isaac-wiki-crawl.md`
- `additional_context_refs`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`（BOI 站点策略，本次需要回填数据修正）
  - `scripts/mediawiki-api-extract/strategies/discovery.py`（`AllPagesDiscoveryStrategy.fetch_list_pages` 异常处理）
  - `scripts/mediawiki-api-extract/strategies/acquisition.py`（`fetch_page_content` 异常处理）
  - `scripts/mediawiki-api-extract/_strategies_legacy.py`（遗留策略类异常处理）
  - `scripts/mediawiki-api-extract/pipeline/phase_a.py`（`run_phase_a` 的 `fetch_list_pages` 调用点）
  - `scripts/mediawiki-api-extract/pipeline/phase_0.py`（`run_phase_0` 分类排除过滤点）
  - `scripts/mediawiki-api-extract/cli.py`（`--exclude-category` 参数新增点）
  - `scripts/mediawiki-api-extract/pipeline/orchestrate.py`（排除合并逻辑）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `repo://my-wiki:docs/workflow-experience/binding-of-isaac-wiki-crawl.md`（更新爬取状态、已修复问题、分类排除能力说明）
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`（修正 taxonomy.list_pages、新增 api.homepage.exclude_categories）
- `writeback_owner`: chrome-agent
- `writeback_timing`: 验证通过后执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（5 个 spec）
- [x] 已确认项目页引用（1 个 project page + 1 个 strategy file）
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
