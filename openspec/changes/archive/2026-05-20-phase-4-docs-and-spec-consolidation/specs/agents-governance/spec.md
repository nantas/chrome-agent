# Specification Delta

## Capability 对齐（已确认）

- Capability: `agents-governance`
- 来源: `proposal.md` Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: LSP 真源核查发现 6 处过时申明需修复；AGENTS.md 瘦身将架构/开发内容迁移至 docs/architecture/；STRATEGY_REGISTRY 位置路径更新

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: AGENTS.md 结构与强制内容

The system SHALL maintain AGENTS.md as a pure governance document with the following mandatory sections, ordered as specified:

1. **Critical Rule**: LSP code intelligence usage mandate (preserved from §0)
2. **Service Identity**: 声明仓库为"跨仓库网页抓取服务（cross-repo web scraping service）"，定义核心设计原则（Scrapling-first、workflow-driven、read-only by default、证据驱动）
3. **Capability Framework**: 列出仓库对外能力（explore / fetch / crawl / scrape）和对内能力（site-strategy / anti-crawl-strategy / engine-registry / output-lifecycle），引用总体规划文档
4. **Governance Rules**: 定义工作流路由规则、Confirmation Gates、爬取问题诊断流程、Handoff 工作流、认证访问边界、报告产出规范
5. **Directory Governance**: 定义每个顶级目录的用途和内容约束（精简版，完整结构见 `docs/architecture/01-overview.md`）
6. **Decision Record Governance**: 定义决策记录格式
7. **Spec and Change Governance**: 定义 openspec 管理规则
8. **Strategy Library Governance**: 策略库治理约束（不含 Pipeline Strategy Schema ID 清单，详见 `docs/architecture/03-strategy-schema.md`）
9. **Engine Extension Governance**: 引擎扩展治理约束（不含引擎概览表，详见 `docs/architecture/06-engine-selection.md`）
10. **Reference Index**: 仓库内关键文档索引（增加 `docs/architecture/` 条目）

AGENTS.md SHALL NOT contain architecture design content, engine selection decision trees, development conventions, strategy ID lists, or engine registry tables. Such content SHALL reside in `docs/architecture/`.

After the architecture content migration, AGENTS.md SHALL be ≤3KB in size (down from ~10KB).

#### Scenario: AGENTS.md content separation

- **WHEN** AGENTS.md is read by an agent or operator
- **THEN** the document provides governance-level context (identity, rules, policies) without architecture design details
- **AND** architecture design details are accessible via `docs/architecture/` with explicit "→ 详见 docs/architecture/<file>.md" links at each section boundary

#### Scenario: Mandatory sections present

- **WHEN** AGENTS.md is validated against this spec
- **THEN** all ten mandatory sections SHALL be present in the specified order
- **AND** no section SHALL contain architecture design content, engine tables, or strategy ID lists

### Requirement: 目录结构治理

The system SHALL define the governance rules for each top-level directory in AGENTS.md, with full structural detail delegated to `docs/architecture/01-overview.md`.

#### Scenario: Directory purpose definition

- **WHEN** the directory governance section is read
- **THEN** each top-level directory SHALL have a defined purpose and content constraint
- **AND** the section SHALL include `scripts/lib/` as a top-level concern (shared Python library)
- **AND** it SHALL include `docs/architecture/` as the architecture documentation directory
- **AND** it SHALL reference `docs/architecture/01-overview.md` for the complete directory tree

### Requirement: Pipeline Strategy Schema 治理章节

The system SHALL include a Pipeline Strategy Schema 治理 subsection within AGENTS.md §8 (Strategy Library Governance), containing only governance constraints. Strategy ID lists and platform_variant tables SHALL be delegated to `docs/architecture/03-strategy-schema.md`.

该章节 SHALL 包含以下内容：

