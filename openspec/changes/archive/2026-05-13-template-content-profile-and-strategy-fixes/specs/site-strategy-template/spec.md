# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy-template`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: new
- 用户确认摘要: 模板需补全 content_profile 推荐值和 rate_limit.tier 默认值；capabilities 字段改为动态推导，不再手动维护

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: template-content-profile-recommendations
平台模板的 `api` 对象 SHALL 包含 `content_profile` 字段，提供该平台变体的推荐策略 ID 组合。这些值为推荐默认值，用户在 scaffold 确认时可覆盖。

各模板推荐值：

| 模板 | discovery | acquisition | link_resolver | template_processor | assembler |
|------|-----------|-------------|---------------|--------------------|-----------|
| `mediawiki.yaml` | `allpages` | `wikitext_only` | `exact_title_match` | `simple_substitution` | `frontmatter_driven` |
| `mediawiki-fandom.yaml` | `category_members` | `html_rendered` | `short_name_with_cross_namespace` | `fandom_infobox` | `hybrid_frontmatter_and_rendered` |
| `mediawiki-wiki-gg.yaml` | `category_members` | `hybrid_wikitext_plus_rendered` | `short_name_with_cross_namespace` | `structured_with_lua_fallback` | `hybrid_frontmatter_and_rendered` |

#### Scenario: fandom-template-has-content-profile
- **WHEN** 加载 `mediawiki-fandom.yaml` 模板
- **THEN** `api.content_profile` 包含 `discovery_strategy: "category_members"`、`content_acquisition: "html_rendered"`、`link_resolver: "short_name_with_cross_namespace"`、`template_processor: "fandom_infobox"`、`list_page_assembler: "hybrid_frontmatter_and_rendered"`

#### Scenario: standard-mediawiki-template-uses-defaults
- **WHEN** 加载 `mediawiki.yaml` 模板
- **THEN** `api.content_profile` 各维度值与 `DEFAULT_STRATEGIES` 一致

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
