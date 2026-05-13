# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: new
- 用户确认摘要: 修正现有站点策略文件的数据问题（tier 引用、引擎引用、variant 声明、registry 索引缺失）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

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
