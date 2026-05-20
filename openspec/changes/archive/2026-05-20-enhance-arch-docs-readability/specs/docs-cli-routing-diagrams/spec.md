# Specification Delta

## Capability 对齐（已确认）

- Capability: `docs-cli-routing-diagrams`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 为 CLI 参考文档增加命令路由决策树和管线阶段流程图

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: command-routing-decision-tree

The document `docs/architecture/04-cli-reference.md` SHALL include an ASCII decision tree diagram showing how the CLI routes user commands to backend execution paths.

The decision tree SHALL illustrate:
- `explore <url>` → `scripts/explore/main.py` (deep discovery or platform analysis)
- `fetch <url>` → `selectFetcher()` → Scrapling / MediaWiki API
- `crawl <url>` → `findStrategy()` → `api.platform=mediawiki` ? `python3 -m scripts.pipeline` : Scrapling
- `scrape <url>` → `runScraplingScrape()`
- Each branch SHALL show the relevant code entry point (function name + line number)

#### Scenario: routing-decision-tree-navigation

- **WHEN** a user needs to understand which backend a command triggers
- **THEN** they SHALL visually trace the decision path
- **AND** the diagram SHALL appear in the "概述" section

### Requirement: pipeline-phase-flow-diagram

The document `docs/architecture/04-cli-reference.md` SHALL include an ASCII flowchart showing how `--discovery` and `--phase` CLI parameters affect which pipeline phases execute.

The flowchart SHALL illustrate:
- `--discovery auto|allpages|homepage` → discovery phase selection
- `--phase all|discover|fetch|convert|assemble` → execution phase selection
- The default path (`--discovery auto --phase all`)
- The resume path (`--from-manifest` → skip discovery)

#### Scenario: phase-flow-diagram-readability

- **WHEN** a user is selecting pipeline parameters
- **THEN** they SHALL understand which phases will execute for any parameter combination
- **AND** the diagram SHALL appear near the `--phase` and `--discovery` parameter documentation
