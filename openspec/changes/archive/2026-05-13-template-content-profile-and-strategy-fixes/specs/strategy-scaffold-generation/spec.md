# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-scaffold-generation`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: new
- 用户确认摘要: 合并逻辑从 `or` 覆盖改为分层合并；capabilities 由动态推导生成；api_discovery 的 capabilities 不再传入策略文件

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: layered-api-merge
scaffold generator 的 API 对象组装 SHALL 使用分层合并逻辑，替代当前的 `api_config or template_data.get("api")` 单一覆盖：

- **Layer 1 — 模板声明性字段**：`platform_variant`、`content_profile`、`rate_limit` 从模板的 `api` 对象复制到 scaffold
- **Layer 2 — 探测事实性字段**：`base_url`、`version` 从 api_config 覆盖到 scaffold
- **Layer 3 — 动态推导字段**：`capabilities` 通过 `derive_capabilities()` 从 content_profile 生成

`api_config` 中的 `capabilities`、`site_name`、`lang`、`pages`、`articles` 等 siteinfo 字段 SHALL NOT 写入策略文件。

#### Scenario: api-config-present-template-has-profile
- **WHEN** api_config 返回 `{base_url: "https://example.com/api.php", version: "1.43", capabilities: ["read","parse"]}` 且模板包含 `content_profile` 和 `platform_variant`
- **THEN** scaffold 的 `api.base_url` 为 `"https://example.com/api.php"`，`api.version` 为 `"1.43"`，`api.content_profile` 来自模板，`api.capabilities` 由 `derive_capabilities()` 生成，不包含 `["read","parse"]`

#### Scenario: api-config-absent
- **WHEN** api_config 为 None（API 探测失败）
- **THEN** scaffold 的 `api` 完全来自模板，`base_url` 留空字符串

#### Scenario: template-has-no-api
- **WHEN** 模板的 `api` 字段为 null（如 `custom.yaml`）
- **THEN** scaffold 的 `api` 仅包含 api_config 的事实性字段，无 content_profile，capabilities 使用默认值推导

### Requirement: api-discovery-capabilities-isolation
`api_discovery.py` 的 `_probe_mediawiki()` 返回结果 SHALL 继续包含 `capabilities` 字段（用于信息展示），但 scaffold generator SHALL NOT 将 api_config 的 capabilities 传递到策略文件的 `api.capabilities` 字段。

#### Scenario: discovery-returns-capabilities-but-scaffold-ignores
- **WHEN** api_discovery 返回 `capabilities: ["read", "parse", "query"]`
- **THEN** 该值在 explore 输出中可见（JSON 输出的 api_discovery 部分），但生成的 scaffold 策略文件的 `api.capabilities` 不包含这些值

### Requirement: scaffold-generates-derived-capabilities
scaffold generator 在组装 API 对象时 SHALL 调用 `derive_capabilities()` 函数生成 `api.capabilities` 字段。

#### Scenario: fandom-scaffold-capabilities
- **WHEN** scaffold 使用 `mediawiki-fandom.yaml` 模板（content_profile 含 `html_rendered`）
- **THEN** 生成的 `api.capabilities` 包含 `["category_lookup", "html_parse", "page_list"]`

#### Scenario: default-scaffold-capabilities
- **WHEN** scaffold 使用 `mediawiki.yaml` 模板（content_profile 含默认值）
- **THEN** 生成的 `api.capabilities` 包含 `["category_lookup", "page_list", "wikitext_parse"]`
