# Specification Delta

## Capability 对齐（已确认）

- Capability: `homepage-driven-discovery`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: Phase 0 需要补充分类页面 manifest 入列、list_page_content 获取功能；manifest 输出格式扩展

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: manifest-output-compatibility

The output of homepage-driven discovery SHALL be a manifest JSON that is structurally compatible with Phase B and Phase C consumption, AND SHALL include category pages and list page content.

The manifest SHALL include:
- `pages`: array of `{title, target_directory, target_filename, source_categories, mw_categories, is_list_page?, assigned_category?, assignment_method?}`
- `list_page_content`: dict mapping page_title → wikitext string (for list pages)
- `categories_discovered`: number of categories found on homepage
- Metadata fields compatible with Phase B/Phase C consumption

#### Scenario: manifest-includes-category-pages

- **WHEN** homepage-driven discovery completes with categories "Items" (list_page) and "Bosses" (list_page)
- **THEN** the manifest SHALL include entries for "Items" and "Bosses" with `is_list_page: true`
- **AND** the manifest SHALL include entries for member pages (The Sad Onion, Monstro, etc.)
- **AND** the total page count SHALL include both category pages and member pages

#### Scenario: manifest-includes-list-page-content

- **WHEN** homepage-driven discovery completes
- **AND** list page wikitext was successfully fetched for "Items" and "Bosses"
- **THEN** `manifest["list_page_content"]` SHALL contain keys "Items" and "Bosses"
- **AND** each value SHALL be a non-empty wikitext string
- **AND** the format SHALL match Phase A's `list_page_content` format

#### Scenario: manifest-compatible-with-phase-b

- **WHEN** homepage-driven discovery completes
- **THEN** the output manifest SHALL be writable to `page_manifest.json`
- **AND** Phase B SHALL be able to consume the manifest without modification
- **AND** Phase C SHALL be able to consume both `pages` and `list_page_content`

### Requirement: category-discovery-strategy-selection

The system SHALL select the appropriate page discovery strategy based on the category page type.

- For `type: list_page` (ns=0): use `action=parse&prop=links` to discover linked pages
- For `type: category_page` (ns=14): use `action=query&list=categorymembers` to discover member pages

**ADDED**: The category page itself SHALL be included in the discovered page set for both types.

#### Scenario: list-page-discovery-includes-self

- **WHEN** a category has `type: list_page`
- **THEN** the system SHALL call `action=parse&page=<title>&prop=links` to discover sub-pages
- **AND** the list page itself SHALL be added to the discovered page set with `is_list_page: true`
- **AND** only ns=0 links SHALL be included in the linked page list

#### Scenario: category-page-discovery-includes-self

- **WHEN** a category has `type: category_page`
- **THEN** the system SHALL call `action=query&list=categorymembers&cmtitle=Category:<name>` to discover members
- **AND** the category page itself (ns=14 entry) SHALL NOT be added (ns=14 pages are not extracted)
- **AND** all ns=0 member pages SHALL be included in the page list

### Requirement: discovery-deduplication

The system SHALL deduplicate discovered pages. When the same page title is discovered from multiple categories, the page SHALL appear only once, with `source_categories` containing all originating categories.

**ADDED**: When a page is both a category page and discovered as a member of another category, the `is_list_page` flag SHALL take precedence.

#### Scenario: category-page-also-discovered-as-member

- **WHEN** "Items" is a category page (is_list_page: true)
- **AND** "Items" is also linked from another list page as a member
- **THEN** the page SHALL appear once in the manifest
- **AND** `is_list_page` SHALL be `true`
- **AND** `source_categories` SHALL include both originating category names
