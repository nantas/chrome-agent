# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-site-strategy`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户选择三层方案，需扩展策略 schema 增加 api.homepage 配置块

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: api-homepage-config-block

The system SHALL recognize an optional `api.homepage` configuration block in the strategy YAML frontmatter for homepage-driven crawl entry points.

The `api.homepage` block SHALL contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_title` | string | yes | The actual wiki page title of the homepage (handles redirect from `Main_Page`) |
| `category_sections` | object[] | yes | CSS selectors to extract category links from homepage HTML |
| `categories` | object[] | yes | List of categories with name-to-directory mapping |
| `category_page_types` | object | no | Map of category name to page type (`list_page` or `category_page`). Default: `list_page` |
| `assignment_priority` | string[] | yes | Ordered list of category names for multi-category page assignment priority |
| `manual_assignments` | object | no | Map of page title to output directory for manual override |

Each `category_sections` entry SHALL contain:
- `selector` (string, required): CSS selector for category link elements
- `type` (string, optional): `list_page` or `category_page`, default `list_page`

Each `categories` entry SHALL contain:
- `name` (string, required): Category display name (e.g., `"Items"`, `"Bosses"`)
- `dir` (string, required): Output subdirectory name (e.g., `"items"`, `"bosses"`)

#### Scenario: valid-homepage-config

- **WHEN** a strategy file defines `api.homepage` with all required fields
- **THEN** the strategy SHALL be accepted for `--phase homepage` pipeline execution
- **THEN** all fields SHALL be parsed without error

#### Scenario: missing-homepage-config

- **WHEN** a strategy file does NOT define `api.homepage`
- **THEN** the strategy SHALL remain valid for all other pipeline phases
- **THEN** `--phase homepage` SHALL NOT be available for this strategy

#### Scenario: category-page-type-distinction

- **WHEN** `category_page_types` maps `"Modes"` to `"category_page"`
- **AND** `"Objects"` to `"category_page"`
- **THEN** discovery for these categories SHALL use `categorymembers` API
- **THEN** categories NOT listed SHALL default to `list_page` (using `prop=links`)

#### Scenario: assignment-priority-with-mapping

- **WHEN** `assignment_priority` lists `["Items", "Bosses", "Monsters"]`
- **AND** `categories` maps `Items` → `"items"`, `Bosses` → `"bosses"`, `Monsters` → `"monsters"`
- **THEN** a page with MW categories `["Bosses", "Monsters"]` SHALL be assigned to `"bosses"` (first match)
- **THEN** a page with MW categories `["Collectibles"]` (maps to `Items` → `"items"`) SHALL be assigned to `"items"`

### Requirement: structure-category-page-type

The system SHALL accept `category` as a valid value for `structure.pages[].type` in site strategy files.

A page with `type: category` SHALL:
- Have `content_type: wiki_category`
- Default discovery strategy SHALL be `categorymembers` (via ns=14 Category namespace)

#### Scenario: category-page-in-structure

- **WHEN** a strategy defines a page with `type: category` and `content_type: wiki_category`
- **THEN** the strategy SHALL be considered valid
- **THEN** pipeline consumers SHALL use `categorymembers` for discovery by default
