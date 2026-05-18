# homepage-driven-discovery Specification

## Purpose
Provides homepage-driven page discovery for MediaWiki pipelines. Parses the site homepage via MediaWiki API to extract category links, then discovers pages within each category using the appropriate strategy (list page links or category members). Outputs a manifest compatible with Phase B consumption.

## Requirements

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

### Requirement: category-exclusion-filtering

The system SHALL 在 Phase 0 的 `run_phase_0()` 中，`parse_homepage()` 完成后、`_discover_category_pages()` 调用前，按 `api.homepage.exclude_categories` 列表过滤分类。

排除匹配按 `categories[].name` 字段进行名称匹配（大小写敏感）。被排除的分类不进入 `_discover_category_pages()` 的后续遍历。

`exclude_categories` 为可选字段，缺失或为空时 SHALL 不过滤任何分类（行为与当前一致）。

#### Scenario: exclude-three-categories

- **WHEN** `api.homepage.exclude_categories` 为 `["Music", "Modding", "Version History"]`
- **AND** `parse_homepage()` 返回 19 个分类（含 Music、Modding、Version History）
- **THEN** `run_phase_0()` SHALL 过滤掉这三个分类
- **AND** `_discover_category_pages()` SHALL 仅接收 16 个分类
- **AND** 日志 SHALL 输出 `"Excluded N categories: Music, Modding, Version History"`（info 级别）

#### Scenario: no-exclusion-configured

- **WHEN** `api.homepage.exclude_categories` 未定义或为空列表 `[]`
- **THEN** `run_phase_0()` SHALL 不过滤任何分类
- **AND** 行为与当前完全一致

#### Scenario: exclude-category-not-found

- **WHEN** `exclude_categories` 包含 `"NonExistent"`
- **AND** `parse_homepage()` 返回的分类中无名称匹配 `"NonExistent"` 的分类
- **THEN** `run_phase_0()` SHALL 记录 `log.info("Exclude category 'NonExistent' not found in homepage categories — ignoring")`
- **AND** SHALL 不阻断流程，继续处理未排除的分类

### Requirement: excluded-categories-absent-from-manifest

被排除的分类 SHALL 不在最终 manifest 的任何位置出现（不在 `source_categories`、不在 `assigned_category`、不在 `categories_discovered` 计数中）。

#### Scenario: manifest-excludes-filtered-categories

- **WHEN** Music 分类被排除
- **THEN** manifest 中所有 page 的 `source_categories` SHALL 不包含 `"Music"`
- **AND** manifest 中所有 page 的 `assigned_category` SHALL 不为 `"Music"`
- **AND** `manifest.categories_discovered` SHALL 不包含被排除的分类

### Requirement: exclude-categories-merge-with-cli

Phase 0 SHALL 在运行时合并策略文件的 `api.homepage.exclude_categories` 和 CLI 传入的 `--exclude-category` 参数，取并集。合并逻辑由 `orchestrate.py` 的 `run_pipeline()` 负责，Phase 0 消费合并后的最终列表。

#### Scenario: merge-strategy-and-cli-excludes

- **WHEN** 策略 `exclude_categories` 为 `["Music", "Modding"]`
- **AND** CLI 传入 `--exclude-category "Version History" --exclude-category "Music"`
- **THEN** 最终排除列表 SHALL 为 `{"Music", "Modding", "Version History"}`（并集，去重）
- **AND** 日志 SHALL 输出 `"Excluded categories: Music, Modding, Version History (source: strategy=2, cli=2)"`
