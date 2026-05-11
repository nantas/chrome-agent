# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrape-parallel-mode`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 确认所有 6 项 capability

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: scrape-parallel-flag

The scrape command SHALL support a `--parallel` flag. When set, the scrape workflow SHALL use the Obscura serve pool for Phase 2 content retrieval instead of Scrapling serial fetch.

#### Scenario: scrape-parallel-enabled
- **WHEN** `scrape <url> --parallel --workers 5`
- **THEN** the system SHALL execute the standard Scrapling-based traversal loop (Phase 1) to discover and collect URLs, then use Obscura serve pool with 5 workers for parallel content retrieval, then run Markdown conversion (Phase 3)

#### Scenario: scrape-parallel-fallback
- **WHEN** `scrape --parallel` is specified but Obscura preflight fails
- **THEN** the system SHALL fall back to the standard Scrapling serial scrape path and report the fallback

### Requirement: scrape-parallel-workers-flag

The scrape command SHALL support a `--workers <n>` flag to control the Obscura serve pool size. The default SHALL be 5, and the maximum SHALL be 30.

#### Scenario: scrape-parallel-workers-custom
- **WHEN** `scrape <url> --parallel --workers 10`
- **THEN** the system SHALL start a 10-worker Obscura serve pool for parallel content retrieval
