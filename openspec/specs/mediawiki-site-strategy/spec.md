# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-site-strategy`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户已通过对话确认，为 vampire.survivors.wiki 创建 site strategy，使 crawl 命令可用；页面类型使用现有受控词汇表 static_page / static_article，无需扩展。

## 规范真源声明

- 本文件是 `mediawiki-site-strategy` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 策略文件创建

The system SHALL create a complete `sites/strategies/vampire.survivors.wiki/strategy.md` with valid YAML frontmatter and Markdown body.

#### Scenario: 必填 frontmatter 字段完整性

- **WHEN** the strategy file is created
- **THEN** it SHALL contain all mandatory fields per `site-strategy-schema`: `domain`, `description`, `protection_level`, `anti_crawl_refs`, `structure`, and optionally `extraction`
- **AND** `protection_level` SHALL be `low`
- **AND** `anti_crawl_refs` SHALL be `[]`
- **AND** `engine_preference.preferred` SHALL be `scrapling-get`

#### Scenario: 页面结构定义

- **WHEN** the strategy defines page structure
- **THEN** it SHALL declare at least two page types: `wiki_category` (type `static_page`) and `wiki_article` (type `static_article`)
- **AND** `wiki_category` SHALL define `links_to` targeting `wiki_article` with an appropriate CSS selector for MediaWiki internal links
- **AND** `entry_points` SHALL be `[wiki_category]`

#### Scenario: 提取配置

- **WHEN** the strategy defines extraction rules
- **THEN** `extraction.image_handling` SHALL specify `attribute: src`, `output_format: markdown_inline`
- **AND** `extraction.cleanup` SHALL list the applicable MediaWiki noise rule identifiers per `mediawiki-extraction-patterns`

### Requirement: 索引同步

The system SHALL update `sites/strategies/registry.json` with a new entry for `vampire.survivors.wiki`.

#### Scenario: Registry 一致性

- **WHEN** the site strategy is created
- **THEN** a corresponding entry SHALL be added to `registry.json`
- **AND** the entry SHALL include: `domain`, `description`, `protection_level`, `page_types`, `pagination`, `entry_points`, `anti_crawl_refs`, `file`
- **AND** `page_types` SHALL contain `static_page` and `static_article`
- **AND** `file` SHALL be `vampire.survivors.wiki/strategy.md`

## MODIFIED Requirements

### Requirement: content_profile 字段定义

The system SHALL recognize an `api.content_profile` field in the strategy frontmatter that allows declarative strategy selection for the MediaWiki API extraction pipeline.

The `content_profile` field is OPTIONAL. When absent, the pipeline SHALL use all default strategy implementations.

The `content_profile` schema SHALL be as follows:

```yaml
api:
  content_profile:
    discovery_strategy: "<strategy-id>"      # OPTIONAL, default: "allpages"
    content_acquisition: "<strategy-id>"     # OPTIONAL, default: "wikitext_only"
    link_resolver: "<strategy-id>"           # OPTIONAL, default: "exact_title_match"
    template_processor: "<strategy-id>"      # OPTIONAL, default: "simple_substitution"
    list_page_assembler: "<strategy-id>"     # OPTIONAL, default: "frontmatter_driven"
```

The following strategy IDs SHALL be recognized:

| Concern | Default ID | Available IDs (this change) |
|---------|-----------|-----------------------------|
| `discovery_strategy` | `allpages` | `allpages` |
| `content_acquisition` | `wikitext_only` | `wikitext_only` |
| `link_resolver` | `exact_title_match` | `exact_title_match` |
| `template_processor` | `simple_substitution` | `simple_substitution` |
| `list_page_assembler` | `frontmatter_driven` | `frontmatter_driven` |

**Note**: Additional strategy IDs (for StS2-specific implementations) SHALL be added in a future change (Change 2). This change only registers the default IDs.

#### Scenario: content_profile absent, defaults used

- **WHEN** the strategy file has no `api.content_profile` field
- **THEN** the pipeline SHALL compose all default strategy implementations
- **AND** the extraction behavior SHALL be identical to the current (pre-refactoring) behavior

#### Scenario: content_profile partially specified

- **WHEN** `api.content_profile` specifies only `discovery_strategy: "allpages"`
- **THEN** the discovery strategy SHALL use the `allpages` implementation
- **AND** all unspecified concerns SHALL use their default implementations

#### Scenario: content_profile fully specified with defaults

- **WHEN** `api.content_profile` explicitly specifies all five default IDs
- **THEN** the pipeline SHALL compose the specified implementations
- **AND** the extraction behavior SHALL be identical to the current behavior

#### Scenario: Unknown strategy ID

- **WHEN** `api.content_profile` specifies an unknown strategy ID (e.g., `discovery_strategy: "unknown_strategy"`)
- **THEN** the pipeline SHALL log a warning and use the default implementation for that concern
- **AND** the pipeline SHALL NOT fail

### Requirement: capabilities 字段引用

The system SHALL document that `api.capabilities` is the list of API capabilities the strategy declares as available. The declaration SHALL use the controlled vocabulary defined in `mediawiki-api-extraction` spec.

The `capabilities` field SHALL be checked by the pipeline's `validate_api_config` to ensure the strategy's declared capabilities cover the union of `required_capabilities` from all composed strategies.

#### Scenario: Capabilities reference validation

- **WHEN** a strategy declares `api.capabilities: [page_list, category_lookup, wikitext_parse]`
- **AND** the default strategies require `{page_list, category_lookup, wikitext_parse}`
- **THEN** validation SHALL pass

#### Scenario: Capabilities subset validation

- **WHEN** a strategy declares `api.capabilities: [page_list]` (subset)
- **AND** the default strategies require `{page_list, category_lookup, wikitext_parse}`
- **THEN** validation SHALL fail with missing capabilities reported

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
