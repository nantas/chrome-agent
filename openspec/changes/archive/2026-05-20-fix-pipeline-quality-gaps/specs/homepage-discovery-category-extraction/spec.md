# Specification Delta

## Capability 对齐（已确认）

- Capability: `homepage-discovery-category-extraction`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: explore 阶段确认 Phase 0 缺失关键功能——分类页面本身不入 manifest、不填 list_page_content，导致分类页不被提取

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: category-pages-in-manifest

The homepage discovery pipeline SHALL include category pages (the wiki pages linked from the homepage, such as "Items", "Bosses") in the page manifest alongside their member/linked pages.

Each category page entry SHALL include metadata marking it as a list page type so that Phase C can generate appropriate index pages.

#### Scenario: category-page-added-to-manifest

- **WHEN** the homepage parser discovers category "Items" with `page_title: "Items"` and `type: list_page`
- **AND** `_discover_list_page_pages()` finds 723 linked pages from the Items page
- **THEN** the manifest SHALL include the "Items" page itself as an entry
- **AND** the "Items" entry SHALL have `"is_list_page": true`
- **AND** the "Items" entry SHALL have `"target_directory"` matching the category's configured `dir` (e.g., `"items"`)
- **AND** the "Items" entry SHALL have `"target_filename"` set to `"index.md"`

#### Scenario: category-page-deduplication

- **WHEN** a page title appears both as a category page and as a linked/member page
- **THEN** the page SHALL appear only once in the manifest
- **AND** the `is_list_page` flag SHALL be `true` (category page metadata takes precedence)

#### Scenario: category-page-directory-assignment

- **WHEN** a category page is added to the manifest
- **THEN** its `target_directory` SHALL match the `dir` field from `api.homepage.categories`
- **AND** its `assignment_method` SHALL be `"homepage_category"`
- **AND** its `source_categories` SHALL include its own category name

### Requirement: list-page-content-population

The homepage discovery pipeline SHALL populate `manifest["list_page_content"]` with the wikitext content of each discovered list page, compatible with Phase C's index page generation.

#### Scenario: list-page-content-fetched

- **WHEN** homepage discovery identifies category pages (list_page type)
- **THEN** the pipeline SHALL fetch each list page's wikitext via `action=parse&prop=wikitext`
- **AND** the wikitext SHALL be stored in `manifest["list_page_content"][page_title]`
- **AND** the format SHALL match Phase A's `list_page_content` format exactly

#### Scenario: list-page-fetch-failure-graceful

- **WHEN** fetching a list page's wikitext fails (network error, page not found)
- **THEN** the pipeline SHALL log a warning with the page title
- **AND** the pipeline SHALL continue processing remaining list pages
- **AND** `manifest["list_page_content"]` SHALL omit the failed page (not contain an error placeholder)

#### Scenario: list-page-content-consumed-by-phase-c

- **WHEN** Phase C reads `manifest["list_page_content"]`
- **AND** a list page's wikitext content is available
- **THEN** Phase C SHALL use the content to generate `index.md` (via `list_page_assembler.assemble_index()`)
- **AND** the resulting `index.md` SHALL contain the category page's actual content, not just a bare link listing

### Requirement: exclude-categories-enforcement-in-homepage

The homepage discovery pipeline SHALL exclude category pages and their member pages when the category name matches `exclude_categories` (from strategy or CLI).

Exclusion SHALL occur before any member page discovery, preventing excluded categories' pages from entering the manifest.

#### Scenario: exclude-category-filtered-before-discovery

- **WHEN** `exclude_categories` contains `["Music", "Modding"]`
- **AND** the homepage parser discovers categories including "Music" and "Modding"
- **THEN** "Music" and "Modding" category entries SHALL be removed from the categories list
- **AND** NO member pages of Music or Modding SHALL be discovered
- **AND** category pages "Music" and "Modding" SHALL NOT appear in the manifest

#### Scenario: exclude-category-not-on-homepage

- **WHEN** `exclude_categories` contains `["Version History"]`
- **AND** "Version History" is NOT among the homepage-discovered categories
- **THEN** the pipeline SHALL log an info message `"Exclude category 'Version History' not found in homepage categories — ignoring"`
- **AND** the pipeline SHALL continue normally
