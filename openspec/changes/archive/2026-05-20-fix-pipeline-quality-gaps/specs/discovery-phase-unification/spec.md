# Specification Delta

## Capability 对齐（已确认）

- Capability: `discovery-phase-unification`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: explore 阶段确认 Phase A 与 Phase 0 本质是同一 Discovery 阶段的两种互斥策略实现，应统一命名并通过 --discovery 参数切换

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: discovery-strategy-parameter

The system SHALL provide a `--discovery` CLI parameter with values `auto`, `allpages`, and `homepage`, controlling which discovery strategy is used during the pipeline's Discovery phase.

The `--discovery` parameter SHALL be orthogonal to `--phase` (which controls B/C execution).

#### Scenario: discovery-auto-with-homepage-config

- **WHEN** `--discovery` is `auto` (or not specified)
- **AND** the strategy has `api.homepage` defined
- **THEN** the pipeline SHALL use the homepage discovery strategy
- **AND** the orchestrator SHALL log `"Strategy has api.homepage — using homepage discovery"`

#### Scenario: discovery-auto-without-homepage-config

- **WHEN** `--discovery` is `auto` (or not specified)
- **AND** the strategy does NOT have `api.homepage` defined
- **THEN** the pipeline SHALL use the allpages discovery strategy
- **AND** the orchestrator SHALL log `"No api.homepage config — using allpages discovery"`

#### Scenario: discovery-explicit-override

- **WHEN** `--discovery allpages` is specified
- **AND** the strategy has `api.homepage` defined
- **THEN** the pipeline SHALL use the allpages discovery strategy
- **AND** the orchestrator SHALL log `"Discovery strategy overridden to allpages by --discovery flag"`

#### Scenario: discovery-homepage-without-config

- **WHEN** `--discovery homepage` is specified
- **AND** the strategy does NOT have `api.homepage` defined
- **THEN** the pipeline SHALL exit with `EXIT_STRATEGY_ERROR`
- **AND** the orchestrator SHALL log `"Strategy has no 'api.homepage' configuration — cannot use homepage discovery"`

### Requirement: phase-parameter-simplification

The `--phase` CLI parameter SHALL be simplified to only accept `extract`, `assemble`, and `all`. The `homepage` and `A`/`B`/`C` single-letter values SHALL be removed.

The default value SHALL remain `all` (extract + assemble).

#### Scenario: phase-all-default

- **WHEN** `--phase` is not specified
- **THEN** the pipeline SHALL run the full pipeline (discovery + extract + assemble)
- **AND** discovery strategy SHALL be determined by `--discovery` (default: `auto`)

#### Scenario: phase-extract-only

- **WHEN** `--phase extract` is specified
- **THEN** the pipeline SHALL skip discovery and assembly, running only content extraction
- **AND** a valid `page_manifest.json` SHALL exist in the output directory

#### Scenario: phase-assemble-only

- **WHEN** `--phase assemble` is specified
- **THEN** the pipeline SHALL skip discovery and extraction, running only output assembly
- **AND** valid `page_manifest.json` and `extraction_results.json` SHALL exist in the output directory

#### Scenario: deprecated-phase-homepage

- **WHEN** `--phase homepage` is specified (deprecated syntax)
- **THEN** the pipeline SHALL emit a deprecation warning
- **AND** the pipeline SHALL behave as if `--discovery homepage` was specified with `--phase all`

#### Scenario: deprecated-phase-letters

- **WHEN** `--phase A`, `--phase B`, or `--phase C` is specified (deprecated syntax)
- **THEN** the pipeline SHALL emit a deprecation warning
- **AND** map `A` → skip (discovery runs via `--discovery`), `B` → `extract`, `C` → `assemble`

### Requirement: unified-discovery-internal-naming

Internally, Discovery phase implementations SHALL be named by their strategy (`allpages_discovery`, `homepage_discovery`) rather than by phase number (`phase_a`, `phase_0`).

The orchestration code SHALL NOT refer to Phase 0 or Phase A as distinct phases. Both SHALL be dispatch targets under a single Discovery phase entry point.

#### Scenario: internal-module-names

- **WHEN** the pipeline runs discovery
- **THEN** the code SHALL invoke `run_allpages_discovery()` or `run_homepage_discovery()` based on the resolved strategy
- **AND** the module files SHALL retain their current filenames (`phase_a.py`, `phase_0.py`) for backward compatibility
- **AND** new imports SHALL use strategy-based naming in docstrings and log messages

### Requirement: dead-code-removal

The files `_pipeline_legacy.py` and `_strategies_legacy.py` SHALL be removed from the repository.

No code in the repository SHALL import from these files (verified by grep before removal).

#### Scenario: legacy-files-not-imported

- **WHEN** a grep for `_pipeline_legacy` or `_strategies_legacy` across `scripts/` is executed
- **THEN** zero matches SHALL be found
- **AND** the files SHALL be safe to delete

#### Scenario: legacy-files-removed

- **WHEN** the files are deleted
- **THEN** all existing imports and pipeline execution SHALL continue to work unchanged
- **AND** `python3 -m scripts.mediawiki-api-extract` SHALL complete successfully
