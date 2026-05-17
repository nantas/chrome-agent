# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认策略文件的 `extraction` 配置增加 `infobox_field_handlers` map，定义每个 data-source 字段的值提取语义

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: infobox-field-handler-configuration

The strategy file's `extraction` section SHALL optionally include an `infobox_field_handlers` map that defines how each portable infobox `data-source` field value should be extracted from raw HTML.

The map SHALL use the format:
```yaml
extraction:
  infobox_field_handlers:
    health:
      handler: count_images
      description: "Count red heart images"
    id:
      handler: extract_cur_id
      description: "Extract current ID from infobox-nav-cur span"
    alias:
      handler: dedup_pools
      description: "Deduplicate item pool links, skip icon-only entries"
```

Supported handler types:

| Handler | Description | Input | Output |
|---------|-------------|-------|--------|
| `text` | Plain text extraction (default) | Any HTML | Stripped text |
| `image` | Extract main image as Markdown | `<img src="...">` | `![alt](full_url)` |
| `count_images` | Count images by alt text pattern | Multiple `<img>` | `3× Full red heart` |
| `extract_cur_id` | Extract current ID from `infobox-nav-cur` | `<span class="infobox-nav-cur">1</span>` | `1` |
| `dedup_pools` | Deduplicate item pool links, filter icon-only | Pool `<a>` links | `[Crane Game](url), [Treasure Room](url)` |
| `simplify_collection` | Simplify collection grid to single page link | Grid position links | `See [Collection Page](url)` |
| `extract_tags` | Extract tag tooltips from icon links | Icon-only `<a>` with title | `[Used by...](url), [Lachryphagy unlock](url)` |

#### Scenario: handler-map-present
- **WHEN** a strategy file defines `extraction.infoxbox_field_handlers`
- **THEN** the converter SHALL apply the specified handler for each field's `data-source` value
- **THEN** fields not listed in the map SHALL use the default `text` handler

#### Scenario: handler-map-absent
- **WHEN** a strategy file does NOT define `extraction.infoxbox_field_handlers`
- **THEN** all infobox fields SHALL use the default `text` handler
- **THEN** no error SHALL be raised

#### Scenario: handler-count-images
- **WHEN** a field uses `handler: count_images` and the raw value contains 3 `<img alt="Full red heart" ...>`
- **THEN** the output SHALL be `3× Full red heart`

#### Scenario: handler-extract-cur-id
- **WHEN** a field uses `handler: extract_cur_id` and the raw value contains `<span class="infobox-nav-cur"><code>1</code></span>` between `<span class="infobox-nav-prev">` and `<span class="infobox-nav-next">`
- **THEN** the output SHALL be `1` (only the current/cur value)

#### Scenario: handler-dedup-pools
- **WHEN** a field uses `handler: dedup_pools` and the raw value contains duplicate pool links (one with icon image, one with text)
- **THEN** the output SHALL contain only the text-based links (skipping icon-only duplicates)
- **AND** links SHALL be comma-separated in `[Pool Name](full_url)` format

### Requirement: extraction-config-propagation

The `infobox_field_handlers` configuration from the strategy file SHALL be propagated to `HtmlToMarkdownConverter` at construction time via the `extraction_config` dictionary.

#### Scenario: config-passed-to-converter
- **WHEN** `HtmlToMarkdownConverter` is instantiated by the pipeline
- **THEN** `extraction_config.infoxbox_field_handlers` SHALL be passed from the strategy file
- **THEN** the converter SHALL apply the handlers during infobox conversion
