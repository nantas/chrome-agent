# Specification Delta

## Capability 对齐（已确认）

- Capability: `site-strategy`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户同意策略文件 schema 需要扩展 content_profile ID 引用完整性约束和 platform_variant 声明

## 规范真源声明

- 本文件是 `site-strategy` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

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
