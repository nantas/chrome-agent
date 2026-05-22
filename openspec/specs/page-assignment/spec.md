# Specification Delta

## Capability 对齐（已确认）

- Capability: `page-assignment`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: Step 2 延后多 source_categories 页面到 MW 终裁；补充缺失的 assignment_priority 条目；page_categories 新增 MW 分类映射

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

#### Scenario: attributes-members-assigned
- **WHEN** `assignment_priority` includes `"Attributes"`
- **AND** a page has `source_categories: ["Attributes"]` or MW category `"Mechanics"`
- **THEN** pages with `source_categories: ["Attributes"]` SHALL match at the `"Attributes"` priority position
- **THEN** pages with MW category `"Mechanics"` SHALL continue to match via Step 3 to `mechanics/` (existing behavior preserved)

#### Scenario: completion-marks-members-assigned
- **WHEN** `assignment_priority` includes `"Completion Marks"`
- **AND** a page has `source_categories: ["Completion Marks"]`
- **THEN** the page SHALL be assignable to `completion_marks/` via `"Completion Marks"` priority position

### Requirement: page-categories-mapping-gaps
The `taxonomy.page_categories` mapping SHALL cover the following known MW category gaps for the BOI strategy:

| MW Category | Target Directory | Mechanism |
|------------|-----------------|-----------|
| `Runes` | `cards` | page_categories: `Runes → Cards` resolves via top segment `Cards` |
| `Special cards` | `cards` | page_categories: `Special cards → Cards` resolves via top segment `Cards` |
| `Mini-bosses` | `bosses` | page_categories: `Mini-bosses → Bosses` resolves via top segment `Bosses` |
| `Item pools` | `items` | page_categories: `Item pools → Items` resolves via top segment `Items` |

#### Scenario: runes-mapped-to-cards
- **WHEN** a page has MW categories containing `"Runes"`
- **AND** `page_categories` maps `"Runes" → "Cards"`
- **AND** `"Cards"` top segment resolves to category `"Cards"` with `dir: "cards"`
- **THEN** Step 3 fallback SHALL assign the page to `target_directory: "cards"`

#### Scenario: special-cards-mapped-to-cards
- **WHEN** a page has MW categories containing `"Special cards"`
- **AND** `page_categories` maps `"Special cards" → "Cards"`
- **THEN** Step 3 fallback SHALL assign to `target_directory: "cards"`

#### Scenario: mini-bosses-mapped-to-bosses
- **WHEN** a page has MW categories containing `"Mini-bosses"`
- **AND** `page_categories` maps `"Mini-bosses" → "Bosses"`
- **THEN** Step 3 fallback SHALL assign to `target_directory: "bosses"`

#### Scenario: item-pools-mapped-to-items
- **WHEN** a page has MW categories containing `"Item pools"`
- **AND** `page_categories` maps `"Item pools" → "Items"`
- **THEN** Step 3 fallback SHALL assign to `target_directory: "items"`

## ADDED Requirements

### Requirement: source-category-fallback-after-mw
After Step 3 (MW category matching) completes and before Step 4 (default to misc), the system SHALL perform a fallback assignment step (Step 3.5) for pages that remain unassigned. This step SHALL use first-match-wins on `source_categories` against `assignment_priority` — the same priority order used in Step 2, but without the exact-1-match restriction. This ensures that pages with multiple source_categories matches but no MW categories are still assigned to a meaningful directory rather than misc.

#### Scenario: fallback-assigned-with-first-match-wins
- **WHEN** a page remains `assignment_method=None` after Step 3
- **AND** the page has `source_categories: ["Items", "Trinkets"]`
- **AND** `assignment_priority` begins with `["Items", "Bosses", ...]`
- **THEN** the page SHALL be assigned to `target_directory: "items"` with `assignment_method: "source_category_fallback"`
- **THEN** `assigned_category` SHALL be `"Items"` (first matching priority)

#### Scenario: fallback-skipped-for-already-assigned
- **WHEN** a page was assigned by Step 2 (single match) with `assignment_method: "source_category_match"`
- **AND** the page has `assignment_method` not `None` at this point
- **THEN** Step 3.5 SHALL NOT reassign the page

#### Scenario: fallback-skipped-for-mw-match
- **WHEN** a page was assigned by Step 3 with `assignment_method: "mw_category_match"`
- **AND** MW categories correctly identified the category (e.g., "Stages" alias → "Chapters")
- **THEN** Step 3.5 SHALL NOT override the MW match

#### Scenario: fallback-uses-priority-ordering
- **WHEN** a page has `source_categories: ["Trinkets", "Items"]` (unordered)
- **AND** `assignment_priority` has `"Items"` before `"Trinkets"`
- **THEN** the page SHALL be assigned to `"Items"` (first in priority order, not first in source_categories list)

#### Scenario: no-fallback-match
- **WHEN** a page remains unassigned after Step 3
- **AND** none of the page's `source_categories` appear in `assignment_priority`
- **THEN** the page SHALL remain unassigned
- **THEN** Step 4 SHALL assign to `"misc"` with `assignment_method: "default"` (unchanged behavior)

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
