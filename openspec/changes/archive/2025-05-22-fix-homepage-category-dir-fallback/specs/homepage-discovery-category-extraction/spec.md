# Specification Delta

## Capability 对齐（已确认）

- Capability: `homepage-discovery-category-extraction`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: _build_homepage_manifest() 中 cat_dir 为空时不更新 target_directory，导致无 dir 映射的分类页被分配到错误目录

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: category-page-directory-resolution

When `_build_homepage_manifest()` Step 1 processes a category from `parse_homepage()`, it SHALL resolve the target directory using a priority chain:

1. Strategy-configured `dir` mapping from `api.homepage.categories` (highest priority)
2. Auto-fallback: `cat_name.lower().replace(" ", "-")` when no strategy mapping exists

The resolved `cat_dir` SHALL always be non-empty. The `target_directory` of the category page entry SHALL always be updated to `cat_dir`, regardless of whether it was already assigned by `assign_pages()`.

When auto-fallback is triggered, the system SHALL emit a `log.warning` indicating the category name, the auto-generated directory, and a suggestion to add an explicit `dir` mapping to the strategy configuration.

This applies to both the `if page_title in existing_titles` branch (updating an existing page entry) and the `else` branch (creating a new entry).

#### Scenario: category-with-strategy-dir-mapping

- **GIVEN** a category "Items" with strategy config `{name: "Items", dir: "items"}`
- **WHEN** `_build_homepage_manifest()` processes this category
- **THEN** `cat_dir` SHALL be `"items"` (from strategy mapping)
- **AND** no warning SHALL be emitted
- **AND** the category page entry's `target_directory` SHALL be `"items"`

#### Scenario: category-without-strategy-dir-mapping

- **GIVEN** a category "Completion Marks" with no entry in `api.homepage.categories`
- **AND** the page "Completion Marks" already exists in `assigned_pages` with `target_directory: "items"` (from `assign_pages()`)
- **WHEN** `_build_homepage_manifest()` processes this category
- **THEN** `cat_dir` SHALL be `"completion-marks"` (auto-fallback)
- **AND** a `log.warning` SHALL be emitted with category name and auto-generated directory
- **AND** the existing entry's `target_directory` SHALL be updated from `"items"` to `"completion-marks"`
- **AND** the existing entry's `target_filename` SHALL be `"index.md"`
- **AND** the existing entry's `is_list_page` SHALL be `True`

#### Scenario: new-category-without-strategy-dir-mapping

- **GIVEN** a category "Attributes" with no entry in `api.homepage.categories`
- **AND** the page "Attributes" does NOT exist in `assigned_pages`
- **WHEN** `_build_homepage_manifest()` processes this category
- **THEN** `cat_dir` SHALL be `"attributes"` (auto-fallback)
- **AND** a new entry SHALL be created with `target_directory: "attributes"`, `target_filename: "index.md"`, `is_list_page: True`

#### Scenario: no-directory-overwrite-for-configured-categories

- **GIVEN** a category "Bosses" with strategy config `{name: "Bosses", dir: "bosses"}`
- **AND** the page "Bosses" exists in `assigned_pages` with `target_directory: "monsters"` (from `assign_pages()`)
- **WHEN** `_build_homepage_manifest()` processes this category
- **THEN** `cat_dir` SHALL be `"bosses"` (strategy mapping takes priority)
- **AND** the entry's `target_directory` SHALL be updated to `"bosses"`
- **AND** no auto-fallback warning SHALL be emitted
