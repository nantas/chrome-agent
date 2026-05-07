# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-site-strategy`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户已通过对话确认扩展 `api` 字段，新增 `content_profile` schema 用于声明策略覆盖选择。本次只追加，不修改或删除已有字段。

## 规范真源声明

- 本文件是 `mediawiki-site-strategy` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本次只追加 MODIFIED Requirements，不修改或删除任何已有 Requirements

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
