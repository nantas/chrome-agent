# Specification Delta

## Capability 对齐（已确认）

- Capability: `docs-architecture`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 8 篇架构文档清单基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change D1 扩展为 AGENTS.md 内容注入版，覆盖系统全景、管线流、策略 Schema、CLI 参考、转换器、引擎选择、Explore 工作流、技术栈

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: docs-architecture-directory-structure

The system SHALL create `docs/architecture/` directory containing 8 human-readable architecture documents, numbered for reading order.

#### Scenario: directory-creation

- **WHEN** `docs/architecture/` is created
- **THEN** the directory SHALL contain exactly 8 `.md` files: `01-overview.md`, `02-pipeline-flow.md`, `03-strategy-schema.md`, `04-cli-reference.md`, `05-converter-architecture.md`, `06-engine-selection.md`, `07-explore-workflow.md`, `08-tech-stack.md`

### Requirement: docs-truth-source-code-first

Each architecture document SHALL document the actual code behavior (verified via LSP symbols, definition, and references), NOT describe aspirational or spec-level intent that diverges from implementation.

#### Scenario: code-as-truth

- **WHEN** writing any architecture document
- **THEN** key function signatures, module paths, import relationships, and call chains SHALL be verified with `lsp symbols` / `lsp definition` / `lsp references` before writing
- **AND** the document SHALL cite the verified file path and line number for each architectural claim

### Requirement: docs-01-overview-content

`01-overview.md` SHALL cover: system positioning and core design principles (Scrapling-first, workflow-driven, read-only by default, evidence-driven), multi-backend architecture diagram (ASCII art), technology stack summary table, and updated directory structure including `scripts/lib/`.

#### Scenario: overview-completeness

- **WHEN** `01-overview.md` is read
- **THEN** it SHALL reference `scripts/lib/strategy_loader.py`, `scripts/lib/config_resolver.py`, `scripts/lib/extraction/`, `scripts/pipeline/`, `scripts/explore/`, and `scripts/chrome-agent-cli.mjs`
- **AND** the directory structure SHALL match the verified layout from LSP file listing

### Requirement: docs-02-pipeline-flow-content

`02-pipeline-flow.md` SHALL cover: end-to-end flow diagram (ASCII art), five-phase detail (homepage discovery → allpages discovery → fetch → convert → assembly) with input/output/side-effects per phase, cache mechanism (Fetch ↔ Convert decoupling), resume/checkpoint mechanism, and rate-limit priority resolution (CLI → strategy local → anti-crawl tier → defaults).

#### Scenario: pipeline-flow-accuracy

- **WHEN** `02-pipeline-flow.md` documents the pipeline flow
- **THEN** phase function names SHALL match actual code: `run_phase_0` (aliased from `discovery_homepage`), `run_phase_a` (aliased from `discovery_allpages`), `run_phase_fetch`, `run_phase_convert`, `run_phase_c` (aliased from `assembly`)
- **AND** the orchestrator entry point SHALL reference `scripts/pipeline/pipeline/orchestrator.py:run_pipeline()`

### Requirement: docs-03-strategy-schema-content

`03-strategy-schema.md` SHALL be the single authoritative source of YAML frontmatter field reference for strategy files. It SHALL document: every frontmatter field with type, required/optional, default value, and example; valid values for `content_profile.*` dimensions sourced from `scripts/pipeline/pipeline/registry.py:_STRATEGY_REGISTRY`; `platform_variant` enum (`standard`, `fandom`, `wiki-gg`); `registry.json` format; anti-crawl strategy format.

#### Scenario: strategy-schema-authoritative

- **WHEN** any agent or operator needs to know a strategy field's valid values
- **THEN** they SHALL consult `03-strategy-schema.md` as the single source of truth
- **AND** the document SHALL declare this authority explicitly in its header

### Requirement: docs-04-cli-reference-content

`04-cli-reference.md` SHALL cover: all commands (`explore`, `fetch`, `crawl`, `scrape`, `bootstrap-strategy`, `doctor`, `clean`, `iterate`, `freeze`) with parameter tables; pipeline subcommand reference (`--phase`, `--discovery`, `--re-fetch`, `--from-manifest`, `--exclude-category`, `--max-pages`, `--concurrency`, `--workers`); JSON output format reference.

#### Scenario: cli-reference-completeness

- **WHEN** `04-cli-reference.md` is read
- **THEN** every command and flag documented SHALL be verifiable against `scripts/chrome-agent-cli.mjs:parseArgs()`
- **AND** pipeline subcommand flags SHALL be verifiable against `scripts/pipeline/cli.py`

