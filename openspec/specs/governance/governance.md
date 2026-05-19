# Governance Domain: Core Governance — Merged Spec

## Source Attribution

| Source Spec | Type | Notes |
|------------|------|-------|
| `agents-governance` | frozen | AGENTS.md structure, workflow routing, engine selection, reporting, directory governance, strategy schema |
| `master-plan` | frozen | Repository-wide planning, phase boundaries, capability map, README framing |
| `capability-contracts` | frozen | Universal contract metamodel (input/output/error dimensions) for all engine contracts |

Paths have been updated to reflect the current directory structure (`scripts/pipeline/`, `scripts.pipeline`, `orchestrator.py`).

---

# Core Governance Specification

## Purpose

Define the repository entry document governance, workflow routing, engine selection strategy, reporting expectations, directory governance, decision records, master planning, phase boundaries, and the universal contract metamodel for all engine capabilities.

---

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

The system SHALL declare chrome-agent as a cross-repo web scraping service with a skill-first, CLI-backed external entry model.

The service identity SHALL state that:
- the global `chrome-agent` workflow skill is the recommended primary entry for agent-driven usage
- the repo-backed `chrome-agent` CLI is the low-level explicit execution surface and shell/backend entry
- repository-local governance remains authoritative for workflow execution

#### Scenario: Identity declaration

- **WHEN** an operator or agent reads the Service Identity section
- **THEN** the section SHALL state that chrome-agent is a "跨仓库网页抓取服务（cross-repo web scraping service）"
- **AND** it SHALL describe the global workflow skill as the recommended agent-first entry
- **AND** it SHALL describe the repo-backed CLI as the backend execution surface rather than the only formal entry
- **AND** it SHALL preserve the four core principles: Scrapling-first, workflow-driven (AGENTS.md + skills), read-only by default for authenticated runs, and evidence-driven reporting

#### Scenario: Scope boundaries

- **WHEN** the identity section defines scope
- **THEN** it SHALL state in-scope activities (webpage content retrieval, frontend debugging, evidence collection, reporting)
- **AND** it SHALL state the current out-of-scope boundary (credential management, large automation framework)

### Requirement: 工作流路由规则

The system SHALL document that both the global workflow skill and the repo-backed CLI are entry layers, while repository-local workflow routing remains authoritative.

For any request arriving through the skill or the CLI, the repository-local workflow SHALL still decide Content Retrieval versus Platform/Page Analysis according to repository governance.

For any workflow path that depends on Scrapling as the first engine family, the system SHALL check Scrapling CLI availability before attempting fetcher selection or content retrieval.

#### Scenario: Skill entry with repository routing

- **WHEN** a request enters through the global `chrome-agent` workflow skill
- **THEN** the skill MAY route the request to `fetch`, `explore`, or `crawl`
- **AND** the repository-local workflow SHALL remain authoritative for engine selection, fallback escalation, and reporting behavior

#### Scenario: CLI entry with repository routing

- **WHEN** a request enters through the repo-backed `chrome-agent` CLI
- **THEN** the target repository SHALL still apply its own workflow routing and execution rules
- **AND** the CLI SHALL not replace those routing decisions with a parallel policy layer

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

The system SHALL preserve repository-local engine selection authority even when a request originates from the global workflow skill or the global CLI.

#### Scenario: Global entry, local engine selection

- **WHEN** `chrome-agent fetch` or `chrome-agent crawl` dispatches into the repository
- **THEN** the repository-local workflow SHALL continue to apply Scrapling-first selection, strategy overrides, and fallback boundaries
- **AND** the global workflow skill and CLI SHALL not hardcode an alternative engine selection model

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

#### Scenario: AGENTS.md content boundary after CLI introduction

- **WHEN** AGENTS.md is updated for Phase 5+
- **THEN** it SHALL describe the existence and role of the global workflow skill and CLI at the governance level
- **AND** it SHALL keep detailed launcher install and doctor procedures in setup or playbook documents rather than turning AGENTS.md into an install manual

### Requirement: 决策记录治理

The system SHALL define the governance rules for decision records in AGENTS.md.

#### Scenario: Decision record format

