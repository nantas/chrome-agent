# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: repo://orbitos (Orbitos Spec Standard v0.3)
- `project_page_ref`:
  - 基准测试报告: `docs/plans/2026-05-11-obscura-vs-scrapling-benchmark-report.md`
  - 交汇分析报告: `docs/plans/2026-05-11-obscura-crawl-convergence-analysis.md`
  - 整合方案设计: `docs/plans/2026-05-11-obscura-bulk-scrape-integration-design.md`
  - Obscura Preflight: `docs/playbooks/obscura-cli-preflight.md`
  - 引擎注册表: `configs/engine-registry.json`
- `additional_context_refs`:
  - Scrapling Fetchers 指南: `docs/playbooks/scrapling-fetchers.md`
  - Chrome Agent CLI 源码: `scripts/chrome-agent-cli.mjs`
  - Fallback 策略: `docs/playbooks/fallback-escalation.md`

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - 项目板/项目页 title: "Obscura Preflight Upgrade and Parallel Integration"
  - 项目页面路径 (预计): Obsidian vault `/Projects/chrome-agent/Obscura-Parallel-Integration`
- `writeback_owner`: nantas (需确认)
- `writeback_timing`: 同步时机 — Phase 2 (CLI 集成) 完成后回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用 — repo://orbitos
- [x] 已确认项目页引用 — docs/plans/ 下三份文档
- [x] 已确认回写目标与权限 — Obsidian vault path: `/Users/nantasmac/projects/obsidian-mind/20_项目/chrome-agent/chrome-agent.md`, Writeback记录: `/Users/nantasmac/projects/obsidian-mind/20_项目/chrome-agent/Writeback记录.md`
- [x] 已确认异常处理与冲突策略 — 降级到 Scrapling 串行已定义
