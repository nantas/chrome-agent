# Specification Delta

## Capability 对齐（已确认）

- Capability: `mw-category-aliases`
- 来源: `proposal.md` — New Capability
- 变更类型: `new`
- 用户确认摘要: handoff S-1 修复方案确认——策略侧增加 MW category 别名映射字段

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: mw-category-aliases-field
The strategy schema SHALL support an optional `mw_category_aliases` field on each entry in `api.homepage.categories`, allowing a single homepage category to map to multiple MediaWiki category tag names.

#### Scenario: alias-based-mw-category-match
- **WHEN** a strategy entry defines `{name: "Items", dir: "items", mw_category_aliases: ["Collectibles", "Activated Collectibles"]}`
- **AND** a page's MW category tags include `"Collectibles"`
- **THEN** the page_assigner SHALL match `"Collectibles"` to the `"Items"` homepage category
- **AND** assign the page to `target_directory: "items"`

#### Scenario: no-aliases-backward-compat
- **WHEN** a strategy entry defines `{name: "Items", dir: "items"}` without `mw_category_aliases`
- **THEN** the page_assigner SHALL behave exactly as before (match only `"Items"` in MW categories)

### Requirement: alias-priority-resolution
When both the homepage category `name` and one of its `mw_category_aliases` match a page's MW categories, the system SHALL treat them as equivalent matches for that category.

#### Scenario: name-and-alias-both-match
- **WHEN** a page has MW categories `["Items", "Collectibles"]`
- **AND** the homepage category `{name: "Items", mw_category_aliases: ["Collectibles"]}` exists
- **THEN** the page SHALL be assigned to the `"Items"` category directory (no duplicate assignment)

### Requirement: alias-usage-in-priority-chain
`mw_category_aliases` SHALL be respected in the `assignment_priority` ordering. When a page matches an alias of a higher-priority category, it SHALL be assigned to that category even if it also matches the name of a lower-priority category.

#### Scenario: alias-priority-overrides-lower-name-match
- **WHEN** `assignment_priority` is `["Items", "Trinkets"]`
- **AND** the `"Items"` category has `mw_category_aliases: ["Collectibles"]`
- **AND** a page has MW categories `["Collectibles", "Trinkets"]`
- **THEN** the page SHALL be assigned to `"Items"` directory (priority order)

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
