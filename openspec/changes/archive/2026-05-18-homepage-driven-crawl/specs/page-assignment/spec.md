# Specification Delta

## Capability 对齐（已确认）

- Capability: `page-assignment`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户选择三层推进方案，要求新增页面→目录分配逻辑

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

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