- **WHEN** a new decision record is created in docs/decisions/
- **THEN** it SHALL use the naming format YYYY-MM-DD-<topic>.md and contain context, decision, and consequences sections

#### Scenario: Decision index

- **WHEN** the decision records directory is maintained
- **THEN** docs/decisions/README.md SHALL serve as an index listing all decisions with title, date, and one-line summary

### Requirement: Reference Index

The system SHALL index both the agent-facing skill path and the CLI/playbook path in its governance references.

#### Scenario: Reference coverage

- **WHEN** AGENTS.md or README links the repository's external entry documentation
- **THEN** the references SHALL cover the global workflow skill and the repo-backed CLI/backend guidance together
- **AND** they SHALL not describe the skill as merely historical if it remains the recommended agent-first entry

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

### Requirement: Pipeline Strategy Schema 治理章节

The system SHALL include a Pipeline Strategy Schema 治理 subsection within AGENTS.md, placed after the 策略库治理（Strategy Library Governance）section.

该章节 SHALL 包含以下内容：

1. **权威来源声明**：声明 `_STRATEGY_REGISTRY`（位于 `scripts/pipeline/pipeline/orchestrator.py`）为策略 ID 的唯一权威来源
2. **策略文件约束**：`content_profile` 字段只能引用已注册 ID；Pipeline 启动时 hard-fail 校验
3. **扩展协议**：实现 → 注册 → 引用的严格顺序
4. **Registry 变更约束**：删除/重命名 ID 前必须反向检查
5. **当前注册 ID 清单**：各维度的合法 ID 列表（快速参考，不替代代码权威）
6. **platform_variant 声明**：可选字段用于 MediaWiki 平台子类型化（fandom / wiki-gg / standard）

#### Scenario: 章节位置与内容

- **WHEN** 用户或 agent 阅读 AGENTS.md
- **THEN** Pipeline Strategy Schema 治理章节 SHALL 位于策略库治理之后
- **AND** SHALL 包含权威来源、约束、扩展协议、ID 清单和 variant 声明
- **AND** SHALL 明确引用 `scripts/pipeline/pipeline/orchestrator.py` 作为 `_STRATEGY_REGISTRY` 的权威位置

### Requirement: explore-crawl-confirmation-gate

AGENTS.md SHALL include an «Explore→Crawl Confirmation Gate» section within the Governance Rules area. This section SHALL define the mandatory confirmation sequence an agent must follow after `explore` identifies a strategy gap, before proceeding to `crawl` or `fetch`.

The section SHALL state:

1. When `explore` returns `partial_success` with a strategy gap, the agent MUST follow the Explore Workflow Gates defined in the chrome-agent skill.
2. The agent MUST NOT proceed directly to `crawl` or `fetch` without user confirmation.
3. The agent MUST present at minimum: structure analysis, sample conversions, and self-check results.
4. When `explore` returns `failure`, the agent MUST surface the exact failure reason and remediation, MUST NOT fabricate a strategy or workaround, and MUST NOT attempt to fall back to a different extraction path without user approval.

#### Scenario: agent-reads-confirmation-gate

- **WHEN** an agent reads AGENTS.md after `explore` returns a strategy gap
- **THEN** the agent SHALL find an explicit rule prohibiting direct progression to `crawl` or `fetch`
- **THEN** the rule SHALL reference the chrome-agent skill for the detailed gate sequence
- **THEN** the rule SHALL enumerate minimum requirements: structure analysis, sample conversions, self-check results

#### Scenario: explore-failure-prohibition

- **WHEN** `explore` returns `result: "failure"`
- **THEN** the agent SHALL NOT attempt to create a strategy, run any extraction pipeline, or invent a workaround
- **THEN** the agent SHALL surface the failure reason and suggested remediation from the explore result as-is
- **THEN** the agent SHALL wait for user direction before taking any further action on the target URL

#### Scenario: section-placement

- **WHEN** AGENTS.md is rendered
- **THEN** the «Explore→Crawl Confirmation Gate» section SHALL appear within the Governance Rules area
- **THEN** it SHALL be placed after the existing «Intent Routing» subsection (which defines the route rules for fetch/explore/crawl) and before any subsequent governance section

