# Specification Delta

## Capability 对齐（已确认）

- Capability: `page-assignment`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: Step 2 延后多 source_categories 页面到 MW 终裁；补充缺失的 assignment_priority 条目（策略配置级）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: unique-source-category-assignment
The `_apply_source_category_assignments` step (Step 2) SHALL only immediately assign pages that match exactly ONE category name in `assignment_priority` within `source_categories`. Pages matching TWO OR MORE category names SHALL NOT be assigned in Step 2 and SHALL be deferred to Step 3 (MW category matching) for tiebreaking. Pages matching ZERO category names SHALL also be deferred to Step 3 as before.

When a page matches multiple `source_categories`, the tiebreaking SHALL NOT happen within Step 2 — the page remains unassigned and passes through to `_apply_mw_category_matching`.

#### Scenario: single-source-category-match
- **WHEN** a page has `source_categories: ["Items"]`
- **AND** `assignment_priority` begins with `["Items", "Bosses", ...]`
- **THEN** the page SHALL be assigned to `target_directory: "items"` with `assignment_method: "source_category_match"` (immediate match, single category)

#### Scenario: multiple-source-category-match-deferred
- **WHEN** a page has `source_categories: ["Bosses", "Chapters"]`
- **AND** `assignment_priority` is `["Items", "Bosses", ..., "Chapters", ...]`
- **THEN** the page SHALL NOT be assigned in Step 2 (multiple matches)
- **THEN** the page SHALL be deferred to Step 3 for MW category tiebreaking

#### Scenario: zero-source-category-match-deferred
- **WHEN** a page has `source_categories: []`
- **THEN** the page SHALL NOT be assigned in Step 2 (zero matches)
- **THEN** the page SHALL be deferred to Step 3

### Requirement: mw-category-tiebreaker-preserved
Pages deferred from Step 2 due to multiple `source_categories` matches SHALL be processed by Step 3 (`_apply_mw_category_matching`) with the same priority chain and fallback rules as pages with zero matches. No special priority or penalty.

#### Scenario: deferred-page-matched-via-mw-category
- **WHEN** a page has `source_categories: ["Bosses", "Chapters"]`
- **AND** MW categories `["Stages"]`
- **AND** `"Chapters"` has `mw_category_aliases: ["Stages"]`
- **THEN** Step 3 SHALL match via alias and assign to `target_directory: "chapters"` with `assignment_method: "mw_category_match"`

#### Scenario: deferred-page-matched-via-mw-direct
- **WHEN** a page has MW categories `["Bosses"]`
- **AND** `"Bosses"` is in `assignment_priority`
- **THEN** Step 3 SHALL match via direct name and assign to `target_directory: "bosses"` with `assignment_method: "mw_category_match"`

#### Scenario: deferred-page-falls-to-default
- **WHEN** a deferred page has no matching MW categories
- **THEN** Step 3 SHALL leave it unassigned
- **THEN** Step 4 SHALL assign to `"misc"` with `assignment_method: "default"`

### Requirement: assignment-priority-gap-fill
The strategy SHALL include ALL defined `homepage.categories` entries in `assignment_priority`. Categories outside `assignment_priority` cannot be assigned via Step 2 or Step 3 and therefore become effectively invisible to the assignment system.

For the BOI strategy specifically `Attributes` and `Completion Marks` SHALL be added to `assignment_priority`.

#### Scenario: missing-priority-gap-fixed
- **WHEN** `homepage.categories` defines `{name: "Attributes", dir: "attributes"}`
- **AND** `homepage.categories` defines `{name: "Completion Marks", dir: "completion_marks"}`
- **AND** `assignment_priority` includes `"Attributes"` and `"Completion Marks"`
- **THEN** pages with `source_categories: ["Attributes"]` or MW category `"Completion Marks"` SHALL match at the corresponding priority position

## ADDED Requirements

_None_

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
