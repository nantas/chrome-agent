# Specification Delta

## Capability 对齐（已确认）

- Capability: `page-assignment`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: Step 2 exact-1-match 过分严格——71 页匹配 2+ source_categories 但无 MW 类别，最终落入 misc。新增 Step 3.5 回退，用 first-match-wins 处理这些页面。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

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

## MODIFIED Requirements

_None — existing Step 2 (exact-1-match) and Step 3 (MW matching) behavior unchanged._

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