---

## Master Planning Requirements

### Requirement: Master planning document

The system SHALL produce a master planning document at `docs/governance-and-capability-plan.md` that defines the full project landscape without diving into per-capability implementation details.

#### Scenario: Document structure

- **WHEN** the document is generated
- **THEN** it SHALL contain the following sections:
  - 项目目标与服务身份声明（仓库作为"跨仓库网页抓取服务"）
  - 当前状态摘要（已验证的能力、现有结构）
  - 能力全景图（对外: explore/fetch/crawl；对内: site-strategy/anti-crawl-strategy/engine-registry/output-lifecycle）
  - 阶段划分与交付边界（Phase 1–5 描述+各阶段输出物）
  - 依赖关系（哪个阶段前置哪个）
  - 技术栈与工具链说明（当前引擎 + 扩展方向）
  - 治理约束（repo:// 语义、binding 引用、决策记录索引）

#### Scenario: Phase boundary definition

- **WHEN** each phase is described
- **THEN** the phase entry SHALL include: phase name, scope, deliverables, required specs/contracts to create, and a clear exclusion boundary

### Requirement: 能力全景图

The system SHALL define the external entry model as skill-first and CLI-backed while treating `CHROME_AGENT_REPO` as the default runtime prerequisite for the backend CLI path.

The capability map SHALL show:
- the global `chrome-agent` workflow skill as the recommended agent-facing entry
- the repo-backed `chrome-agent` CLI as the low-level explicit command surface for `explore`, `fetch`, `crawl`, `doctor`, and `clean`

#### Scenario: Phase 5 capability framing

- **WHEN** the master plan describes the external capability progression
- **THEN** Phase 5+ SHALL be framed around a skill-first workflow entry with an env-first backend runtime path
- **AND** it SHALL not frame repo-registry as the default repository lookup path for high-frequency usage

### Requirement: 阶段划分

The system SHALL describe the post-Phase-5 runtime contract as a two-layer entry model whose default local repository source is `CHROME_AGENT_REPO`.

#### Scenario: Phase 5 summary

- **WHEN** the master plan lists Phase 5 scope, deliverables, and boundaries
- **THEN** the scope SHALL describe workflow skill + CLI layering, env-first repository resolution, and explicit override support
- **AND** it SHALL not describe repo-registry-first auto-discovery as the primary runtime assumption

### Requirement: 依赖关系

The system SHALL explain that the skill-first entry layer depends on the stable repository contracts and the CLI backend without replacing either one.

#### Scenario: Phase dependency wording

- **WHEN** the plan explains the dependency shape of Phase 5
- **THEN** it SHALL state that the workflow skill depends on the repo-backed CLI and the repository's stable engine, strategy, and governance contracts
- **AND** it SHALL explain that the skill adds intent routing and result packaging rather than a parallel execution runtime

### Requirement: README rewrite

The system SHALL rewrite `README.md` to reflect the env-first, skill-first / CLI-backed public model.

#### Scenario: README content

- **WHEN** the README is updated after this change
- **THEN** it SHALL distinguish the recommended agent-facing entry from the CLI backend command surface
- **AND** it SHALL explain that `CHROME_AGENT_REPO` is the default runtime prerequisite
- **AND** it SHALL reserve repo-registry references for explicit repo-ref or maintenance-oriented paths

---

## Capability Contract Metamodel

### Requirement: 契约元模型结构

The system SHALL define a universal contract metamodel that all engine-specific contracts MUST follow.

Each engine contract SHALL define three dimensions:

1. **Input Contract**: 引擎接受的输入参数——URL 格式要求、session 模式、超时配置、可选的 CSS selector/headers/cookies/proxy 等
2. **Output Contract**: 引擎在成功时产出的输出——extraction format (markdown/text/html)、content structure、metadata fields (title, final URL, timestamp)
3. **Error Contract**: 引擎在异常时的错误模型——error categories (network, timeout, block, auth, parse)、error response structure、recommended next action per error type

#### Scenario: Contract dimension completeness

