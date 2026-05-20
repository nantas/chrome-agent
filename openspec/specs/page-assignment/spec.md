# Specification Delta

## Capability 对齐（已确认）

- Capability: `page-assignment`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: handoff S-1/S-2 修复——扩展 source_categories 匹配 + 接入 page_categories + MW alias 支持

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: source-category-assignment
The `_apply_category_page_member_assignments` step (Step 2) SHALL be renamed to `_apply_source_category_assignments` and SHALL match pages by their `source_categories` field regardless of category type (both `list_page` and `category_page`). Assignment SHALL follow `assignment_priority` ordering.

#### Scenario: list-page-source-category-match
- **WHEN** a page has `source_categories: ["Items"]`
- **AND** `"Items"` is a `list_page` type category with `dir: "items"`
- **AND** `"Items"` appears in `assignment_priority`
- **THEN** the page SHALL be assigned to `target_directory: "items"` with `assignment_method: "source_category_match"`

#### Scenario: priority-order-for-source-categories
- **WHEN** a page has `source_categories: ["Items", "Trinkets"]`
- **AND** `assignment_priority` is `["Items", "Trinkets", ...]`
- **THEN** the page SHALL be assigned to `"Items"` directory (first matching priority wins)

#### Scenario: category-page-source-category-backward-compat
- **WHEN** a page has `source_categories: ["Objects"]`
- **AND** `"Objects"` is a `category_page` type category
- **THEN** the page SHALL still be assigned correctly (no regression from renaming the step)

### Requirement: page-categories-fallback
The page_assigner SHALL read `taxonomy.page_categories` from the strategy as an additional MW category → directory mapping source. When MW category tags don't match any `homepage.categories` name or `mw_category_aliases`, the system SHALL check `page_categories` for a mapping.

#### Scenario: page-categories-mw-fallback
- **WHEN** a page has MW category `"Stages"`
- **AND** `"Stages"` is not in `homepage.categories` names or any `mw_category_aliases`
- **AND** `taxonomy.page_categories` defines `Stages: "Chapters"`
- **AND** the homepage category `"Chapters"` has `dir: "chapters"`
- **THEN** the page SHALL be assigned to `target_directory: "chapters"`

#### Scenario: page-categories-sub-path-resolution
- **WHEN** `taxonomy.page_categories` defines `"Activated Collectibles": "Collectibles/Activated"`
- **AND** the top-level segment `"Collectibles"` maps to homepage category `"Items"` with `dir: "items"`
- **THEN** the page SHALL be assigned to `target_directory: "items"` (top-level segment resolves to homepage dir)

### Requirement: mw-category-matching-with-aliases
The `_apply_mw_category_matching` step (Step 3) SHALL check both `homepage.categories[].name` and `homepage.categories[].mw_category_aliases` when matching MW category tags. The `assignment_priority` ordering SHALL apply to the homepage category name, and aliases SHALL inherit the same priority.

#### Scenario: alias-match-in-step-3
- **WHEN** `assignment_priority` includes `"Items"`
- **AND** `"Items"` category has `mw_category_aliases: ["Collectibles"]`
- **AND** a page has MW category `"Collectibles"`
- **THEN** Step 3 SHALL match `"Collectibles"` to `"Items"` and assign `target_directory: "items"`

### Requirement: assignment-method-tracking
Each assignment step SHALL record a distinct `assignment_method` value for observability: `"manual"`, `"source_category_match"` (renamed from `"category_page_member"`), `"mw_category_match"`, and `"default"`.

#### Scenario: assignment-method-values
- **WHEN** a page is assigned via Step 2 (source category match)
- **THEN** `assignment_method` SHALL be `"source_category_match"`
- **WHEN** a page is assigned via Step 3 (MW category match including alias)
- **THEN** `assignment_method` SHALL be `"mw_category_match"`

## ADDED Requirements

_None_

## REMOVED Requirements

### Requirement: category-page-member-only
**Reason**: Step 2 previously only matched `category_page` type categories, excluding the majority of `list_page` type categories (Items, Bosses, etc.)
**Migration**: `_apply_category_page_member_assignments` renamed to `_apply_source_category_assignments`; all callers reference the new function name

## RENAMED Requirements

- FROM: `### Requirement: category-page-member-assignments`
- TO: `### Requirement: source-category-assignment`