1. **权威来源声明**：声明 `_STRATEGY_REGISTRY`（位于 `scripts/pipeline/pipeline/registry.py`）为策略 ID 的唯一权威来源
2. **策略文件约束**：`content_profile` 字段只能引用已注册 ID；Pipeline 启动时 hard-fail 校验
3. **扩展协议**：实现 → 注册 → 引用的严格顺序
4. **Registry 变更约束**：删除/重命名 ID 前必须反向检查
5. **引用链接**：`→ 合法 ID 清单及 platform_variant 详见 docs/architecture/03-strategy-schema.md`

#### Scenario: 章节位置与内容

- **WHEN** 用户或 agent 阅读 AGENTS.md
- **THEN** Pipeline Strategy Schema 治理章节 SHALL 位于策略库治理之后
- **AND** SHALL 包含权威来源、约束、扩展协议和 Registry 变更约束
- **AND** SHALL 明确引用 `scripts/pipeline/pipeline/registry.py` 作为 `_STRATEGY_REGISTRY` 的权威位置
- **AND** SHALL 将 ID 清单替换为 `docs/architecture/03-strategy-schema.md` 的链接

### Requirement: AGENTS.md LSP Audit and Repair

Before slimming AGENTS.md, the system SHALL perform an LSP-based audit of all code-path claims in AGENTS.md and repair any stale or incorrect claims.

The audit SHALL verify and repair:

1. **Engine registry table**:补全为 10 引擎（增加 `mediawiki-api` rank 0, `obscura-serve-pool` rank 3）; 修正 `scrapling-fetch` rank 从 3→4
2. **Python 3.9 compatibility**: `sample_converter.py` 已使用 `from typing import Optional`（`dict | None` 问题已在 Change 2 修复）
3. **Test module path**: Python 测试路径从 `orchestrate.py` 修正为 `discovery_summary.py`
4. **Directory structure**: 补充 `scripts/lib/` 条目
5. **Phase naming in pipeline description**: `Phase A → Phase Fetch → Phase Convert → Phase C` 更新为 `homepage/allpages discovery → fetch → convert → assembly`
6. **Node.js test count**: 验证仍为 9（不需要修改）

#### Scenario: audit-completeness

- **WHEN** the LSP audit is performed
- **THEN** all 6 repair items SHALL be applied to AGENTS.md
- **AND** each repair SHALL be verifiable against actual source code via LSP symbols/hover

### Requirement: AGENTS.md Architecture Content Migration

Architecture and development content currently in AGENTS.md SHALL be migrated to the corresponding `docs/architecture/` documents, with each migrated section replaced by a governance-level summary and an explicit link.

Migration mapping:
- §3 引擎选择策略 → `docs/architecture/06-engine-selection.md`
- §3 Deep Discovery 8-step → `docs/architecture/07-explore-workflow.md`
- §3 API管线 Phase 流程 → `docs/architecture/02-pipeline-flow.md`
- §3 样本转换 CLI → `docs/architecture/07-explore-workflow.md`
- §4 完整目录结构 → `docs/architecture/01-overview.md`
- §6 仓库结构表 / 测试 / 约定 / LSP模式 / 版本检查 / 常见陷阱 → `docs/architecture/08-tech-stack.md`
- §8 策略注册 ID 清单 + platform_variant → `docs/architecture/03-strategy-schema.md`
- §9 已注册引擎概览表 + 引擎版本治理字段获取方法 → `docs/architecture/06-engine-selection.md`

#### Scenario: migration-completeness

- **WHEN** migration is complete
- **THEN** AGENTS.md SHALL be ≤3KB
- **AND** each migrated section SHALL be replaced with `→ 详见 docs/architecture/<file>.md` format link
- **AND** no orphaned architecture detail SHALL remain in AGENTS.md

### Requirement: Reference Index Update

The Reference Index in AGENTS.md SHALL include entries for `docs/architecture/` documents.

#### Scenario: reference-index-complete

- **WHEN** AGENTS.md or README is updated
- **THEN** the reference index SHALL list `docs/architecture/` as "核心架构文档" with entry point `01-overview.md`
- **AND** key individual documents (`02-pipeline-flow.md`, `03-strategy-schema.md`, `06-engine-selection.md`) SHALL be individually indexed
