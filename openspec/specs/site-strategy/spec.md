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

#### Scenario: registry-reflects-bgg-engine-change
- **WHEN** BGG 策略的 engine_preference 更新为 cloakbrowser-fetch
- **THEN** registry.json 中 BGG 条目无 engine_preference 相关字段需更新（registry 不存储 engine 信息）

### Requirement: neonabyss.fandom.com 策略文件 content_profile 修正
The system SHALL 修正 `sites/strategies/neonabyss.fandom.com/strategy.md` 的 `api.content_profile` 引用，使其符合 `_STRATEGY_REGISTRY` 的约束。

需要修正的两个字段：

| 字段 | 当前值 | 目标值 | 原因 |
|------|--------|--------|------|
| `link_resolver` | `short_name` | `short_name_with_cross_namespace` | `short_name` 未注册；`short_name_with_cross_namespace` 是语义最接近的已注册实现 |
| `template_processor` | `fandom_infobox` | `fandom_infobox`（保持） | `fandom_infobox` 是本 change 中新增注册的 ID |

此外，SHALL 增加 `api.platform_variant: fandom` 字段。

#### Scenario: 修正后的 content_profile
- **WHEN** neonabyss.fandom.com/strategy.md 的 content_profile 被 pipeline 读取
- **THEN** 以下引用 SHALL 在 `_STRATEGY_REGISTRY` 中全部合法：
  - `discovery_strategy: "category_members"` → 已注册
  - `content_acquisition: "html_rendered"` → 已注册
  - `link_resolver: "short_name_with_cross_namespace"` → 已注册（新修正）
  - `template_processor: "fandom_infobox"` → 本 change 中注册
  - `list_page_assembler: "hybrid_frontmatter_and_rendered"` → 已注册
- **AND** platform_variant 字段存在且值为 `fandom`

### Requirement: 现有策略文件排查
The system SHALL 扫描所有 `sites/strategies/*/strategy.md` 文件，检查是否存在其他引用未注册 content_profile ID 的情况。

如果发现，按照以下优先级处理：
1. 如果已有语义等价的已注册 ID → 替换为已注册 ID
2. 如果没有等价 ID → 创建对应的实现类并注册（复杂度高时转入后续 change）

#### Scenario: 策略文件扫描
- **WHEN** grep `sites/strategies/*/strategy.md` 的 `content_profile` 字段
- **THEN** 所有引用的 ID SHALL 在 `_STRATEGY_REGISTRY` 中存在
- **AND** 不存在的 ID SHALL 被记录为待修复项

### Requirement: YAML frontmatter 新增字段
The system SHALL 在策略文件的 `api` 对象中增加以下可选字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `platform_variant` | enum | no | MediaWiki 平台变体标识，当前取值：`standard`（默认）、`fandom`、`wiki-gg` |

### Requirement: content_profile ID 引用约束
The system SHALL 对 `api.content_profile` 各字段的 value 施加引用完整性约束。

`content_profile` 的每个字段 SHALL 只能引用 `_STRATEGY_REGISTRY` 中该维度已注册的 ID。

允许值（当前注册 ID 清单，来自 `_STRATEGY_REGISTRY`）：

| 维度 | 合法 ID |
|--------|----------|
| `discovery_strategy` | `allpages`, `category_members` |
| `content_acquisition` | `wikitext_only`, `hybrid_wikitext_plus_rendered`, `html_rendered` |
| `link_resolver` | `exact_title_match`, `short_name_with_cross_namespace` |
| `template_processor` | `simple_substitution`, `structured_with_lua_fallback` |
| `list_page_assembler` | `frontmatter_driven`, `hybrid_frontmatter_and_rendered` |

引用未注册 ID 的策略文件 SHALL 被视为无效文件。

#### Scenario: 引用已注册 ID
- **WHEN** 策略文件指定 `content_profile.link_resolver: "exact_title_match"`
- **THEN** pipeline SHALL 正常使用 `ExactTitleLinkResolver`
- **AND** SHALL 不发出任何警告

#### Scenario: 引用未注册 ID
- **WHEN** 策略文件指定 `content_profile.link_resolver: "short_name"`
- **THEN** `short_name` 在 registry 中不存在（仅有 `short_name_with_cross_namespace`）
- **AND** pipeline SHALL 拒绝执行并返回 `EXIT_STRATEGY_ERROR`
- **AND** 错误信息 SHALL 指出: `Strategy ID 'short_name' not registered in 'link_resolver'. Did you mean 'short_name_with_cross_namespace'?`

#### Scenario: content_profile 不完整
- **WHEN** 策略文件指定了部分 `content_profile` 字段（如仅指定 `discovery_strategy` 和 `content_acquisition`）
- **THEN** 未指定的字段 SHALL 使用对应的默认 ID（来自 `DEFAULT_STRATEGIES`）
- **AND** 仅对已指定的字段执行 ID 引用完整性校验

### Requirement: 注册表 ID 清单同步
The system SHALL 在 AGENTS.md 的治理约束中维护当前注册 ID 清单作为快速参考。该清单 SHALL 仅为人眼快速参考，不替代 `_STRATEGY_REGISTRY` 作为权威来源。

#### Scenario: AGENTS.md ID 参考表
- **WHEN** `_STRATEGY_REGISTRY` 中的 ID 被新增或移除
- **THEN** AGENTS.md 中的 ID 参考表 SHALL 同步更新
- **AND** 如果 AGENTS.md 参考表与代码不一致，以代码中的 `_STRATEGY_REGISTRY` 为准

