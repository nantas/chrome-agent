# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认现有策略文件需要按照新治理规则进行维护

## 规范真源声明

- 本文件是 `site-strategy` 在本次 change 中的行为规范真源

## MODIFIED Requirements

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
