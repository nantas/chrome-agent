# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy-template`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 wiki.gg 平台模板增加 `image_filtering.skip_patterns` 配置

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: template-content-profile-recommendations

The existing content profile recommendations SHALL be updated for `mediawiki-wiki-gg.yaml`:

```yaml
api:
  platform: mediawiki
  platform_variant: wiki-gg
  content_profile:
    discovery_strategy: "allpages"
    content_acquisition: "html_rendered"
    link_resolver: "exact_title_match"
    template_processor: "structured_with_lua_fallback"
    list_page_assembler: "hybrid_frontmatter_and_rendered"
```

#### Scenario: wiki-gg-template-discovery
- **WHEN** loading `mediawiki-wiki-gg.yaml`
- **THEN** `api.content_profile.discovery_strategy` SHALL be `"allpages"`
- **AND** `api.content_profile.content_acquisition` SHALL be `"html_rendered"`
- **AND** `api.content_profile.link_resolver` SHALL be `"exact_title_match"`

## ADDED Requirements

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
- **THEN** `extraction.infoxbox_field_handlers` SHALL be absent or an empty map
- **THEN** each site's strategy file SHALL define its own `infobox_field_handlers` as needed

#### Scenario: isaac-wiki-defines-field-handlers
- **WHEN** loading `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
- **THEN** `extraction.infoxbox_field_handlers` SHALL be present with site-specific handler mappings
