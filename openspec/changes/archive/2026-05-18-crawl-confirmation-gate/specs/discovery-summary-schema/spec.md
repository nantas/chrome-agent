# Specification Delta

## Capability 对齐（已确认）

- Capability: `discovery-summary-schema`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: explore 阶段确认 —— 机器可读 JSON schema，由 CLI discovery-only 产生，由 SKILL 消费构建树状图

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: discovery-summary-top-level-fields

The `discovery_summary.json` SHALL contain the following top-level fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `discovery_method` | `"homepage" \| "allpages" \| "first_level_links"` | yes | Which discovery strategy was used |
| `site_title` | string | yes | Page title of the site's main page |
| `domain` | string | yes | Domain name |
| `categories` | array of category objects | yes | Discovered categories with their pages |
| `excluded` | array of exclusion objects | yes | Categories excluded from crawl (may be empty) |
| `unclassified` | unclassified object | yes | Pages that didn't match any category |
| `total_pages` | integer | yes | Total pages in manifest |
| `estimated_time_minutes` | integer | yes | Estimated extraction time |
| `manifest_path` | string | yes (API path) / null (Scrapling path) | Absolute path to `page_manifest.json` |
| `warnings` | array of strings | yes | Warnings from discovery (may be empty) |
| `caveats` | array of strings | yes | Limitations and caveats (may be empty) |
| `failure_rate` | number (0.0–1.0) | yes | Fraction of discovery operations that failed |

#### Scenario: minimum-valid-summary

- **WHEN** discovery completes with no failures and no exclusions
- **THEN** the summary SHALL have `excluded: []`, `warnings: []`, `caveats: []`, `failure_rate: 0.0`
- **AND** all required fields SHALL be present

### Requirement: category-object-schema

Each element in `categories` SHALL be an object with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name (e.g., "Items") |
| `directory` | string | yes | Output directory name (e.g., "items") |
| `type` | `"list_page" \| "category_page"` | yes | Category type from strategy |
| `is_index_page` | boolean | yes | Whether this category has an index.md |
| `page_count` | integer | yes | Number of pages in this category |
| `sample_pages` | array of strings (3-5) | yes | Representative page titles for context |
| `page_type` | string | yes | Type of pages in this category (e.g., "entity_page", "wiki_article") |

#### Scenario: list-page-category

- **WHEN** a category has `type: "list_page"` and `is_index_page: true`
- **THEN** the category SHALL have `page_count` including both the index page and all entity pages
- **AND** `sample_pages` SHALL contain 3-5 entity page titles, not the index page itself

#### Scenario: category-page-category

- **WHEN** a category has `type: "category_page"`
- **THEN** the category SHALL have `is_index_page: false`
- **AND** `page_count` SHALL count only member pages of that category

### Requirement: excluded-object-schema

Each element in `excluded` SHALL be an object with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Category display name |
| `page_count` | integer | yes | Number of pages excluded |
| `reason` | string | yes | Why this category was excluded (e.g., "api.exclude_categories", "CLI --exclude-category") |

#### Scenario: strategy-level-exclusion

- **WHEN** a category is excluded via `api.exclude_categories` in the strategy
- **THEN** the exclusion SHALL have `reason` matching the source of exclusion
- **AND** the excluded category SHALL NOT appear in `categories`

### Requirement: unclassified-object-schema

The `unclassified` field SHALL be an object with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `count` | integer | yes | Number of unclassified pages |
| `directory` | string | yes | Directory name for unclassified pages (e.g., "misc") |
| `sample_pages` | array of strings (0-5) | yes | Sample unclassified page titles (may be empty if count is 0) |

#### Scenario: zero-unclassified

- **WHEN** all pages are classified into categories
- **THEN** `unclassified.count` SHALL be 0
- **AND** `unclassified.sample_pages` SHALL be `[]`

### Requirement: scrapling-path-caveats

When `discovery_method` is `"first_level_links"`, the Scrapling discovery mode SHALL populate `caveats` with at minimum:

- A message stating that only first-level links from the main page were discovered
- A message stating that actual page counts may differ after full traversal

The `page_count` in each category SHALL be the count of unique URLs matched at the first level (not a precise count after full crawl).

#### Scenario: scrapling-discovery-summary

- **WHEN** discovery runs on a non-API site via Scrapling
- **THEN** `caveats` SHALL contain entries documenting the first-level-only limitation
- **AND** `manifest_path` SHALL be `null`
- **AND** `total_pages` SHALL be the sum of all first-level link counts
- **AND** `estimated_time_minutes` SHALL be a conservative estimate

### Requirement: time-estimation

The `estimated_time_minutes` field SHALL be calculated as:

- API path: `total_pages * avg_extraction_time_seconds / 60` where `avg_extraction_time_seconds` is based on the strategy's rate limit tier
- Scrapling path: `total_pages * 5 / 60` as a conservative default (5 seconds per page)

The estimate SHALL be a ceiling integer (rounded up).

#### Scenario: rate-limit-aware-estimation

- **WHEN** the strategy has `api.rate_limit.tier: "strict"` with `batch_delay_ms: 1200`
- **THEN** the estimate SHALL account for batch delays in addition to per-page extraction time
- **AND** the estimate SHALL NOT be less than 1 minute for any non-empty manifest
