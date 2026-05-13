# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/agents-governance/spec.md`（AGENTS.md 治理约束的规范真源，含 Pipeline Strategy Schema 章节）
  - `openspec/specs/engine-registry/spec.md`（引擎注册索引的规范真源）
- `project_page_ref`:
  - `AGENTS.md`（治理文档，含 Pipeline Strategy Schema 治理、引擎注册概览、策略库治理章节）
  - `sites/README.md`（站点策略库使用说明）
- `additional_context_refs`:
  - `scripts/mediawiki-api-extract/pipeline/orchestrate.py`（`_STRATEGY_REGISTRY` 权威来源、`DEFAULT_STRATEGIES`、`validate_api_config`）
  - `scripts/explore/strategy_scaffold_generator.py`（scaffold 生成器，合并逻辑修改目标）
  - `scripts/explore/api_discovery.py`（API 探测，capabilities 词汇修正目标）
  - `sites/templates/*.yaml`（平台模板，content_profile 和 rate_limit 补全目标）
  - `sites/strategies/*/strategy.md`（现有站点策略，数据修复目标）
  - `sites/anti-crawl/registry.json`（反爬策略索引，neonabyss 缺失修复目标）
  - `configs/engine-registry.json`（引擎注册配置）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md`：更新 Pipeline Strategy Schema 治理章节，补充 capabilities 推导函数说明；更新引擎注册概览中 BGG 的引擎引用
  - `openspec/specs/agents-governance/spec.md`：同步 AGENTS.md 治理约束变更
  - `sites/anti-crawl/registry.json`：补充 neonabyss.fandom.com 到 rate-limit-api 的 sites 列表
  - `sites/strategies/registry.json`：同步策略文件修正后的元数据
- `writeback_owner`: 实施者（通过 tasks.md 中的具体步骤执行）
- `writeback_timing`: 所有 tasks 完成后统一回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
