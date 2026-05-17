# site-strategy-template Specification

## Purpose
TBD - created by archiving change template-content-profile-and-strategy-fixes. Update Purpose after archive.
## Requirements
### Requirement: template-content-profile-recommendations
平台模板的 `api` 对象 SHALL 包含 `content_profile` 字段，提供该平台变体的推荐策略 ID 组合。这些值为推荐默认值，用户在 scaffold 确认时可覆盖。

各模板推荐值：

| 模板 | discovery | acquisition | link_resolver | template_processor | assembler |
|------|-----------|-------------|---------------|--------------------|-----------|
| `mediawiki.yaml` | `allpages` | `wikitext_only` | `exact_title_match` | `simple_substitution` | `frontmatter_driven` |
| `mediawiki-fandom.yaml` | `category_members` | `html_rendered` | `short_name_with_cross_namespace` | `fandom_infobox` | `hybrid_frontmatter_and_rendered` |
| `mediawiki-wiki-gg.yaml` | `allpages` | `html_rendered` | `exact_title_match` | `structured_with_lua_fallback` | `hybrid_frontmatter_and_rendered` |

#### Scenario: fandom-template-has-content-profile
- **WHEN** 加载 `mediawiki-fandom.yaml` 模板
- **THEN** `api.content_profile` 包含 `discovery_strategy: "category_members"`、`content_acquisition: "html_rendered"`、`link_resolver: "short_name_with_cross_namespace"`、`template_processor: "fandom_infobox"`、`list_page_assembler: "hybrid_frontmatter_and_rendered"`

#### Scenario: standard-mediawiki-template-uses-defaults
- **WHEN** 加载 `mediawiki.yaml` 模板
- **THEN** `api.content_profile` 各维度值与 `DEFAULT_STRATEGIES` 一致

#### Scenario: wiki-gg-template-discovery
- **WHEN** loading `mediawiki-wiki-gg.yaml`
- **THEN** `api.content_profile.discovery_strategy` SHALL be `"allpages"`
- **AND** `api.content_profile.content_acquisition` SHALL be `"html_rendered"`
- **AND** `api.content_profile.link_resolver` SHALL be `"exact_title_match"`

### Requirement: template-rate-limit-defaults
需要限速的 MediaWiki 平台模板 SHALL 在 `api.rate_limit` 中提供默认 tier 引用。

| 模板 | rate_limit.tier |
|------|----------------|
| `mediawiki.yaml` | 无（低保护站点通常不限速） |
| `mediawiki-fandom.yaml` | `strict` |
| `mediawiki-wiki-gg.yaml` | `strict` |

站点策略文件可覆盖此值为其他 tier 名称或完整 rate_limit 配置。

#### Scenario: fandom-template-has-strict-tier
- **WHEN** 加载 `mediawiki-fandom.yaml` 模板
- **THEN** `api.rate_limit.tier` 为 `"strict"`

#### Scenario: wiki-gg-template-has-strict-tier
- **WHEN** 加载 `mediawiki-wiki-gg.yaml` 模板
- **THEN** `api.rate_limit.tier` 为 `"strict"`

### Requirement: template-no-static-capabilities
平台模板 SHALL NOT 包含 `capabilities` 字段。capabilities 由 scaffold generator 通过 `derive_capabilities()` 函数从 content_profile 动态推导。

#### Scenario: template-without-capabilities
- **WHEN** 加载任意 MediaWiki 模板
- **THEN** `api` 对象中不存在 `capabilities` 键，或其值为空列表 `[]`

### Requirement: template-image-filtering

Platform templates SHALL optionally include `extraction.image_filtering.skip_patterns` for wiki.gg sites. The `mediawiki-wiki-gg.yaml` template SHALL define the following default patterns:

```yaml
extraction:
  image_filtering:
    skip_patterns:
      - "Font_TeamMeat"
      - "Dlc_.*indicator"
```

#### Scenario: wiki-gg-template-has-image-filtering
- **WHEN** loading `mediawiki-wiki-gg.yaml` template
- **THEN** `extraction.image_filtering.skip_patterns` SHALL contain `"Font_TeamMeat"` and `"Dlc_.*indicator"`
- **THEN** these patterns SHALL be passed to `HtmlToMarkdownConverter.convert_images_to_md()` as `skip_patterns`

#### Scenario: fandom-template-no-image-filtering
- **WHEN** loading `mediawiki-fandom.yaml` template
- **THEN** `extraction.image_filtering` MAY be absent or empty
- **THEN** no default image filtering SHALL be applied for Fandom sites

#### Scenario: standard-mediawiki-no-image-filtering
- **WHEN** loading `mediawiki.yaml` template
- **THEN** `extraction.image_filtering` MAY be absent or empty

### Requirement: template-extraction-cleanup-selectors

The `mediawiki-wiki-gg.yaml` template SHALL include default `extraction.cleanup_selectors`:

```yaml
extraction:
  cleanup_selectors:
    - ".mw-editsection"
    - ".toc"
    - "#toc"
    - ".hatnote"
    - ".nav-box"
    - ".nav-header"
```

#### Scenario: nav-header-in-cleanup-selectors
- **WHEN** loading `mediawiki-wiki-gg.yaml`
- **THEN** `extraction.cleanup_selectors` SHALL include `.nav-header`
- **AND** `extraction.cleanup_selectors` SHALL include `.nav-box`
- **THEN** these selectors SHALL be passed to the converter's element removal step

### Requirement: template-infobox-field-handlers-default

The `mediawiki-wiki-gg.yaml` template SHALL NOT include `infobox_field_handlers` by default. These handlers are site-specific and SHALL be configured in individual `sites/strategies/<domain>/strategy.md` files.

#### Scenario: template-without-field-handlers
- **WHEN** loading `mediawiki-wiki-gg.yaml`
- **THEN** `extraction.infobox_field_handlers` SHALL be absent or an empty map
- **THEN** each site's strategy file SHALL define its own `infobox_field_handlers` as needed

#### Scenario: isaac-wiki-defines-field-handlers
- **WHEN** loading `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
- **THEN** `extraction.infobox_field_handlers` SHALL be present with site-specific handler mappings