### Requirement: docs-05-converter-architecture-content

`05-converter-architecture.md` SHALL cover: two-phase model (preprocessing + conversion), unified extraction engine design (`lib/extraction/infobox.py:extract_infobox()`, `lib/extraction/preprocessor.py:preprocess_html()`), Infobox extraction mechanism (BS4 vs selectolax dual parser, field handler callback pattern), HTML cleanup pipeline (context-aware: "pipeline" lightweight vs "explore" full 6-phase), and converter integration points (`html_to_markdown.py` in `scripts/pipeline/converters/`).

#### Scenario: converter-doc-accuracy

- **WHEN** `05-converter-architecture.md` documents the converter
- **THEN** it SHALL reference the exact function signatures verified via LSP hover
- **AND** it SHALL explicitly note that `html_to_markdown.py` remains in `scripts/pipeline/converters/` (not yet in `lib/extraction/`), with rationale

### Requirement: docs-06-engine-selection-content

`06-engine-selection.md` SHALL cover: full engine registry table (10 engines including `mediawiki-api` and `obscura-serve-pool`) sourced from `configs/engine-registry.json`; engine selection decision tree (platform detection → protection level → page type → fetcher routing); preflight mechanism (Scrapling, Obscura, CloakBrowser); fallback escalation path; and engine version governance (version manifest, upgrade workflow, hash/size fields).

#### Scenario: engine-table-complete

- **WHEN** `06-engine-selection.md` lists engines
- **THEN** the list SHALL match `configs/engine-registry.json` exactly (all 10 engines, correct ranks, correct statuses)
- **AND** `scrapling-stealthy-fetch` SHALL be marked as `superseded`

### Requirement: docs-07-explore-workflow-content

`07-explore-workflow.md` SHALL cover: deep discovery 8-step pipeline (ProbeChain → ApiDiscovery → StructureMapper → ProtectionIdentifier → Template Selection → Scaffold Generation → Sample Conversion & Self-Check → Freeze); Architecture Gate validation (strategy↔pipeline bidirectional alignment); KI Lifecycle Gate; sample converter CLI usage; and the confirmation gate between explore and crawl.

#### Scenario: explore-workflow-accuracy

- **WHEN** `07-explore-workflow.md` documents deep discovery
- **THEN** the 8 steps SHALL match `scripts/explore/main.py` implementation
- **AND** Architecture Gate logic SHALL reference `scripts/explore/gates/architecture.py`
- **AND** KI Lifecycle SHALL reference `scripts/explore/ki_lifecycle.py`

### Requirement: docs-08-tech-stack-content

`08-tech-stack.md` SHALL cover: runtime dependencies table (Python modules: `scripts/lib/`, `scripts/pipeline/`, `scripts/explore/`; Node.js modules: `chrome-agent-cli.mjs`, `chrome-agent-runtime.mjs`); external engine dependencies (Scrapling, Obscura, CloakBrowser) with version manifest; development conventions (Node.js ESM rules, Python 3.9 compatibility, shell scripting patterns); LSP code intelligence patterns (4 verified patterns); test commands and infrastructure; and common pitfalls with remediation.

#### Scenario: tech-stack-accuracy

- **WHEN** `08-tech-stack.md` documents Python compatibility
- **THEN** it SHALL state that `sample_converter.py` uses `from typing import Optional` (no longer has `dict | None` issue)
- **AND** it SHALL document that `html_to_markdown.py` uses `from __future__ import annotations` for `X | Y` syntax

### Requirement: docs-agents-md-content-injection

Content currently in `AGENTS.md` that constitutes architecture or development guidance SHALL be migrated to the corresponding architecture documents, with each source section mapping to exactly one target document.

#### Scenario: content-migration-completeness

- **WHEN** migration is complete
- **THEN** AGENTS.md SHALL contain only governance rules (≤3KB)
- **AND** each migrated section SHALL be replaced with a `→ 详见 docs/architecture/<file>.md` link
- **AND** `docs/architecture/` documents SHALL be the authoritative source for the migrated content

### Requirement: docs-architecture-index

AGENTS.md and README.md SHALL include an index entry pointing to `docs/architecture/` as the architecture documentation directory.

#### Scenario: index-entry

- **WHEN** AGENTS.md or README.md is read
- **THEN** a reader SHALL find a reference to `docs/architecture/01-overview.md` as the architecture documentation entry point
