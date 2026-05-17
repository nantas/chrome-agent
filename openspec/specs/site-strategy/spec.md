# site-strategy Specification

## Purpose
TBD - created by archiving change template-content-profile-and-strategy-fixes. Update Purpose after archive.

## Requirements

### Requirement: valid-tier-reference
站点策略文件的 `api.rate_limit.tier` 值 SHALL 引用在对应 anti-crawl 策略文件的 `rate_limit_tiers` 中已定义的 tier 名称。

#### Scenario: neonabyss-tier-fix
- **WHEN** 检查 `neonabyss.fandom.com/strategy.md` 的 `api.rate_limit.tier`
- **THEN** 值为 `"strict"`（在 `rate-limit-api.md` 的 `rate_limit_tiers` 中存在）

### Requirement: anti-crawl-registry-site-coverage
`sites/anti-crawl/registry.json` 中每个 anti-crawl 策略条目的 `sites` 列表 SHALL 包含所有在站点策略 `anti_crawl_refs` 中引用该 anti-crawl 策略的域名。

#### Scenario: neonabyss-in-rate-limit-api-registry
- **WHEN** 检查 `sites/anti-crawl/registry.json` 中 `rate-limit-api` 条目的 `sites` 列表
- **THEN** 列表包含 `"neonabyss.fandom.com"`

### Requirement: non-superseded-engine-preference
站点策略的 `engine_preference.preferred` SHOULD NOT 引用状态为 `superseded` 的引擎。当存在替代引擎时，SHALL 更新为替代引擎 ID。

#### Scenario: bgg-engine-update
- **WHEN** 检查 `boardgamegeek.com/strategy.md` 的 `engine_preference.preferred`
- **THEN** 值为 `"cloakbrowser-fetch"`（`scrapling-stealthy-fetch` 的替代引擎）

### Requirement: platform-variant-declaration
使用非标准 MediaWiki 平台变体的站点策略 SHALL 在 `api.platform_variant` 中声明其变体类型。

#### Scenario: slaythespire-wiki-gg-variant
- **WHEN** 检查 `slaythespire.wiki.gg/strategy.md` 的 `api.platform_variant`
- **THEN** 值为 `"wiki-gg"`

### Requirement: strategy-registry-sync
`sites/strategies/registry.json` 中每个条目的元数据 SHALL 与对应策略文件的 frontmatter 保持一致。当策略文件修改时，registry 中对应条目的 `description`、`anti_crawl_refs`、`page_types` 等字段 SHALL 同步更新。

#### Scenario: registry-reflects-neonabyss-changes
- **WHEN** neonabyss 策略文件的 tier 从 "standard" 改为 "strict"
- **THEN** registry.json 中 neonabyss 条目的 `anti_crawl_refs` 包含 `"rate-limit-api"`（已包含则不变）

### Requirement: neonabyss.fandom.com 策略文件 content_profile 修正
The system SHALL 修正 `sites/strategies/neonabyss.fandom.com/strategy.md` 的 `api.content_profile` 引用，使其符合 `_STRATEGY_REGISTRY` 的约束。

需要修正的两个字段：

| 字段 | 当前值 | 目标值 | 原因 |
|------|--------|--------|------|
| `link_resolver` | `short_name` | `short_name_with_cross_namespace` | `short_name` 未注册 |
| `template_processor` | `fandom_infobox` | `fandom_infobox`（保持） | 本 change 中注册 |

此外，SHALL 增加 `api.platform_variant: fandom` 字段。

#### Scenario: 修正后的 content_profile
- **WHEN** neonabyss.fandom.com/strategy.md 的 content_profile 被 pipeline 读取
- **THEN** 以下引用 SHALL 在 `_STRATEGY_REGISTRY` 中全部合法

### Requirement: YAML frontmatter 新增字段
The system SHALL 在策略文件的 `api` 对象中增加以下可选字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `platform_variant` | enum | no | MediaWiki 平台变体标识，当前取值：`standard`（默认）、`fandom`、`wiki-gg` |

### Requirement: content_profile ID 引用约束
The system SHALL 对 `api.content_profile` 各字段的 value 施加引用完整性约束。

允许值（当前注册 ID 清单，来自 `_STRATEGY_REGISTRY`）：

| 维度 | 合法 ID |
|--------|----------|
| `discovery_strategy` | `allpages`, `category_members` |
| `content_acquisition` | `wikitext_only`, `hybrid_wikitext_plus_rendered`, `html_rendered` |
| `link_resolver` | `exact_title_match`, `short_name_with_cross_namespace` |
| `template_processor` | `simple_substitution`, `structured_with_lua_fallback` |
| `list_page_assembler` | `frontmatter_driven`, `hybrid_frontmatter_and_rendered` |

引用未注册 ID 的策略文件 SHALL 被视为无效文件。

#### Scenario: 引用未注册 ID
- **WHEN** 策略文件指定了未注册的 content_profile ID
- **THEN** pipeline SHALL 拒绝执行并返回 `EXIT_STRATEGY_ERROR`

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
```

Supported handler types:

| Handler | Description | Input | Output |
|---------|-------------|-------|--------|
| `text` | Plain text extraction (default) | Any HTML | Stripped text |
| `image` | Extract main image as Markdown | `<img src="...">` | `![alt](full_url)` |
| `count_images` | Count images by alt text pattern | Multiple `<img>` | `3× Full red heart` |
| `extract_cur_id` | Extract current ID from `infobox-nav-cur` | `<span class="infobox-nav-cur">1</span>` | `1` |
| `dedup_pools` | Deduplicate item pool links, filter icon-only | Pool `<a>` links | `[Pool Name](url), ...` |
| `simplify_collection` | Simplify collection grid to single page link | Grid position links | `See [Collection Page](url)` |
| `extract_tags` | Extract tag tooltips from icon links | Icon-only `<a>` with title | `[Used by...](url), ...` |

#### Scenario: handler-map-present
- **WHEN** a strategy file defines `extraction.infobox_field_handlers`
- **THEN** the converter SHALL apply the specified handler for each field's `data-source` value
- **THEN** fields not listed in the map SHALL use the default `text` handler

#### Scenario: handler-map-absent
- **WHEN** a strategy file does NOT define `extraction.infobox_field_handlers`
- **THEN** all infobox fields SHALL use the default `text` handler
- **THEN** no error SHALL be raised

### Requirement: extraction-config-propagation

The `infobox_field_handlers` configuration from the strategy file SHALL be propagated to `HtmlToMarkdownConverter` at construction time via the `extraction_config` dictionary.

#### Scenario: config-passed-to-converter
- **WHEN** `HtmlToMarkdownConverter` is instantiated by the pipeline
- **THEN** `extraction_config.infobox_field_handlers` SHALL be passed from the strategy file
- **THEN** the converter SHALL apply the handlers during infobox conversion

### Requirement: 注册表 ID 清单同步
The system SHALL 在 AGENTS.md 的治理约束中维护当前注册 ID 清单作为快速参考。该清单 SHALL 仅为人眼快速参考，不替代 `_STRATEGY_REGISTRY` 作为权威来源。
