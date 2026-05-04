# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy-schema`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户已通过对话确认，在站点策略 schema 中新增可选 `backend` 字段，用于标记后端家族关系

## 规范真源声明

- 本文件是 `site-strategy-schema` 在本次 change 中的行为规范真源增量
- 完整规范仍需参考 `openspec/specs/site-strategy-schema/spec.md`
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: YAML frontmatter 必填与可选字段

The system SHALL define a mandatory and optional YAML frontmatter schema for all site strategy files.

Each `strategy.md` SHALL include the following **required** fields in its YAML frontmatter:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `domain` | string | yes | Primary domain (e.g., `fanbox.cc`, `mp.weixin.qq.com`) |
| `description` | string | yes | One-sentence summary of scraping scope |
| `protection_level` | enum | yes | `low`, `medium`, `high`, `authenticated`, or `variable` |
| `anti_crawl_refs` | string[] | yes | References to `anti-crawl/` strategy IDs; empty array if none |
| `engine_preference` | object | no | Optional engine preference for this site; contains `preferred` (string) and optional `reason` (string) |
| `structure` | object | yes | Page hierarchy and connectivity (see Structure requirement) |
| `extraction` | object | no | Globally useful selectors, image handling, and cleanup rules |

Each `strategy.md` MAY include the following **optional** field:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `backend` | string | no | Backend family identifier from `configs/backend-signatures.json`; used for cross-site strategy reuse and backend detection validation |

#### Scenario: 新增 backend 字段

- **WHEN** a site strategy is created for a domain that shares a known backend platform (e.g., Weird Gloop MediaWiki)
- **THEN** the `backend` field MAY be populated with the matching `id` from `configs/backend-signatures.json`
- **AND** when present, `backend` SHALL be treated as an advisory tag, not a runtime strategy matching key

#### Scenario: 无 backend 字段

- **WHEN** a site strategy does not specify `backend`
- **THEN** the strategy SHALL be considered fully valid and complete
- **AND** the absence of `backend` SHALL NOT trigger any validation error
- **AND** the behavior of all downstream consumers SHALL remain unchanged

#### Scenario: backend 字段值无效

- **WHEN** a site strategy specifies a `backend` value that does not exist in `configs/backend-signatures.json`
- **THEN** the system SHALL emit a warning but SHALL NOT treat it as a blocking error
- **AND** the strategy SHALL still be accepted for crawl eligibility

#### Scenario: 必填字段完整性

- **WHEN** a site strategy file is created
- **THEN** it SHALL contain all mandatory frontmatter fields (`domain`, `description`, `protection_level`, `anti_crawl_refs`, `structure`)
- **AND** missing any required field SHALL be treated as an incomplete strategy
- **AND** `backend` being absent SHALL NOT cause the strategy to be considered incomplete

## ADDED Requirements

### Requirement: Registry.json 新增 backend 索引字段

The system SHALL extend `sites/strategies/registry.json` entries to optionally include a `backend` field.

#### Scenario: Registry 条目包含 backend

- **WHEN** a strategy file has a `backend` field in its YAML frontmatter
- **THEN** the corresponding `registry.json` entry SHOULD include `backend` with the same value
- **AND** `registry.json` entries without `backend` SHALL remain valid

#### Scenario: 通过 backend 查询策略

- **WHEN** an agent or tool queries `registry.json` for all strategies sharing a specific backend
- **THEN** it SHALL be able to filter entries by the `backend` field
- **AND** entries without `backend` SHALL be excluded from such filtered results
