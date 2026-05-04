# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy-schema`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认在策略 schema 中新增可选 `api` 字段，用于记录 CMS 平台的 API 能力，支持 crawl 命令的 API-first 路由

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/site-strategy-schema/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: API 提取配置

The system SHALL define an optional `api` object in the site strategy YAML frontmatter for sites that expose a CMS API for structured content extraction.

The `api` object SHALL contain:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platform` | enum | yes | CMS platform identifier. Current valid value: `mediawiki` |
| `base_url` | string | no | API base URL. When absent, the system SHALL auto-detect via endpoint probing |
| `capabilities` | string[] | yes | List of supported API operations. Current valid values: `page_list`, `category_lookup`, `wikitext_parse`, `html_parse` |
| `taxonomy` | object | no | Category-to-directory mapping rules |
| `filename` | object | no | Filename sanitization rules |
| `output` | object | no | Output configuration for Markdown generation |

The `api` field SHALL be optional. Its absence SHALL NOT invalidate the strategy file.

#### Scenario: 完整 api 字段示例

- **WHEN** a MediaWiki strategy declares:
  ```yaml
  api:
    platform: mediawiki
    base_url: "https://balatrowiki.org/api.php"
    capabilities:
      - page_list
      - category_lookup
      - wikitext_parse
    taxonomy:
      list_pages:
        Jokers: "Jokers"
        Decks: "Decks"
      category_filters:
        - "Disambiguations"
    filename:
      replacements:
        "/": "_"
        ":": "_"
    output:
      frontmatter_fields:
        - effect
        - rarity
        - type
        - buyprice
        - sellprice
  ```
- **THEN** the crawl command SHALL recognize this site as API-capable
- **AND** the system SHALL route to the MediaWiki API extraction pipeline when `crawl` is invoked

#### Scenario: api 字段缺失

- **WHEN** a strategy file does not include an `api` field
- **THEN** the strategy SHALL be considered fully valid
- **AND** crawl SHALL route to the standard Scrapling pipeline
- **AND** no validation error SHALL be raised

#### Scenario: api.platform 值无效

- **WHEN** a strategy declares `api.platform` with a value other than `mediawiki`
- **THEN** the system SHALL emit a warning
- **AND** crawl SHALL fall through to the Scrapling pipeline
- **AND** the unknown platform value SHALL be preserved in the strategy file for future use

### Requirement: API Capabilities 受控词汇表

The system SHALL define a controlled vocabulary for `api.capabilities` values.

| Value | Description |
|-------|-------------|
| `page_list` | Site exposes a page listing API (e.g., `action=query&list=allpages`) |
| `category_lookup` | Site exposes a category lookup API (e.g., `action=query&prop=categories`) |
| `wikitext_parse` | Site exposes a wikitext parse API (e.g., `action=parse&prop=wikitext`) |
| `html_parse` | Site exposes an HTML parse API (e.g., `action=parse&prop=text`) |

New values SHALL be added via openspec change to this spec.

#### Scenario: Capabilities 清单驱动管线行为

- **WHEN** `api.capabilities` contains `page_list`
- **THEN** the system SHALL use the API for page discovery (Phase A)
- **AND** when absent, Phase A SHALL fall back to DOM link extraction

- **WHEN** `api.capabilities` contains `wikitext_parse`
- **THEN** the system SHALL use the API for content extraction (Phase B)
- **AND** when absent but `html_parse` is present, Phase B SHALL use HTML extraction (with appropriate DOM parser)
- **AND** when neither is present, Phase B SHALL fall back to Scrapling

### Requirement: API Taxonomy 配置

The system SHALL define the `api.taxonomy` object for category-to-directory mapping.

`api.taxonomy` SHALL contain:
- `list_pages` (optional): map of page title to target directory path, used for list pages that serve as `index.md`
- `category_filters` (optional): array of category names to exclude from content classification

#### Scenario: list_pages 映射

- **WHEN** a strategy declares:
  ```yaml
  taxonomy:
    list_pages:
      Jokers: "Jokers"
      Tarot_Cards: "Consumables/Tarot_Cards"
  ```
- **THEN** the page "Jokers" SHALL be used as the source for `Jokers/index.md`
- **AND** the page "Tarot_Cards" SHALL be used as the source for `Consumables/Tarot_Cards/index.md`
- **AND** list pages themselves SHALL NOT be placed in other directories per normal category routing

#### Scenario: category_filters 排除

- **WHEN** a strategy declares `category_filters: ["Disambiguations"]`
- **THEN** pages whose only category is "Disambiguations" SHALL be classified as Misc rather than any content directory
- **AND** this SHALL prevent disambiguation pages from polluting content directories

### Requirement: API Filename 配置

The system SHALL define the `api.filename` object for filename sanitization rules.

`api.filename` SHALL contain:
- `replacements` (required if `filename` is present): map of character to replacement string for filename sanitization

#### Scenario: 文件名替换

- **WHEN** a strategy declares `filename.replacements: { "/": "_", ":": "_" }`
- **THEN** page title `File:Joker.png` SHALL produce filename `Joker.png`
- **AND** page title `Update 1.0.0h/Fixes` SHALL produce filename `Update 1.0.0h_Fixes.md`
- **AND** only characters in the replacements map SHALL be substituted; all other characters SHALL be preserved

### Requirement: API Output 配置

The system SHALL define the `api.output` object for Markdown output configuration.

`api.output` SHALL contain:
- `frontmatter_fields` (optional): array of infobox template parameter names to extract as YAML frontmatter fields
- `template_map` (optional): map of wikitext template names to inline Markdown format strings

#### Scenario: frontmatter_fields 提取

- **WHEN** a strategy declares `output.frontmatter_fields: [effect, rarity, type, buyprice, sellprice]`
- **THEN** the system SHALL search wikitext for template parameters matching these names
- **AND** matched values SHALL be written as YAML frontmatter fields
- **AND** the `title` and `source_url` fields SHALL always be present regardless of `frontmatter_fields`

#### Scenario: template_map 展开

- **WHEN** a strategy declares `output.template_map: { "Mult": "**%s Mult**", "Chips": "**%s Chips**" }`
- **THEN** wikitext `{{Mult|+4}}` SHALL convert to `**+4 Mult**`
- **AND** wikitext `{{Chips|+5}}` SHALL convert to `**+5 Chips**`
- **AND** templates not in the map SHALL be logged as warnings and preserved as `{{...}}` text
