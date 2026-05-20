# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-cli-entry`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: `--phase` 参数重构，新增 `--discovery` 参数，废弃 `homepage` 和单字母 phase 值

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: cli-subcommand-routing

CLI 入口 SHALL 支持子命令路由：`pipeline`（默认）、`fetch`、`reprocess`、`fix-links`、`reconvert`。

The `pipeline` subcommand SHALL accept the new `--discovery` parameter.

### Requirement: pipeline-discovery-parameter

The `pipeline` subcommand SHALL accept `--discovery` with choices `auto`, `allpages`, `homepage`. The default value SHALL be `auto`.

#### Scenario: discovery-parameter-default

- **WHEN** `python3 -m scripts.mediawiki-api-extract <url> --strategy <path> --output <dir>` is called without `--discovery`
- **THEN** `--discovery` SHALL default to `auto`
- **AND** the orchestrator SHALL resolve the actual strategy based on strategy config

#### Scenario: discovery-parameter-explicit

- **WHEN** `python3 -m scripts.mediawiki-api-extract <url> --strategy <path> --output <dir> --discovery homepage` is called
- **THEN** the orchestrator SHALL use homepage discovery regardless of strategy config

### Requirement: phase-parameter-deprecation

The `--phase` parameter SHALL support legacy values with deprecation warnings.

Accepted values SHALL be:
- `all` (default): run discovery + extract + assemble
- `extract`: run extract only
- `assemble`: run assemble only
- `homepage` (deprecated): mapped to `--discovery homepage --phase all` with warning
- `A` (deprecated): mapped to skip discovery, equivalent to extract
- `B` (deprecated): mapped to `extract`
- `C` (deprecated): mapped to `assemble`

#### Scenario: deprecated-homepage-warning

- **WHEN** `--phase homepage` is specified
- **THEN** the CLI SHALL emit: `"DEPRECATED: --phase homepage is deprecated. Use --discovery homepage instead."`
- **AND** continue with homepage discovery + full pipeline

#### Scenario: deprecated-A-warning

- **WHEN** `--phase A` is specified
- **THEN** the CLI SHALL emit: `"DEPRECATED: --phase A is deprecated. Use --phase extract with --discovery <strategy>."`
- **AND** continue with mapped behavior

#### Scenario: deprecated-B-warning

- **WHEN** `--phase B` is specified
- **THEN** the CLI SHALL emit: `"DEPRECATED: --phase B is deprecated. Use --phase extract instead."`
- **AND** continue with mapped behavior

#### Scenario: deprecated-C-warning

- **WHEN** `--phase C` is specified
- **THEN** the CLI SHALL emit: `"DEPRECATED: --phase C is deprecated. Use --phase assemble instead."`
- **AND** continue with mapped behavior

#### Scenario: phase-all-with-discovery

- **WHEN** `--phase all --discovery homepage` is specified
- **THEN** the pipeline SHALL run homepage discovery + extract + assemble
- **AND** no deprecation warning SHALL be emitted

### Requirement: chrome-agent-cli-integration

The `chrome-agent crawl` command (in `scripts/chrome-agent-cli.mjs`) SHALL pass `--discovery` to the MediaWiki pipeline based on the strategy configuration.

When the strategy has `api.homepage`, the CLI SHALL pass `--discovery homepage`. Otherwise, it SHALL pass `--discovery allpages` (or omit for auto default).

#### Scenario: crawl-with-homepage-strategy

- **WHEN** `chrome-agent crawl https://bindingofisaacrebirth.wiki.gg/` is called
- **AND** the strategy has `api.homepage` defined
- **THEN** the CLI SHALL spawn the pipeline with `--discovery homepage`
- **AND** the pipeline SHALL use homepage discovery

#### Scenario: crawl-without-homepage-strategy

- **WHEN** `chrome-agent crawl <url>` is called
- **AND** the strategy does NOT have `api.homepage` defined
- **THEN** the CLI SHALL spawn the pipeline with `--discovery allpages` or omit the flag (auto default)
