# Specification Delta

## Capability 对齐（已确认）

- Capability: `cli`
- 来源: `proposal.md` / 用户授权“按照你建议的方案创建 change”。
- 变更类型: modified
- 用户确认摘要: 落实已讨论的抽取完整性修复范围；不自动恢复全站抓取。

## 规范真源声明

本文件是该 capability 在本 change 中的行为规范真源；design/tasks/verification SHALL 以此为依据，页面回写不得替代 spec delta。

## ADDED Requirements

### Requirement: configurable-mediawiki-pipeline-timeout
MediaWiki crawl SHALL accept `--pipeline-timeout-seconds <n>`, a positive integer from 1 through 86400, defaulting to 600. It SHALL set the timeout for each MediaWiki discovery or extraction child process in milliseconds, without changing per-request API timeouts or other backends. Invalid values SHALL fail before starting discovery/extraction. CLI help and reference SHALL document units, default and scope.

#### Scenario: long-extraction
- **WHEN** MediaWiki crawl specifies `--pipeline-timeout-seconds 3600`
- **THEN** the child SHALL receive a 3,600,000 ms timeout instead of the fixed ten-minute limit.

#### Scenario: default-and-invalid-values
- **WHEN** the option is omitted
- **THEN** the timeout SHALL remain 600,000 ms.
- **WHEN** the option is zero, negative, fractional, nonnumeric, missing its value or greater than 86400
- **THEN** argument validation SHALL fail before any discovery/extraction process starts.

#### Scenario: timeout-remains-loud
- **WHEN** the child exceeds its configured timeout
- **THEN** the result SHALL be failure with requested mode, configured timeout, process error/signal and upstream status diagnostics
- **AND** it SHALL NOT become partial success or fall back to Scrapling, and the existing internal-failure handoff SHALL remain available.

#### Scenario: confirmation-gate-preserved
- **WHEN** a custom timeout is provided to discovery-only or an unconfirmed crawl
- **THEN** it SHALL NOT bypass the existing discovery/confirmation gate.
