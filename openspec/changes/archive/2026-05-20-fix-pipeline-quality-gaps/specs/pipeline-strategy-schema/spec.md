# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-strategy-schema`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: `exclude_categories` 需提升到 `api` 顶层，`discovery_strategy` 与 `api.homepage` 的关系需明确

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: exclude-categories-top-level-schema

The strategy schema SHALL support `api.exclude_categories` as a top-level list field, containing category names to exclude from ALL discovery strategies (both allpages and homepage).

The legacy field `api.homepage.exclude_categories` SHALL be retained as an alias with identical semantics. When both are defined, values SHALL be merged (union).

#### Scenario: top-level-exclude-categories

- **WHEN** a strategy defines `api.exclude_categories: [Music, Modding, Version History]`
- **THEN** Phase A (allpages) SHALL read and apply these exclusions
- **AND** Phase 0 (homepage) SHALL read and apply these exclusions
- **AND** the field location is valid per schema

#### Scenario: legacy-homepage-exclude-categories

- **WHEN** a strategy defines `api.homepage.exclude_categories: [Music]` but NOT `api.exclude_categories`
- **THEN** the pipeline SHALL read from the legacy location as fallback
- **AND** behavior SHALL be identical to top-level definition

#### Scenario: merged-exclusions

- **WHEN** a strategy defines both `api.exclude_categories: [Music]` and `api.homepage.exclude_categories: [Modding]`
- **THEN** the effective exclusion list SHALL be `[Music, Modding]`
- **AND** the merge SHALL preserve deduplication

### Requirement: discovery-strategy-and-homepage-relationship

The strategy schema SHALL clarify the relationship between `api.content_profile.discovery_strategy` and `api.homepage`.

When `api.homepage` is defined:
- `api.content_profile.discovery_strategy` SHALL be treated as the explicit override for `--discovery auto`
- If `discovery_strategy` is `"allpages"` but `api.homepage` exists, the auto-detection SHALL still prefer homepage (homepage config presence takes precedence)
- If the user explicitly sets `--discovery allpages`, `api.homepage` SHALL be ignored for discovery

When `api.homepage` is NOT defined:
- `api.content_profile.discovery_strategy` SHALL control the discovery strategy as before

#### Scenario: homepage-config-takes-precedence

- **WHEN** strategy has both `api.homepage` and `api.content_profile.discovery_strategy: "allpages"`
- **AND** `--discovery` is `auto` (default)
- **THEN** the pipeline SHALL use homepage discovery
- **AND** SHALL log a warning: `"api.homepage defined — using homepage discovery despite discovery_strategy: allpages. Use --discovery allpages to override."`

#### Scenario: no-homepage-follows-discovery-strategy

- **WHEN** strategy has `api.content_profile.discovery_strategy: "category_members"` but NO `api.homepage`
- **THEN** the pipeline SHALL use category_members discovery (existing behavior)
