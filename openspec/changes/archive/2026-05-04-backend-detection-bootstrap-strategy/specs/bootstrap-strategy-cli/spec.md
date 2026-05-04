# Specification Delta

## Capability 对齐（已确认）

- Capability: `bootstrap-strategy-cli`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户已通过对话确认，选择 A+C 组合方案：新增 bootstrap-strategy CLI 命令，从同后端已有策略自动派生新站点策略

## 规范真源声明

- 本文件是 `bootstrap-strategy-cli` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 命令接口

The system SHALL expose a `bootstrap-strategy` CLI command with the following interface:

```
chrome-agent bootstrap-strategy <url> --from <existing-domain> [--profile <cleanup-profile>]
```

#### Scenario: 最小参数调用

- **WHEN** the user runs `chrome-agent bootstrap-strategy <target-url> --from <domain>`
- **THEN** the system SHALL validate the `--from` domain has an existing strategy
- **AND** it SHALL generate a new strategy for the target URL's domain based on the reference strategy

#### Scenario: 指定清理 profile

- **WHEN** the user supplies `--profile <name>`
- **THEN** the generated strategy SHALL use the specified cleanup profile in `extraction.cleanup`
- **AND** if the profile does not exist in the reference strategy's cleanup options, the system SHALL warn but proceed

### Requirement: 参考策略验证

Before generating a new strategy, the system SHALL validate that the `--from` domain exists in `sites/strategies/registry.json` and has a readable `strategy.md`.

#### Scenario: 参考策略存在

- **WHEN** `--from` points to a domain with a valid `sites/strategies/<domain>/strategy.md`
- **THEN** the system SHALL read the strategy's YAML frontmatter as the template

#### Scenario: 参考策略不存在

- **WHEN** `--from` points to a domain not present in `registry.json`
- **THEN** the command SHALL return `failure`
- **AND** the result SHALL explain that no strategy exists for the `--from` domain

#### Scenario: 目标域名已存在策略

- **WHEN** the target URL's domain already has an entry in `registry.json`
- **THEN** the command SHALL return `failure`
- **AND** the result SHALL explain that a strategy already exists and bootstrap would overwrite it

### Requirement: 字段适配规则

The system SHALL adapt the reference strategy's frontmatter fields to the new domain.

#### Scenario: Domain 字段替换

- **WHEN** generating a new strategy
- **THEN** the `domain` field SHALL be set to the target URL's hostname

#### Scenario: Description 字段替换

- **WHEN** generating a new strategy
- **THEN** the `description` field SHALL preserve the reference structure but replace the old domain name and game/topic name with the new domain's inferred identity
- **AND** if the description contains a game or topic name placeholder, the system SHALL attempt to extract it from the target page's `<title>` or `#firstHeading`

#### Scenario: URL 相关字段替换

- **WHEN** generating a new strategy
- **THEN** all `url_example` fields in `structure.pages[]` SHALL have their hostname replaced with the new domain
- **AND** `url_pattern` fields SHALL remain unchanged (same backend implies same path structure)

#### Scenario: Extraction 配置继承

- **WHEN** generating a new strategy
- **THEN** `extraction.selectors` SHALL be copied verbatim from the reference strategy
- **AND** `extraction.image_handling` SHALL be copied verbatim
- **AND** `extraction.cleanup` SHALL be copied verbatim unless overridden by `--profile`

#### Scenario: Engine 与保护级别继承

- **WHEN** generating a new strategy
- **THEN** `engine_preference` SHALL be copied verbatim
- **AND** `protection_level` SHALL be copied verbatim
- **AND** `anti_crawl_refs` SHALL be copied verbatim

### Requirement: Markdown body 生成

The system SHALL generate a minimal but complete Markdown body for the bootstrapped strategy.

#### Scenario: Body 包含引导标记

- **WHEN** the strategy is bootstrapped
- **THEN** the Markdown body SHALL contain a header comment indicating it was bootstrapped from the reference domain and the date
- **AND** it SHALL include Overview, Page Structure, Extraction Flow, Known Issues, and Evidence sections
- **AND** the Evidence section SHALL state "Bootstrapped from <ref-domain> on <date>; requires validation"

#### Scenario: Body 不重复 frontmatter

- **WHEN** the Markdown body is generated
- **THEN** it SHALL NOT duplicate frontmatter fields
- **AND** it SHALL expand on operational details not covered by frontmatter

### Requirement: Registry 索引更新

After writing the new strategy file, the system SHALL update `sites/strategies/registry.json` to include the new domain.

#### Scenario: 成功追加条目

- **WHEN** the strategy file is successfully written
- **THEN** a new entry SHALL be appended to `registry.json` `entries` array
- **AND** the entry SHALL contain all required fields: `domain`, `description`, `protection_level`, `page_types`, `pagination`, `entry_points`, `anti_crawl_refs`, `file`
- **AND** `page_types` SHALL be derived from `structure.pages[].type` in the generated frontmatter

#### Scenario: Registry 写入失败

- **WHEN** the strategy file is written but `registry.json` update fails
- **THEN** the command SHALL return `partial_success`
- **AND** the result SHALL indicate that manual registry.json update is required

### Requirement: 输出与结果格式

The `bootstrap-strategy` command SHALL return a result following the existing CLI result format.

#### Scenario: 成功生成

- **WHEN** the strategy is fully generated and registry is updated
- **THEN** the result SHALL be `success`
- **AND** artifacts SHALL include the new `strategy.md` path and the updated `registry.json` path
- **AND** `next_action` SHALL recommend reviewing the strategy and then running `chrome-agent crawl <url>`
