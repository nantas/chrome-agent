# Specification Delta

## Capability 对齐（已确认）

- Capability: `docs-strategy-schema-diagrams`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 为策略 schema 参考文档增加 3 个结构化视觉元素

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: strategy-context-diagram

The document `docs/architecture/03-strategy-schema.md` SHALL include an ASCII diagram showing the strategy file's position within the chrome-agent system architecture.

The diagram SHALL illustrate:
- Strategy file (`sites/strategies/<domain>/strategy.md`) as a YAML frontmatter file
- The pipeline that consumes it (strategy → orchestrator → _STRATEGY_REGISTRY → build_pipeline())
- The explore path that generates it (deep discovery → scaffold → freeze)
- The extraction engine that reads extraction rules from it

#### Scenario: context-diagram-readability

- **WHEN** a new contributor reads `03-strategy-schema.md`
- **THEN** they SHALL understand where strategy files fit in the system within the first 50 lines
- **AND** the diagram SHALL appear in the "概述" section

### Requirement: strategy-field-hierarchy-tree

The document `docs/architecture/03-strategy-schema.md` SHALL include an ASCII tree diagram showing the hierarchical nesting of all YAML keys in a strategy file.

The tree SHALL distinguish:
- Required vs optional fields (marked with ✅/❌)
- Nested object relationships (e.g., `api` → `content_profile` → `discovery_strategy`)
- The routing from `content_profile` values to `_STRATEGY_REGISTRY` dimension → strategy class instantiation

#### Scenario: field-tree-navigation

- **WHEN** a reader is configuring a strategy file
- **THEN** they SHALL be able to visually trace any YAML key to its position in the hierarchy
- **AND** they SHALL see which fields are required

### Requirement: content-profile-routing-diagram

The document `docs/architecture/03-strategy-schema.md` SHALL include an ASCII diagram showing how `content_profile` field values route to pipeline strategy classes via `_STRATEGY_REGISTRY`.

The diagram SHALL show:
- 5 content_profile dimensions (discovery_strategy, content_acquisition, link_resolver, template_processor, list_page_assembler)
- Each dimension's registerable strategy IDs
- The mapping from YAML value → registry key → Python class

#### Scenario: routing-diagram-readability

- **WHEN** a developer needs to add a new strategy implementation
- **THEN** they SHALL understand which registry dimension to register in
- **AND** they SHALL see the existing strategy IDs for each dimension
