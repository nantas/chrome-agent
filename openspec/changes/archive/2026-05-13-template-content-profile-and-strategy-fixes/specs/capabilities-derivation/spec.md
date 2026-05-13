# Specification Delta

## Capability 对齐（已确认）

- Capability: `capabilities-derivation`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: new
- 用户确认摘要: explore 模式中讨论确定——capabilities 由 content_profile ID 动态推导，不应在模板中硬编码

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: derive-capabilities-from-content-profile
系统 SHALL 提供公共函数 `derive_capabilities(content_profile: dict) -> list[str]`，根据 content_profile 中声明的策略 ID，从 `_STRATEGY_REGISTRY` 中对应策略类实例的 `required_capabilities` 属性推导出 pipeline 校验所需的 capabilities 列表。

推导逻辑：
1. 对 `discovery` 和 `content_acquisition` 两个维度，查找 content_profile 中对应的 key（`discovery_strategy` → `discovery`，`content_acquisition` → `content_acquisition`）
2. 实例化对应策略类，读取 `required_capabilities` 属性
3. 取两个维度的并集
4. 如果 content_profile 中未指定某维度，使用 `DEFAULT_STRATEGIES` 中的默认 ID
5. 返回排序后的 capability 字符串列表

#### Scenario: derive-from-fandom-content-profile
- **WHEN** content_profile 为 `{"discovery_strategy": "category_members", "content_acquisition": "html_rendered", "link_resolver": "short_name_with_cross_namespace", "template_processor": "fandom_infobox", "list_page_assembler": "hybrid_frontmatter_and_rendered"}`
- **THEN** 返回 `["category_lookup", "html_parse", "page_list"]`

#### Scenario: derive-from-default-empty-profile
- **WHEN** content_profile 为空 dict `{}`
- **THEN** 使用 DEFAULT_STRATEGIES（allpages + wikitext_only），返回 `["category_lookup", "page_list", "wikitext_parse"]`

#### Scenario: derive-from-hybrid-profile
- **WHEN** content_profile 中 `content_acquisition` 为 `"hybrid_wikitext_plus_rendered"`
- **THEN** capabilities 包含 `["category_lookup", "html_parse", "imageinfo_query", "page_list", "wikitext_parse"]`

### Requirement: derive-capabilities-public-api
`derive_capabilities` 函数 SHALL 通过 `orchestrate.py` 导出为公共 API（与 `STRATEGY_REGISTRY` 同级导出），供 `strategy_scaffold_generator.py` 和其他外部消费者使用。

#### Scenario: import-from-orchestrate
- **WHEN** 外部模块执行 `from scripts.mediawiki_api_extract.pipeline.orchestrate import derive_capabilities`
- **THEN** 函数可用且可正常调用

### Requirement: derive-capabilities-robustness
当 content_profile 引用了不在 `_STRATEGY_REGISTRY` 中的策略 ID 时，`derive_capabilities` SHALL 抛出 `ValueError`，与 `build_pipeline()` 的 hard-fail 校验行为保持一致。

#### Scenario: invalid-strategy-id
- **WHEN** content_profile 中 `discovery_strategy` 为 `"nonexistent_strategy"`
- **THEN** 抛出 `ValueError`，消息包含无效 ID 和可用 ID 列表
