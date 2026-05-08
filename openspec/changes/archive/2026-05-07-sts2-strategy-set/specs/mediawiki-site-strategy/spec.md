# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-site-strategy`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认更新 content_profile 可用策略 ID 表格，追加 StS2 策略集引用

## 规范真源声明

- 本文件是 `mediawiki-site-strategy` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

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
| `discovery_strategy` | `allpages` | `allpages`, `category_members` |
| `content_acquisition` | `wikitext_only` | `wikitext_only`, `hybrid_wikitext_plus_rendered` |
| `link_resolver` | `exact_title_match` | `exact_title_match`, `short_name_with_cross_namespace` |
| `template_processor` | `simple_substitution` | `simple_substitution`, `structured_with_lua_fallback` |
| `list_page_assembler` | `frontmatter_driven` | `frontmatter_driven`, `hybrid_frontmatter_and_rendered` |

**Note**: Strategy IDs for complex sites like StS2 (`category_members`, `hybrid_wikitext_plus_rendered`, `short_name_with_cross_namespace`, `structured_with_lua_fallback`, `hybrid_frontmatter_and_rendered`) are registered in this change. Future changes may add additional strategy IDs (e.g., auto-detected profiles in Change 3).

#### Scenario: content_profile absent, defaults used

- **WHEN** the strategy file has no `api.content_profile` field
- **THEN** the pipeline SHALL compose all default strategy implementations
- **AND** the extraction behavior SHALL be identical to the current (pre-refactoring) behavior

#### Scenario: content_profile partially specified

- **WHEN** `api.content_profile` specifies only `discovery_strategy: "category_members"`
- **THEN** the discovery strategy SHALL use the `category_members` implementation
- **AND** all unspecified concerns SHALL use their default implementations

#### Scenario: content_profile fully specified with StS2 strategies

- **WHEN** `api.content_profile` explicitly specifies all five StS2 strategy IDs
- **THEN** the pipeline SHALL compose the StS2 strategy implementations
- **AND** the extraction behavior SHALL be optimized for slaythespire.wiki.gg (ns=3000)

#### Scenario: Unknown strategy ID

- **WHEN** `api.content_profile` specifies an unknown strategy ID (e.g., `discovery_strategy: "unknown_strategy"`)
- **THEN** the pipeline SHALL log a warning and use the default implementation for that concern
- **AND** the pipeline SHALL NOT fail

### Requirement: capabilities 字段引用

The system SHALL document that `api.capabilities` is the list of API capabilities the strategy declares as available. The declaration SHALL use the controlled vocabulary defined in `mediawiki-api-extraction` spec.

The `capabilities` field SHALL be checked by the pipeline's `validate_api_config` to ensure the strategy's declared capabilities cover the union of `required_capabilities` from all composed strategies.

#### Scenario: Capabilities reference validation for StS2

- **WHEN** a strategy declares `api.capabilities: [page_list, category_lookup, wikitext_parse, html_parse, imageinfo_query]`
- **AND** the selected StS2 strategies require `{page_list, category_lookup, wikitext_parse, html_parse, imageinfo_query}`
- **THEN** validation SHALL pass

#### Scenario: Capabilities subset validation for StS2

- **WHEN** a strategy declares `api.capabilities: [page_list, category_lookup, wikitext_parse]` (missing `html_parse` and `imageinfo_query`)
- **AND** the selected `HybridAcquisitionStrategy` requires `{wikitext_parse, html_parse, imageinfo_query}`
- **THEN** validation SHALL fail with missing capabilities reported
