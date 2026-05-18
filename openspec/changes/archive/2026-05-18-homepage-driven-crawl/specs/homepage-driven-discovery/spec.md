# Specification Delta

## Capability 对齐（已确认）

- Capability: `homepage-driven-discovery`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户选择三层推进方案，要求新增首页驱动的分类发现管线

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: homepage-html-parsing

The system SHALL parse the homepage HTML specified in strategy `api.homepage.page_title` via MediaWiki `action=parse` API to extract category links.

The homepage fetch SHALL use `redirects=true` to handle pages that are redirect targets (e.g., `Main_Page` → `Binding_of_Isaac:_Rebirth_Wiki`).

#### Scenario: homepage-fetch-with-redirect

- **WHEN** `api.homepage.page_title` is `"Main_Page"` and the page is a redirect
- **THEN** the API call SHALL include `redirects=true`
- **THEN** the returned HTML SHALL be from the resolved page, not empty or error

#### Scenario: homepage-fetch-direct

- **WHEN** `api.homepage.page_title` is the actual page title (no redirect)
- **THEN** the API call SHALL succeed with `redirects=true` (no-op on non-redirect pages)

### Requirement: category-link-extraction

The system SHALL extract category links from the homepage HTML using CSS selectors defined in `api.homepage.category_sections`.

Each `category_sections` entry SHALL contain a `selector` field (CSS selector string) and MAY contain a `type` field (`list_page` or `category_page`, defaulting to `list_page`).

#### Scenario: extract-gallery-links

- **WHEN** `category_sections` contains `{selector: ".gallerytext a"}` and the homepage has gallery-linked categories
- **THEN** the system SHALL extract all `<a>` elements matching the selector
- **THEN** each extracted link SHALL be resolved to a page title and a category name
- **THEN** links to non-wiki pages (external URLs) SHALL be filtered out

#### Scenario: category-name-resolution

- **WHEN** a category link's display text is `"Items"` but the href is `/wiki/Items`
- **THEN** the category name SHALL be derived from the display text (`"Items"`)
- **THEN** the page title SHALL be derived from the href (`"Items"`)

### Requirement: category-discovery-strategy-selection

The system SHALL select the appropriate page discovery strategy based on the category page type.

- For `type: list_page` (ns=0): use `action=parse&prop=links` to discover linked pages
- For `type: category_page` (ns=14): use `action=query&list=categorymembers` to discover member pages

#### Scenario: list-page-discovery

- **WHEN** a category has `type: list_page` (or no type specified)
- **THEN** the system SHALL call `action=parse&page=<title>&prop=links` to discover sub-pages
- **THEN** only ns=0 links SHALL be included in the page list

#### Scenario: category-page-discovery

- **WHEN** a category has `type: category_page` (ns=14 Category namespace)
- **THEN** the system SHALL call `action=query&list=categorymembers&cmtitle=Category:<name>` to discover members
- **THEN** all member pages SHALL be included in the page list

#### Scenario: discovery-deduplication

- **WHEN** the same page title is discovered from multiple categories
- **THEN** the page SHALL appear only once in the de-duplicated page list
- **THEN** the discovery source categories SHALL be preserved for assignment


### Requirement: category-namespace-link-inclusion

The system SHALL NOT skip Category: namespace links during homepage link extraction. Category: pages linked from the homepage gallery (e.g., `Category:Objects`, `Category:Modes`) SHALL be included as discoverable categories.

Previously, `_extract_links_from_element()` skipped all non-content namespaces including `Category:`. This requirement REMOVES `Category:` from the exclusion list while keeping `File:`, `Template:`, `Talk:`, `Special:`, `Help:`, and `User:` excluded.

#### Scenario: category-namespace-link-discovered

- **WHEN** the homepage gallery contains `<a href="/wiki/Category:Objects">Objects</a>`
- **THEN** the link SHALL NOT be filtered out by the namespace skip list
- **THEN** the extracted category SHALL have `page_title: "Category:Objects"` and `name: "Objects"`

#### Scenario: non-content-namespaces-still-filtered

- **WHEN** a link points to `File:`, `Template:`, `Talk:`, `Special:`, `Help:`, or `User:` namespace
- **THEN** the link SHALL still be filtered out
- **THEN** only Category: namespace is newly included among previously-filtered namespaces

### Requirement: category-page-auto-detection

The system SHALL auto-detect category page type from the `page_title` prefix when no explicit type is configured in `category_page_types`.

If `page_title` starts with `Category:`, the type SHALL default to `category_page` regardless of the selector-level default type.

Priority: `category_page_types` explicit mapping > `page_title` prefix auto-detection > selector-level `default_type`.

#### Scenario: auto-detect-category-page

- **WHEN** a homepage link has `page_title: "Category:Objects"` and `name: "Objects"`
- **AND** `category_page_types` does NOT contain `"Objects"`
- **THEN** the category type SHALL be `"category_page"` (auto-detected from prefix)

#### Scenario: explicit-override-takes-precedence

- **WHEN** `category_page_types` maps `"Objects"` to `"list_page"` (explicit override)
- **AND** `page_title` starts with `Category:`
- **THEN** the type SHALL be `"list_page"` (explicit config wins over auto-detection)

### Requirement: manifest-output-compatibility

The output of homepage-driven discovery SHALL be a manifest JSON that is structurally compatible with Phase A's output format.

The manifest SHALL include:
- `pages`: array of `{title, target_directory, target_filename, source_categories, mw_categories}`
- Metadata fields compatible with Phase B consumption

#### Scenario: manifest-compatible-with-phase-b

- **WHEN** homepage-driven discovery completes
- **THEN** the output manifest SHALL be writable to `page_manifest.json`
- **THEN** Phase B SHALL be able to consume it without modification
- **THEN** `target_directory` SHALL reflect the assigned output subdirectory
