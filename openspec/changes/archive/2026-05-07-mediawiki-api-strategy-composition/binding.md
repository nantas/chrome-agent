# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `repo://chrome-agent/openspec/specs/mediawiki-api-extraction/spec.md` — MODIFIED：新增策略接口契约、capabilities 词汇表、namespace 场景、策略挂载点描述
  - `repo://chrome-agent/openspec/specs/mediawiki-site-strategy/spec.md` — MODIFIED：新增 `api.content_profile` schema
  - `repo://chrome-agent/openspec/specs/agents-governance/spec.md` — 本次引用，作为治理规则对齐参考
- `project_page_ref`:
  - `repo://my-wiki/docs/design/chrome-agent-mediawiki-extraction-improvement-plan.md` — 本次变更的设计来源文档（Change 1 方案定义）
  - `repo://my-wiki/docs/workflow-experience/chrome-agent-sts2-crawl-postmortem.md` — 问题背景参考，Change 1 只做架构重构不修复问题
- `additional_context_refs`:
  - `repo://chrome-agent/sites/strategies/balatrowiki.org/strategy.md` — 本次回归验证的策略文件
  - `repo://chrome-agent/sites/strategies/slaythespire.wiki.gg/strategy.md` — 对比站点策略（Change 1 不改，Change 2 目标）
  - `repo://chrome-agent/scripts/mediawiki-api-extract` — 本次重构目标文件（1292 行单体脚本）
  - `repo://chrome-agent/openspec/specs/mediawiki-extraction-patterns/spec.md` — 引用作为清理规则参考

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（本次 MODIFIED：`mediawiki-api-extraction`, `mediawiki-site-strategy`）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；改善方案文档提供设计方案但不定义行为规范

## 回写目标

- `writeback_targets`:
  1. `openspec/specs/mediawiki-api-extraction/spec.md` — MODIFIED：追加策略接口契约、capabilities 词汇表、namespace 场景、管线流程图
  2. `openspec/specs/mediawiki-site-strategy/spec.md` — MODIFIED：追加 `api.content_profile` schema
  3. `scripts/mediawiki-api-extract/` — RESTRUCTURED：单文件 → 多文件包（client.py, strategies.py, phase_a/b/c.py, pipeline.py, `__main__.py`）
  4. `sites/strategies/balatrowiki.org/strategy.md` — MODIFIED：可选追加 `api.content_profile` 声明
  5. `AGENTS.md` — MODIFIED：管线架构更新（策略组合模式说明）
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 实现阶段立即写入仓库；AGENTS.md 在变更归档时同步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 本次变更不新增行为，只重构现有逻辑为策略组合架构
- 默认行为必须与重构前完全一致（balatro 回归验证）
- 总管线改善方案（`chrome-agent-mediawiki-extraction-improvement-plan.md`）是 Change 1 和 Change 2 的宏观规划参考，不替代当前 change 的内置 artifact

## 待确认项

- [x] 已确认标准页引用（mediawiki-api-extraction, mediawiki-site-strategy, agents-governance）
- [x] 已确认项目页引用（改善方案文档 + postmortem）
- [x] 已确认回写目标与权限（全部在 chrome-agent 仓库内，无需外部权限）
- [x] 已确认异常处理与冲突策略（行为 spec 为真源；balatro 回归验证；不做行为变更）
