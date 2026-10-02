# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore`
- 来源: proposal.md；用户基于已讨论的 Explore 停止条件与 CLI 失败传播方案要求创建 change。
- 变更类型: modified。

## 规范真源声明

本文件是 Explore 本次改动的行为真源，design/tasks/verification 必须引用。归档合并至 openspec/specs/explore/explore-deep-discovery.md 的同名 requirements，保留其他要求。

## MODIFIED Requirements

### Requirement: deep-discovery

The system SHALL, when `explore` is executed against a URL not covered by an existing strategy, automatically execute a deep discovery pipeline before reporting a strategy gap. Each engine candidate SHALL pass the shared fetch-content-admission contract before being selected as success_engine or passed to structure analysis. Rejected content SHALL continue through the existing engine chain; no usable content SHALL stop downstream structure mapping, scaffold generation and automatic sample work.

Deep discovery startup SHALL make repository-local packages and sibling Explore modules importable before importing pipeline modules, without requiring caller-provided PYTHONPATH or a particular working directory. The existing application-layer interpreter resolution and discovery/confirmation gates SHALL remain in effect.

#### Scenario: chain-engine-probe
- **WHEN** `explore` starts with no matching strategy
- **THEN** the system SHALL attempt engine chain: `scrapling-get` → `obscura-fetch` → `cloakbrowser-fetch` → `chrome-devtools-mcp`
- **THEN** the system SHALL record for each engine: `status` (success/failure/partial), `http_status` or `error_type`, `page_title`, `content_length`

#### Scenario: api-discovery
- **WHEN** any engine in the chain succeeds
- **THEN** the system SHALL probe for known API endpoints: `/api.php` (MediaWiki), `/wp-json` (WordPress), `/graphql` (GraphQL), `/sitemap.xml`, `/robots.txt`
- **THEN** the system SHALL record for each detected API: `type`, `base_url`, `version`, `capabilities`

#### Scenario: structure-mapping
- **WHEN** page content is successfully retrieved
- **THEN** the system SHALL extract the page type (home/list/article/gallery) based on DOM features
- **THEN** the system SHALL identify nav structure and extract top-level section labels (≤10 items)
- **THEN** the system SHALL NOT extract the complete internal link topology
- **THEN** the system SHALL detect content structure: presence of tables, infoboxes, list/card patterns

#### Scenario: protection-identification
- **WHEN** the engine chain produces failures or partial results
- **THEN** the system SHALL identify the protection mechanism (cloudflare-turnstile / cloudflare-managed / login-wall / rate-limit / none)
- **THEN** the system SHALL record the detection basis (HTTP status, DOM markers, error message)

#### Scenario: direct-entry-without-pythonpath
- **WHEN** application dependencies are available and the real `scripts/explore/main.py --help` entry is launched as a child process with PYTHONPATH removed
- **AND** its cwd is either the repository root or an unrelated temporary directory
- **THEN** it SHALL exit 0 and display the Deep discovery CLI help
- **AND** it SHALL NOT emit `ModuleNotFoundError: No module named 'scripts'`
- **AND** it SHALL NOT fetch pages, create a scaffold, or start extraction.

#### Scenario: strategy-gap-cli-startup
- **WHEN** the real CLI routes a strategy-gap Explore request to the real main.py entry with application dependencies available and PYTHONPATH absent
- **THEN** repository-local imports SHALL succeed before probe-chain execution
- **AND** subsequent probe success or failure SHALL be reported through the existing Explore result/handoff contract.

#### Scenario: challenge-fallback-recovery
- **WHEN** the first engine returns challenge HTML and a later eligible engine returns admitted normal HTML
- **THEN** the first attempt SHALL be failure with challenge evidence and the later engine SHALL be selected
- **AND** only its admitted HTML SHALL be structurally analyzed

#### Scenario: no-admitted-content
- **WHEN** no engine produces admitted content, including when the last fallback requires manual action
- **THEN** success_engine SHALL be null and the workflow SHALL return failure with the attempt evidence
- **AND** it SHALL NOT invoke structure mapping, scaffold generation, sample conversion or freeze
- **AND** existing strategy files SHALL remain unchanged
- **AND** browser authorization requirements SHALL remain in effect

### Requirement: explore-preflight-failure

The system SHALL report dependency and unstructured execution errors as failures, while preserving recognized structured workflow outcomes, their evidence and failure classification across the Python-to-CLI boundary. No admitted content SHALL produce result=failure and SHALL NOT produce a completed-discovery or freeze-readiness claim.

#### Scenario: python-deps-missing
- **WHEN** `runExplore()` checks Python dependencies and one or more are not importable
- **THEN** the system SHALL return `result: "failure"` with `summary` containing the missing package names

#### Scenario: deep-discovery-execution-failure
- **WHEN** `scripts/explore/main.py` fails without a recognized structured workflow outcome
- **THEN** the system SHALL return `result: "failure"` with `summary` containing the first 500 characters of stderr

#### Scenario: structured-content-failure
- **WHEN** main.py emits a recognized structured content-admission failure and nonzero exit code
- **THEN** the CLI SHALL preserve result=failure, reason, engine evidence and diagnostic references
- **AND** it SHALL NOT reclassify the external challenge as an internal pipeline crash
- **AND** it SHALL NOT describe discovery as completed, report a successful engine or recommend freeze

#### Scenario: structured-partial-outcome
- **WHEN** main.py emits a recognized partial outcome backed by admitted content, such as an architecture-gate failure
- **THEN** the CLI SHALL preserve partial_success and its evidence without converting it to a generic internal crash
- **AND** freeze readiness SHALL NOT be inferred from scaffold existence alone
