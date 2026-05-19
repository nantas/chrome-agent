# AGENTS.md — chrome-agent 治理文档

## 0. Critical Rule

优先使用 `lsp` 工具（symbols / definition / references）而非 `grep` + `read`。

→ 决策表 & 模式详见 `docs/architecture/08-tech-stack.md`

## 1. Service Identity

**chrome-agent** 是跨仓库网页抓取服务。核心原则：Scrapling-first、workflow-driven、read-only by default、证据驱动。

范围：网页内容获取、前端调试、经验积累。范围外（v1）：凭据管理、自动化框架。

## 2. Capability Framework

| 对外 | 说明 | 对内 | 状态 |
|------|------|------|------|
| explore | 分析页面结构与反爬 | site-strategy | 未结构化 |
| fetch | 获取页面内容 | anti-crawl-strategy | 未结构化 |
| crawl | 策略引导遍历 | engine-registry | 已规范 |
| scrape | 策略无关爬取 | output-lifecycle | 未实现 |

→ 全景详见 [总体规划](docs/governance-and-capability-plan.md)

## 3. Governance Rules

**路由：** Content Retrieval（默认）vs Platform Analysis（深度路径）。

→ Deep Discovery 详见 `docs/architecture/07-explore-workflow.md`
→ 引擎选择 & fallback 详见 `docs/architecture/06-engine-selection.md`
→ API 管线流程详见 `docs/architecture/02-pipeline-flow.md`

**Crawl Gate:** Discovery-only → ask_user 确认 → Extraction（`--from-manifest`）。
**Explore→Crawl Gate:** partial_success 需确认；failure 不准伪造策略。
**爬取诊断：** P-line/S-line/W-line 三线归因。
**Handoff：** 内部失败 → `outputs/handoffs/<tag>/handoff.md` → Gate 停止工作流。
**认证：** 需批准、只读、Scrapling-first、会话失败切 chrome-cdp。
**报告：** 默认不产出；深度路径完整产出。

## 4. Directory Governance

→ 完整结构详见 `docs/architecture/01-overview.md`

`openspec/`（规范变更）→ `docs/`（架构/决策）→ `scripts/`（lib/, pipeline/, explore/）→ `sites/`（策略）→ `configs/`（配置）→ `skills/`（workflow）→ `outputs/`（产出）。

## 5. Decision Record Governance

`docs/decisions/` 内。命名 `YYYY-MM-DD-topic.md`。每份含 Context / Decision / Consequences。

## 6. Spec & Change Governance

Orbitos Spec Standard v0.3。真源：`openspec/specs/`。变更：`openspec/changes/`。

## 7. Strategy Library Governance

`strategy.md` frontmatter 为权威来源。新增策略需更新 `registry.json`。

→ Pipeline Strategy ID 清单 & `platform_variant` 详见 `docs/architecture/03-strategy-schema.md`

`_STRATEGY_REGISTRY`（`registry.py`）为 ID 唯一权威来源。扩展：实现→注册→引用。

## 8. Engine Extension Governance

新引擎通过 openspec change 接入。`configs/engine-versions.json` 为版本真源。升级须同步哈希/大小字段。

→ 引擎概览详见 `docs/architecture/06-engine-selection.md`

## 9. Reference Index

| 文档 | 位置 | 用途 |
|------|------|------|
| 核心架构文档 | `docs/architecture/` | 总览、管线、Schema、引擎选择 |
| 总体规划 | `docs/governance-and-capability-plan.md` | 路线图 |
| 决策记录 | `docs/decisions/` | 架构决策 |
| 操作手册 | `docs/playbooks/` | 抓取/fallback/认证 |
| 能力规范 | `openspec/specs/` | 行为真源 |
| KI Lifecycle | `scripts/explore/ki_lifecycle.py` | Issue 分类与修复 |
