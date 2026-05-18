# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/global-workflow-skill/spec.md` — SKILL.md 行为规范真源，Crawl Confirmation Gate 作为新的 Agent Gate 添加
  - `openspec/specs/strategy-guided-crawl/spec.md` — crawl 命令行为规范真源，--discovery-only / --from-manifest / --yes 参数添加
  - `openspec/specs/pipeline-cli-entry/spec.md` — Python 管线 CLI 参数规范真源，--phase discover 值添加
  - `openspec/specs/mediawiki-api-extraction-pipeline/spec.md` — 管线编排行为真源，discovery-only 执行路径
  - `openspec/specs/homepage-driven-discovery/spec.md` — Phase 0 首页发现行为真源
  - `openspec/specs/explore-skill-gates/spec.md` — 现有 Agent Gate 模式参考（不修改）
- `project_page_ref`:
  - `AGENTS.md` — 治理文档，需新增 Crawl Confirmation Gate 治理规则段
  - `~/.agents/skills/chrome-agent/SKILL.md` — 全局 workflow skill，需新增 Crawl Confirmation Gate 章节
  - `scripts/chrome-agent-cli.mjs` — CLI 主入口，新增 --discovery-only / --from-manifest / --yes 参数
  - `scripts/mediawiki-api-extract/cli.py` — Python 管线 CLI 入口，--phase 新增 discover 值
  - `scripts/mediawiki-api-extract/pipeline/orchestrate.py` — 管线编排，新增 discovery-only 分支与 discovery_summary 生成
- `additional_context_refs`:
  - `openspec/changes/fix-pipeline-quality-gaps/` — --discovery 参数正交拆分上下文（已落地，本 change 基于其上构建）
  - `openspec/changes/archive/2026-05-16-explore-workflow-hardening/` — Explore→Crawl Confirmation Gate 原始模式参考

## Source of Truth

- 行为规范真源：本 change 的 `specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；SKILL.md 和 AGENTS.md 中的 Gate 描述从 spec 派生，以 spec 为准

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` — 新增「Crawl Confirmation Gate」治理规则段，引用 crawl-confirmation-gate spec
  - `~/.agents/skills/chrome-agent/SKILL.md` — 新增「Crawl Confirmation Gate」章节，定义 discovery → tree → ask_user → proceed 工作流
  - `skills/chrome-agent/SKILL.md` — 仓库内 skill 源文件同步更新
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- CLI 参数变更以 `pipeline-cli-entry` 和 `strategy-guided-crawl` spec 为权威格式
- SKILL.md 中的 Gate 流程描述从 `crawl-confirmation-gate` spec 派生

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
