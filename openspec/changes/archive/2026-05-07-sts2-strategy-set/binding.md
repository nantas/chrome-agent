# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `repo://chrome-agent/openspec/specs/mediawiki-api-extraction/spec.md` — MODIFIED：追加新策略 ID 到可用 ID 表格、新增 scenario（动态内容检测、跨 namespace 链接、infobox 图片获取）
  - `repo://chrome-agent/openspec/specs/mediawiki-site-strategy/spec.md` — MODIFIED：更新 `content_profile` 可用 ID 表格，追加 StS2 策略集 ID
  - `repo://chrome-agent/openspec/specs/agents-governance/spec.md` — 本次引用，作为治理规则对齐参考
- `project_page_ref`:
  - `repo://my-wiki/docs/design/chrome-agent-mediawiki-extraction-improvement-plan.md` — 本次变更的设计来源文档（Change 2 方案定义）
  - `repo://my-wiki/docs/workflow-experience/chrome-agent-sts2-crawl-postmortem.md` — 问题背景参考
- `additional_context_refs`:
  - `repo://chrome-agent/openspec/changes/archive/2026-05-07-mediawiki-api-strategy-composition/` — Change 1 已归档工件，提供策略接口冻结基线
  - `repo://chrome-agent/scripts/mediawiki-api-extract/` — 本次变更的实现目标（策略组合包）
  - `repo://chrome-agent/sites/strategies/slaythespire.wiki.gg/strategy.md` — 本次变更的策略文件目标
  - `repo://chrome-agent/sites/strategies/balatrowiki.org/strategy.md` — 对比站点策略（回归验证基线）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（本次 MODIFIED：`mediawiki-api-extraction`, `mediawiki-site-strategy`）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；改善方案文档提供设计方案但不定义行为规范

## 回写目标

- `writeback_targets`:
  1. `openspec/specs/mediawiki-api-extraction/spec.md` — MODIFIED：追加新策略 ID（`category_members`, `hybrid_wikitext_plus_rendered`, `short_name_with_cross_namespace`, `structured_with_lua_fallback`, `hybrid_frontmatter_and_rendered`）、新增 StS2-specific scenario
  2. `openspec/specs/mediawiki-site-strategy/spec.md` — MODIFIED：更新 `content_profile` 可用 ID 表格
  3. `scripts/mediawiki-api-extract/strategies.py` — MODIFIED：追加 5 个新策略实现
  4. `scripts/mediawiki-api-extract/pipeline.py` — MODIFIED：更新 `build_pipeline()` 支持新策略 ID、追加 L6 验证入口
  5. `scripts/mediawiki-api-extract/phase_a.py` — MODIFIED：支持跨 namespace 发现
  6. `scripts/mediawiki-api-extract/phase_c.py` — MODIFIED：支持 `--validate` flag、L6 验证集成
  7. `sites/strategies/slaythespire.wiki.gg/strategy.md` — MODIFIED：配置 `content_profile` 使用新策略集、扩展 `template_map`
  8. `AGENTS.md` — MODIFIED：L6 验证层说明、跨 namespace 支持说明
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 实现阶段立即写入仓库；spec 在变更归档时同步冻结

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- Change 2 依赖 Change 1 冻结的策略接口（`DiscoveryStrategy`, `ContentAcquisitionStrategy`, `LinkResolver`, `TemplateProcessor`, `ListPageAssembler`），这些接口在 Change 2 中只追加实现不修改签名
- 默认行为（balatro 路径）在 Change 2 中保持不变——新策略只在 StS2 `content_profile` 中启用
- 总管线改善方案（`chrome-agent-mediawiki-extraction-improvement-plan.md`）是 Change 1 和 Change 2 的宏观规划参考，不替代当前 change 的内置 artifact

## 待确认项

- [x] 已确认标准页引用（mediawiki-api-extraction, mediawiki-site-strategy, agents-governance）
- [x] 已确认项目页引用（改善方案文档 + postmortem）
- [x] 已确认回写目标与权限（全部在 chrome-agent 仓库内，无需外部权限）
- [x] 已确认异常处理与冲突策略（行为 spec 为真源；balatro 回归验证；默认策略不变）
