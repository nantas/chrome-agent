# Specification Delta

## Capability 对齐（已确认）

- Capability: `page-assignment`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: BOI 策略配置补全——`assignment_priority` 补充缺失条目；`taxonomy.page_categories` 新增 MW 分类 → 目录映射

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

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

_None_

## REMOVED Requirements

_None_
