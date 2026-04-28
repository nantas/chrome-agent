# Specification Delta

## Capability 对齐（已确认）

- Capability: `master-plan`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——产出总体规划文档，覆盖项目目标、能力全景图、阶段划分与边界，作为后续各 Phase change 的引用锚点

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源

## ADDED Requirements

### Requirement: Master planning document

The system SHALL produce a master planning document at `docs/governance-and-capability-plan.md` that defines the full project landscape without diving into per-capability implementation details.

#### Scenario: Document structure

- **WHEN** the document is generated
- **THEN** it SHALL contain the following sections:
  - 项目目标与服务身份声明（仓库作为"跨仓库网页抓取服务"）
  - 当前状态摘要（已验证的能力、现有结构）
  - 能力全景图（对外: explore/fetch/crawl；对内: site-strategy/anti-crawl-strategy/engine-registry/output-lifecycle）
  - 阶段划分与交付边界（Phase 1–5 描述+各阶段输出物）
  - 依赖关系（哪个阶段前置哪个）
  - 技术栈与工具链说明（当前引擎 + 扩展方向）
  - 治理约束（repo:// 语义、binding 引用、决策记录索引）

#### Scenario: Phase boundary definition

- **WHEN** each phase is described
- **THEN** the phase entry SHALL include: phase name, scope, deliverables, required specs/contracts to create, and a clear exclusion boundary

### Requirement: README rewrite

The system SHALL rewrite `README.md` to reflect the project's "cross-repo web scraping service" identity, replace the old "browser workstation" language, and serve as the repository's public-facing entry point.

#### Scenario: README content

- **WHEN** the README is rewritten
- **THEN** it SHALL include: project identity, capability overview, directory structure, quick start, and a reference to the master planning document for the full roadmap
- **THEN** it SHALL NOT contain operational how-to details (these belong in AGENTS.md and playbooks)
