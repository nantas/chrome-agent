# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: repo://orbitos (`openspec/specs/orbitos-spec-standard-v1/spec.md`)
- `project_page_ref`:
  - `chrome-agent` 仓库：`AGENTS.md`（治理约束目的地）
  - `chrome-agent` 仓库：`scripts/mediawiki-api-extract/pipeline/orchestrate.py`（`_STRATEGY_REGISTRY` 权威来源）
  - `chrome-agent` 仓库：`sites/templates/registry.json` 及 `sites/templates/*.yaml`（模板权威来源）
  - `chrome-agent` 仓库：`scripts/explore/strategy_scaffold_generator.py`（bootstrap-strategy 输出）
  - `chrome-agent` 仓库：`sites/strategies/neonabyss.fandom.com/strategy.md`（暴露设计缺口的实例）
  - `chrome-agent` 仓库：`sites/strategies/slaythespire.wiki.gg/strategy.md`（现有 wiki.gg 策略实例）
- `additional_context_refs`:
  - `chrome-agent` 仓库：`docs/plans/neonabyss-crawl-postmortem.md`（问题清单与根因分析）
  - `chrome-agent` 仓库：`openspec/specs/agents-governance/spec.md`（AGENTS.md 治理规范真源）

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
- 策略 schema 权威来源：`scripts/mediawiki-api-extract/pipeline/orchestrate.py` 中的 `_STRATEGY_REGISTRY`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md`：新增 Pipeline Strategy Schema 治理章节
  - `scripts/mediawiki-api-extract/pipeline/orchestrate.py`：如 registry 结构变更则同步更新
  - `sites/templates/`：如模板增加 platform_variant 细分则同步更新
  - `sites/strategies/`：如策略文件因新治理规则需要调整
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 变更验证完成后回写

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- AGENTS.md 治理约束直接写入，不经过 spec 代理
- platform_variant 的行为规范走 spec 路径

## 待确认项

- [x] 已确认标准页引用 — Orbitos Spec Standard v0.3
- [x] 已确认项目页引用 — 仓库内 AGENTS.md + pipeline + templates + strategies
- [x] 已确认回写目标与权限 — 仓库内文件
- [ ] 已确认异常处理与冲突策略 — platform_variant 的默认降级策略待 design 中明确