- **WHEN** an engine contract is defined under openspec/specs/<engine-id>-contract/spec.md
- **THEN** it SHALL contain all three dimensions (input, output, error) with non-empty requirement blocks
- **AND** missing any dimension SHALL be treated as an incomplete contract

#### Scenario: Contract validation

- **WHEN** a contract is validated against this metamodel
- **THEN** each dimension SHALL use `### Requirement:` blocks with SHALL/MUST language
- **AND** each requirement SHALL have at least one `#### Scenario:` block

### Requirement: 契约命名与存放规则

The system SHALL define the naming and storage conventions for capability contracts.

#### Scenario: Contract file location

- **WHEN** an engine contract is created
- **THEN** it SHALL be stored at `openspec/specs/<engine-id>-contract/spec.md`
- **AND** <engine-id> SHALL use kebab-case matching the engine's identifier (e.g., `scrapling-get-contract`, `scrapling-fetch-contract`, `scrapling-stealthy-fetch-contract`, `chrome-devtools-mcp-contract`, `chrome-cdp-contract`)

#### Scenario: Contract metamodel location

- **WHEN** the contract metamodel itself is referenced
- **THEN** it SHALL be located at `openspec/specs/capability-contracts/spec.md`
- **AND** this file SHALL serve as the normative reference for all engine contracts

#### Scenario: Contract identifier format

- **WHEN** a contract capability ID is used in proposals
- **THEN** it SHALL follow the pattern `<engine-id>-contract` (e.g., `scrapling-get-contract`)
- **AND** it SHALL clearly distinguish from the engine capability ID itself

### Requirement: 输入契约规范

The system SHALL define the required fields for the input dimension of an engine contract.

#### Scenario: Input contract required fields

- **WHEN** an engine's input contract is defined
- **THEN** it SHALL specify:
  - URL format constraints and supported schemes
  - Required vs optional parameters with their types and defaults
  - Session mode support (single-shot, persistent, bulk)
  - Timeout behavior and default values
  - Header, cookie, and proxy parameter specifications
  - Authentication boundary rules (read-only by default)

#### Scenario: Input contract format

- **WHEN** input parameters are documented
- **THEN** each parameter SHALL include: name, type, required/optional, default value (if any), and a one-sentence description

### Requirement: 输出契约规范

The system SHALL define the required fields for the output dimension of an engine contract.

#### Scenario: Output contract required fields

- **WHEN** an engine's output contract is defined
- **THEN** it SHALL specify:
  - Supported extraction formats (markdown, text, html) with the default
  - Content structure fields (title, body/content, final URL, metadata)
  - Image handling rules (preserve inline image URLs vs strip)
  - Main content extraction behavior (whether default is body-only or full page)
  - Response metadata that MUST be present in every successful output

#### Scenario: Output contract schema

- **WHEN** output fields are documented
- **THEN** each field SHALL include: field name, type, presence (always/maybe), and a one-sentence description

### Requirement: 错误契约规范

The system SHALL define the required fields for the error dimension of an engine contract.

#### Scenario: Error contract required fields

- **WHEN** an engine's error contract is defined
- **THEN** it SHALL specify:
  - Error categories (at minimum: network, timeout, block/challenge, auth, parse/extraction)
  - Error response structure (error code, human-readable message, diagnostic context)
  - Recommended next action per error category (retry, escalate, stop, switch engine)

#### Scenario: Error contract completeness

- **WHEN** an engine encounters a failure mode not listed in its error contract
- **THEN** the error SHALL be reported as an "unclassified" error with full context preserved
- **AND** the engine's contract SHALL be updated to cover the newly discovered failure mode

### Requirement: 契约版本管理

The system SHALL define version management conventions for capability contracts.

#### Scenario: Contract version identifier

- **WHEN** a contract is created or modified
- **THEN** the contract SHALL include a version identifier at the top of the spec (e.g., `version: 1.0.0`)
- **AND** a change history section SHALL record each version with date and summary of changes

#### Scenario: Contract modification via change workflow

- **WHEN** an existing contract needs modification
- **THEN** the modification SHALL go through a new openspec change with a Modified Capabilities entry
- **AND** the change SHALL use MODIFIED Requirements blocks in its delta spec
