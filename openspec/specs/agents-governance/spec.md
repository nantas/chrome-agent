# agents-governance Specification

## Purpose

Define the governance contract for the repository entry document, workflow routing, engine boundaries, reporting expectations, directory rules, decision records, and the relationship between active workflow governance and superseded historical specs.
## Requirements
### Requirement: AGENTS.md 结构与强制内容

The system SHALL rewrite AGENTS.md as a pure governance document with the following mandatory sections, ordered as specified:

1. **Service Identity**: 声明仓库为"跨仓库网页抓取服务（cross-repo web scraping service）"，定义核心设计原则（Scrapling-first、workflow-driven、read-only by default、证据驱动）
2. **Capability Framework**: 列出仓库对外能力（explore / fetch / crawl）和对内能力（site-strategy / anti-crawl-strategy / engine-registry / output-lifecycle），引用总体规划文档的能力全景图
3. **Governance Rules**: 定义引擎选择策略、工作流路由规则、报告产出规范、认证访问边界
4. **Directory Governance**: 定义每个顶级目录的用途、内容约束和生命周期
5. **Decision Record Governance**: 定义 `docs/decisions/` 中决策记录的命名格式、内容结构和索引规则
6. **Spec and Change Governance**: 定义 `openspec/` 中 spec 与 change 的管理规则，引用 Orbitos Spec Standard v0.3
7. **Reference Index**: 列出仓库内关键文档的索引（规划文档、决策记录、操作手册、spec 目录），不嵌入操作细节

AGENTS.md SHALL NOT contain operational how-to content; such content SHALL reside in `docs/playbooks/`.

#### Scenario: AGENTS.md content separation

- **WHEN** AGENTS.md is read by an agent or operator
- **THEN** the document provides governance-level context (identity, rules, policies) without directing tool-level operations
- **AND** operational procedures (Scrapling usage steps, fallback procedures, evidence collection steps) are accessible via `docs/playbooks/`

#### Scenario: Mandatory sections present

- **WHEN** AGENTS.md is validated against this spec
- **THEN** all seven mandatory sections SHALL be present in the specified order
- **AND** no section SHALL contain operational step-by-step instructions

### Requirement: 服务身份声明

The system SHALL declare chrome-agent as a cross-repo web scraping service with explicitly stated core design principles.

#### Scenario: Identity declaration

- **WHEN** an agent or operator reads the Service Identity section
- **THEN** the section SHALL state that chrome-agent is a "跨仓库网页抓取服务（cross-repo web scraping service）"
- **AND** it SHALL list the four core principles: Scrapling-first, workflow-driven (AGENTS.md + skills), read-only by default for authenticated runs, and evidence-driven reporting

#### Scenario: Scope boundaries

- **WHEN** the identity section defines scope
- **THEN** it SHALL state in-scope activities (webpage content retrieval, frontend debugging, evidence collection, reporting)
- **AND** it SHALL state the current out-of-scope boundary (credential management, large automation framework)

### Requirement: 工作流路由规则

The system SHALL document the two primary workflow types (Content Retrieval and Platform/Page Analysis), their routing triggers, and the mandatory Scrapling preflight that occurs before a Scrapling-first workflow begins execution.

For any workflow path that depends on Scrapling as the first engine family, the system SHALL check Scrapling CLI availability before attempting fetcher selection or content retrieval.

#### Scenario: Content Retrieval routing

- **WHEN** the user gives only a URL, asks to get/read/fetch/extract page content, or wants a concise failure explanation
- **THEN** the workflow SHALL default to Content Retrieval with Scrapling-first path and lightweight verification
- **AND** Scrapling CLI availability SHALL be checked before the first Scrapling step executes

#### Scenario: Platform/Page Analysis routing

- **WHEN** the user prompt contains signals such as 分析, 调试, 证据, 总结经验, 平台, 结构, 抓取规则, or 复现
- **THEN** the workflow SHALL route to Platform/Page Analysis with deeper evidence collection and fallback escalation
- **AND** if the chosen analysis path still starts with Scrapling, the same Scrapling CLI preflight SHALL run before execution

#### Scenario: Mixed signals

- **WHEN** both Content Retrieval and Platform/Page Analysis signals appear
- **THEN** the workflow SHALL prefer Platform/Page Analysis

#### Scenario: Preflight install assurance

- **WHEN** the workflow requires Scrapling and the Scrapling CLI is not available
- **THEN** the system SHALL first ensure the CLI is installed or restored according to the `scrapling-cli-environment` capability
- **AND** it SHALL resume the requested workflow only after CLI availability is re-verified

### Requirement: 引擎选择策略

The system SHALL define a Scrapling-first engine selection strategy with explicit fallback boundaries in AGENTS.md, and that strategy SHALL run only after Scrapling preflight has succeeded or been explicitly declared unavailable.

