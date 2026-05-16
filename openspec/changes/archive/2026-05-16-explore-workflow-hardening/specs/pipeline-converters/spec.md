# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: `HtmlToMarkdownConverter` 移除 StS 硬编码；`wiki_domain` 参数化；cleanup selector 和 image filter 从 `extraction` 配置段读取

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: domain-parameterization

`HtmlToMarkdownConverter.__init__` SHALL accept `wiki_domain` as a required parameter and SHALL NOT default to any specific domain name.

#### Scenario: domain-required

- **WHEN** `HtmlToMarkdownConverter` is instantiated without a `wiki_domain` argument
- **THEN** the constructor SHALL raise a `TypeError`
- **THEN** no default value (`"slaythespire.wiki.gg"` or any other) SHALL be applied

#### Scenario: domain-explicit

- **WHEN** `HtmlToMarkdownConverter(wiki_domain="example.wiki.gg")` is instantiated
- **THEN** `self.wiki_domain` SHALL be `"example.wiki.gg"`
- **THEN** all link normalization SHALL use the provided domain

#### Scenario: domain-from-strategy

- **WHEN** the converter is instantiated by pipeline code (Phase B/C) or standalone extraction
- **THEN** `wiki_domain` SHALL be read from the strategy's `api.base_url` (extracted hostname) or `domain` field
- **THEN** the pipeline SHALL pass `wiki_domain` to the converter constructor explicitly

### Requirement: config-driven-cleanup

`HtmlToMarkdownConverter` SHALL read cleanup selectors and image filter patterns from an `extraction_config` dictionary passed at construction time, rather than from hardcoded selector strings.

#### Scenario: cleanup-from-extraction-config

- **WHEN** `HtmlToMarkdownConverter` is instantiated with `extraction_config` containing `cleanup_selectors` list
- **THEN** `self._REMOVAL_SELECTORS` SHALL be set from `cleanup_selectors`
- **THEN** if `cleanup_selectors` is absent or empty, a default set SHALL be used: `(".mw-editsection", ".toc", "#toc", ".hatnote")`

#### Scenario: image-filter-from-extraction-config

- **WHEN** `extraction_config` contains `image_filtering.skip_patterns` list
- **THEN** `clean_html()` SHALL remove `<img>` elements whose `src` attribute matches any pattern in the list
- **THEN** if `image_filtering.skip_patterns` is absent or empty, no image filtering SHALL be applied (no hardcoded patterns)
- **THEN** no StS2-specific patterns (`StS2_Bg`, `StS2_Frame`, etc.) SHALL be hardcoded in the converter

#### Scenario: strategy-passes-extraction-config

- **WHEN** a strategy file defines `extraction.cleanup_selectors` and `extraction.image_filtering.skip_patterns`
- **THEN** the pipeline SHALL pass these values to `HtmlToMarkdownConverter` at instantiation
- **THEN** the converter SHALL apply the configured cleanup without any site-specific hardcoded overrides

#### Scenario: sts-backward-compatibility

- **WHEN** the slaythespire.wiki.gg strategy provides `extraction.cleanup_selectors` and `extraction.image_filtering.skip_patterns` that replicate the previously hardcoded StS2 rules
- **THEN** the converter's output for StS pages SHALL be identical to the pre-change output
