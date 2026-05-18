# page-assignment Specification

## Purpose
Assigns discovered pages to output directories based on a priority chain: manual overrides, category page membership, and MediaWiki category tag matching. Enriches the manifest with assignment metadata for downstream pipeline consumption.

## Requirements

### Requirement: priority-chain-assignment

The system SHALL assign each discovered page to an output directory using a priority chain:

1. Manual overrides (from strategy `api.homepage.manual_assignments`)
2. Category page special members (pages matching a category_page's member set)
3. MediaWiki category tag matching (query `prop=categories`, match against `api.homepage.categories`, ordered by `api.homepage.assignment_priority`)

#### Scenario: manual-override-takes-precedence

- **WHEN** a page `"Seeds"` appears in the Seeds category's linked pages
- **AND** `manual_assignments` specifies `{"Seeds": "seeds"}`
- **THEN** the page SHALL be assigned to directory `"seeds"` regardless of MW category tags

#### Scenario: category-page-special-members

- **WHEN** a page is a member of a `category_page` type category (e.g., `Category:Modes`)
- **AND** no manual override exists for this page
- **THEN** the page SHALL be assigned to the directory configured for that category_page

#### Scenario: mw-category-tag-matching

- **WHEN** a page has MediaWiki category tags `["Bosses", "Basement bosses"]`
- **AND** `assignment_priority` lists `["Bosses", "Chapters", "Monsters"]`
- **AND** `categories` maps `Bosses` → `"bosses"`
- **THEN** the page SHALL be assigned to directory `"bosses"` (first matching priority)

#### Scenario: no-matching-category

- **WHEN** a page has no MediaWiki category tags matching any configured category
- **THEN** the page SHALL be assigned to a `"misc"` directory
- **THEN** a warning SHALL be logged

### Requirement: mw-category-batch-lookup

The system SHALL query MediaWiki category tags in batches of 50 titles via `action=query&prop=categories`.

#### Scenario: batch-category-query

- **WHEN** 1,750 pages need category lookup
- **THEN** the system SHALL split them into batches of 50
- **THEN** each batch SHALL use a single API call with pipe-separated titles
- **THEN** rate limiting (from `api.rate_limit`) SHALL be respected between batches

#### Scenario: category-query-error-handling

- **WHEN** a batch category query fails (network error, rate limit)
- **THEN** the system SHALL retry per `api.rate_limit.retry` configuration
- **THEN** after max retries, pages in the failed batch SHALL be assigned to `"misc"`

### Requirement: assignment-priority-ordering

The system SHALL use `api.homepage.assignment_priority` as an ordered list where earlier entries have higher priority.

#### Scenario: priority-ordering-respected

- **WHEN** `assignment_priority` is `["Items", "Bosses"]`
- **AND** a page has MW categories `["Bosses", "Collectibles"]`
- **AND** `categories` maps `Bosses` → `"bosses"` and `Collectibles` → `"items"`
- **THEN** the page SHALL be assigned to `"bosses"` (Bosses appears first in priority)
- **THEN** not `"items"` (Collectibles appears later in priority chain)

### Requirement: manifest-enrichment

After assignment, the system SHALL enrich each manifest page entry with assignment metadata.

Each page entry SHALL include:
- `assigned_category`: the category name that determined the directory
- `mw_categories`: list of all MediaWiki category tags found
- `assignment_method`: one of `manual`, `category_page_member`, `mw_category_match`, `default`

#### Scenario: manifest-with-assignment-metadata

- **WHEN** a page is assigned via MW category tag matching
- **THEN** `assigned_category` SHALL be the matched category name
- **THEN** `mw_categories` SHALL contain all category tags from the API
- **THEN** `assignment_method` SHALL be `"mw_category_match"`

### Requirement: excluded-categories-not-in-input

`assign_pages()` SHALL 不接收已被排除的分类的页面数据。排除在 Phase 0 的 `run_phase_0()` 中完成（源头过滤），`assign_pages()` 无需内部感知排除逻辑。

#### Scenario: assigner-receives-filtered-input

- **WHEN** Phase 0 排除了 Music、Modding、Version History 三个分类
- **THEN** `assign_pages()` 接收的 `categories` 参数 SHALL 不包含这三个分类
- **AND** `assign_pages()` 接收的 `pages` 参数 SHALL 不包含任何 `source_categories` 仅为已排除分类的页面
- **AND** 分配逻辑 SHALL 无需任何代码变更即可正确处理

#### Scenario: page-in-multiple-categories-one-excluded

- **WHEN** 页面 "Sacrificial Altar" 同时属于 Items（未排除）和 Music（已排除）两个分类
- **AND** Music 被排除
- **THEN** 该页面的 `source_categories` SHALL 仅包含 `["Items"]`
- **AND** 页面 SHALL 被分配至 Items 目录（通过 MW category 匹配或 category_page_member 分配）