#### Scenario: Default Scrapling path

- **WHEN** a webpage grabbing task is initiated and Scrapling preflight succeeds
- **THEN** the workflow SHALL start with Scrapling, selecting the appropriate fetcher (`get` for static, `fetch` for SPA, `stealthy-fetch` for protected pages) unless a live-session continuity trigger is already known

#### Scenario: Stop on unresolved preflight failure

- **WHEN** Scrapling preflight cannot make the CLI available
- **THEN** the workflow SHALL stop before claiming it is executing the Scrapling-first path
- **AND** it SHALL report the installation or configuration failure instead of silently falling through to unrelated tools

#### Scenario: Diagnostic fallback to chrome-devtools-mcp

- **WHEN** Scrapling output is incomplete, blocked, visually suspect, or requires DOM/network/console/screenshot/interaction evidence after a successful preflight and Scrapling attempt
- **THEN** the workflow SHALL escalate to chrome-devtools-mcp as the diagnostic and evidence path

#### Scenario: Live-session continuity fallback to chrome-cdp

- **WHEN** the task must continue immediately on an already-open real Chrome tab, or an approved authenticated state cannot be preserved through Scrapling after a successful preflight and Scrapling attempt
- **THEN** the workflow SHALL escalate to repo-local chrome-cdp as the live-session continuity path

### Requirement: 报告产出规范

The system SHALL define minimum reporting requirements per workflow type in AGENTS.md.

#### Scenario: Content Retrieval reporting

- **WHEN** a Content Retrieval task completes
- **THEN** the report SHALL capture at minimum: page title, final URL, Scrapling fetcher path or fallback path, extracted main content or precise failure reason, and one lightweight evidence point when needed

#### Scenario: Platform/Page Analysis reporting

- **WHEN** a Platform/Page Analysis task completes
- **THEN** the report SHALL be saved as a reports/ artifact with: page title and URL, one key content excerpt, one screenshot, one structure clue (DOM or accessibility snapshot), and one interaction outcome if the task includes a flow

#### Scenario: Article-style extraction

- **WHEN** article content is extracted in either workflow
- **THEN** the output SHALL preserve DOM reading order, keep real image source URLs at their original positions using Markdown image syntax, and not replace article images with generic placeholders

### Requirement: 目录结构治理

The system SHALL define the governance rules for each top-level directory in AGENTS.md.

#### Scenario: Directory purpose definition

- **WHEN** the directory governance section is read
- **THEN** each top-level directory (AGENTS.md, openspec/, docs/, reports/, skills/, sites/, configs/, scripts/) SHALL have a defined purpose and content constraint

#### Scenario: docs/ governance

- **WHEN** docs/ structure is defined
- **THEN** the subdirectories SHALL include decisions/ (decision records with naming format YYYY-MM-DD-topic.md), playbooks/ (operational procedures migrated from AGENTS.md), plans/ (implementation planning documents), and setup/ (environment configuration)

#### Scenario: openspec/ governance

- **WHEN** openspec/ structure is defined
- **THEN** it SHALL include changes/ (active and archived changes under Orbitos Spec Standard v0.3 workflow) and specs/ (frozen capability specifications as behavioral SSOT)

### Requirement: 决策记录治理

The system SHALL define the governance rules for decision records in AGENTS.md.

#### Scenario: Decision record format

- **WHEN** a new decision record is created in docs/decisions/
- **THEN** it SHALL use the naming format YYYY-MM-DD-<topic>.md and contain context, decision, and consequences sections

#### Scenario: Decision index

- **WHEN** the decision records directory is maintained
- **THEN** docs/decisions/README.md SHALL serve as an index listing all decisions with title, date, and one-line summary

### Requirement: Scrapling-first spec 迁移

The system SHALL mark the existing `scrapling-first-browser-workflow` spec as superseded, with its operational routing rules absorbed into `agents-governance`.

#### Scenario: Superseding declaration

- **WHEN** the scrapling-first-browser-workflow spec is updated
- **THEN** it SHALL include a `superseded_by: agents-governance` declaration at the top
- **AND** its operational content SHALL remain preserved for historical reference

#### Scenario: No duplication

- **WHEN** agents-governance defines workflow routing and engine selection
- **THEN** the superseded spec SHALL NOT be referenced as active behavioral authority
- **AND** design and tasks artifacts SHALL reference agents-governance for routing rules, not the superseded spec

### Requirement: Persistent shell change approval

The system SHALL treat persistent shell-environment changes as user-approved actions, not as implicit workflow side effects.

#### Scenario: Request to persist Scrapling CLI path

- **WHEN** the workflow determines that adding `SCRAPLING_CLI_PATH` to `/Users/nantas-agent/.zshenv` would improve future runs
- **THEN** it SHALL ask the user for confirmation before writing
- **AND** it SHALL continue without persistent shell modification if the user declines

