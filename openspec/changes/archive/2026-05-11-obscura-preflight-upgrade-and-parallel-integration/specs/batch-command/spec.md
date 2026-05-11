# Specification Delta

## Capability 对齐（已确认）

- Capability: `batch-command`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 确认所有 6 项 capability

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: batch-command-syntax

The system SHALL provide a `chrome-agent batch <urls...>` subcommand that fetches multiple URLs in parallel using the Obscura serve pool.

#### Scenario: batch-basic-usage
- **WHEN** a user runs `chrome-agent batch https://a.com https://b.com https://c.com --workers 3`
- **THEN** the system SHALL start a 3-worker Obscura serve pool, fetch all 3 URLs concurrently, stop the serve pool, and output the results

#### Scenario: batch-with-markdown
- **WHEN** a user runs `chrome-agent batch <urls...> --markdown`
- **THEN** the system SHALL run the Markdown conversion pipeline on the fetched HTML, producing .md files alongside HTML

#### Scenario: batch-with-timeout
- **WHEN** a user provides `--timeout 30`
- **THEN** the system SHALL pass the timeout to each individual `obscura fetch` call

### Requirement: batch-command-fallback

The batch command SHALL fall back to Scrapling serial fetch when Obscura is unavailable.

#### Scenario: batch-obscura-unavailable
- **WHEN** Obscura preflight fails or the serve pool cannot start
- **THEN** the system SHALL fall back to running `scrapling extract get <url>` serially for each URL and report the fallback in the output summary
