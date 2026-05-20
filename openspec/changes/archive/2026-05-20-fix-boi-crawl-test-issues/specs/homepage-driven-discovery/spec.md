# Specification Delta

## Capability 对齐（已确认）

- Capability: `homepage-driven-discovery`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 修复 `_build_homepage_manifest()` 中 list page 目录分配映射错误；增强 exclude_categories 过滤逻辑

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本文件是 `fix-pipeline-quality-gaps` 中同名 spec 的增量补充

## MODIFIED Requirements

### Requirement: list-page-directory-assignment

`_build_homepage_manifest()` SHALL assign each category's list page to the directory specified by the category's `dir` field in the strategy configuration, rather than using the first/any category's directory for all list pages.

#### Scenario: correct-directory-per-category

- **WHEN** homepage-driven discovery processes a strategy with categories `[{name: "Bosses", dir: "bosses"}, {name: "Characters", dir: "characters"}]`
- **THEN** the manifest SHALL contain:
  - Page "Items" with `target_directory: "items"` and `target_filename: "index.md"`
  - Page "Bosses" with `target_directory: "bosses"` and `target_filename: "index.md"`
  - Page "Characters" with `target_directory: "characters"` and `target_filename: "index.md"`

#### Scenario: category-page-type-dir-preservation

- **WHEN** a category has `type: category_page` (e.g., "Modes" or "Objects")
- **THEN** its `target_directory` SHALL be set to the directory configured for that category in the strategy
- **AND** its `target_filename` SHALL be `index.md`

### Requirement: exclude-categories-source-category-protection

The exclude_categories filter SHALL also check a page's `title` field against the exclude list, to catch pages that leak through because their `source_categories` or `assigned_category` do not directly match the excluded category name.

#### Scenario: excluded-page-by-title

- **WHEN** a page titled "Version History" has `source_categories: ["Items", "Trinkets"]` and `assigned_category: "Items"`
- **AND** `api.exclude_categories` includes "Version History"
- **THEN** the page SHALL be excluded from the manifest regardless of its `source_categories` or `assigned_category`

## RENAMED Requirements

（无重命名）

## REMOVED Requirements

（无废弃需求）
