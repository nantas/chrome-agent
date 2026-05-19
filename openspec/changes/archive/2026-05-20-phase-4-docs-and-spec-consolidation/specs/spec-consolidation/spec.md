# Specification Delta

## Capability 对齐（已确认）

- Capability: `spec-consolidation`
- 来源: `proposal.md` Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change D2 合并映射，调整为含新增 9 个 change spec；冻结 extract-shared-lib 和 split-orchestrator-rename-package 的 spec delta

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: change-spec-freeze

The system SHALL merge spec deltas from two completed changes (`extract-shared-lib` and `split-orchestrator-rename-package`) into `openspec/specs/`, then archive both changes to `openspec/changes/archive/`.

The 9 spec deltas to freeze:
- From `extract-shared-lib`: `shared-strategy-loader`, `shared-config-resolver`, `mediawiki-api-extraction-pipeline` (delta merge)
- From `split-orchestrator-rename-package`: `pipeline-registry`, `pipeline-orchestration`, `pipeline-package-identity`, `pipeline-phases-fetch`, `pipeline-phases-convert`, `pipeline-discovery-summary`

#### Scenario: new-specs-frozen

- **WHEN** freeze is complete
- **THEN** all 9 spec directories SHALL exist in `openspec/specs/`
- **AND** `openspec/changes/extract-shared-lib/` SHALL be moved to `openspec/changes/archive/`
- **AND** `openspec/changes/split-orchestrator-rename-package/` SHALL be moved to `openspec/changes/archive/`

#### Scenario: delta-merged

- **WHEN** `mediawiki-api-extraction-pipeline` delta from `extract-shared-lib` is merged
- **THEN** `openspec/specs/mediawiki-api-extraction-pipeline/spec.md` SHALL contain the merged ADDED/MODIFIED requirements from both the original spec and the change delta
- **AND** no duplicate Requirement headers SHALL exist

### Requirement: spec-merge-by-domain

The system SHALL merge 74 existing spec files in `openspec/specs/` into ~22 capability-domain spec files, organized by functional domain.

The 22 target domains and their sources:

| Target Spec | Sources (count) |
|-------------|-----------------|
| `pipeline/pipeline-core.md` | mediawiki-api-extraction-pipeline + pipeline-cli-entry + pipeline-package-identity (3) |
| `pipeline/pipeline-orchestration.md` | pipeline-orchestration + pipeline-phases-fetch + pipeline-phases-convert + pipeline-resume + api-error-semantics (5) |
| `pipeline/pipeline-discovery.md` | homepage-driven-discovery + pipeline-discovery-summary + incremental-reprocess (3) |
| `pipeline/pipeline-registry.md` | pipeline-registry + pipeline-strategy-schema + platform-variant-framework + capabilities-derivation (4) |
| `pipeline/pipeline-conversion.md` | pipeline-convert-phase + pipeline-converters + pipeline-fetch-phase + unified-link-fixer + page-assignment + page-content-cache + mediawiki-cleanup-script + tooltip-icon-link-merge (8) |
| `pipeline/pipeline-infobox.md` | shared-infobox-renderer + unified-infobox-extraction + pipeline-infobox-rendering + balanced-element-removal (4) |
| `pipeline/html-preprocessing.md` | unified-html-preprocessing (1) |
| `explore/explore-deep-discovery.md` | explore-workflow + explore-backend-detection + explore (3) |
| `explore/explore-scaffold.md` | strategy-scaffold-generation + strategy-templates + sample-converter + sample-self-check (4) |
| `explore/explore-validation.md` | explore-architecture-gate + explore-strategy-pipeline-bridge (2) |
| `explore/explore-ki.md` | explore-ki-lifecycle (1) |
| `engines/engine-registry.md` | engine-registry + engine-contracts + extension-api + 8 engine-contract specs (11) |
| `strategy/strategy-schema.md` | site-strategy-schema + anti-crawl-schema + pipeline-strategy-schema (3) |
| `strategy/strategy-lifecycle.md` | site-strategy + bootstrap-strategy-cli + site-strategy-template + mediawiki-site-strategy + standalone-extraction (5) |
| `cli/cli-interface.md` | global-capability-cli + global-workflow-skill + explore-skill-gates (3) |
| `cli/cli-workflows.md` | scrapling-first-browser-workflow + strategy-guided-crawl + scrape-command + full-url-parameterization (4) |
| `governance/governance.md` | agents-governance + master-plan + capability-contracts (3) |
| `governance/handoff.md` | handoff-emission + handoff-gate (2) |
| `governance/output.md` | output-lifecycle + output-lifecycle-git-governance + report-emission-gating (3) |
| `shared/shared-lib.md` | shared-strategy-loader + shared-config-resolver (2) |
| `mediawiki/api.md` | mediawiki-api-contract + mediawiki-api-extraction + mediawiki-extraction-patterns + mediawiki-extraction (4) |
| `infra/install.md` | install-chain + scrapling-cli-environment (2) |
| `infra/doctor.md` | doctor-repo-freshness + pipeline-phase-naming (2) |

#### Scenario: merge-no-loss

- **WHEN** any source spec's Requirement is not present in the target spec
- **THEN** the merge SHALL be rejected
- **AND** the missing Requirement SHALL be added before proceeding

#### Scenario: merge-dedup

- **WHEN** two source specs contain Requirements with the same name
- **THEN** the merged spec SHALL contain exactly one copy
- **AND** conflicting scenario-level details SHALL be resolved by preferring the newer (Phase 1-3) source

#### Scenario: old-specs-removed

- **WHEN** a source spec's Requirements have all been migrated to the target spec
- **THEN** the source spec directory SHALL be deleted from `openspec/specs/`
- **AND** `grep -r "specs/<old-spec-name>" openspec/changes/` SHALL return no active references before deletion

### Requirement: stale-path-references-fix

During spec merge, all stale file path references from Phase 1-3 refactoring SHALL be corrected.

Path replacement table:

| Old Path Pattern | New Path |
|-----------------|----------|
| `scripts/mediawiki-api-extract/` (directory) | `scripts/pipeline/` |
| `scripts.mediawiki_api_extract` (Python module) | `scripts.pipeline` |
| `-m scripts.mediawiki_api_extract` (CLI invocation) | `-m scripts.pipeline` |
| `orchestrate.py` (filename) | `orchestrator.py` |
| `scripts/mediawiki-api-extract/pipeline/orchestrate.py` (_STRATEGY_REGISTRY location) | `scripts/pipeline/pipeline/registry.py` |
| `infox_renderer.py` (infobox module) | `lib/extraction/infobox.py` |
| `scripts/mediawiki-api-extract/converters/html_to_markdown.py` | `scripts/pipeline/converters/html_to_markdown.py` |
| `phase_0` / `phase_a` / `phase_b` / `phase_c` (file references) | `discovery_homepage` / `discovery_allpages` / `fetch`+`convert` / `assemble` |
| `run_phase_0()` / `run_phase_a()` / `run_phase_b()` / `run_phase_c()` (function references in prose) | Keep as-is (aliases preserved) or update to new names in prose only |

#### Scenario: path-replacement-verification

- **WHEN** all spec merges are complete
- **THEN** `grep -r "mediawiki-api-extract\|mediawiki_api_extract" openspec/specs/` SHALL return 0 matches
- **AND** `grep -r "orchestrate\.py" openspec/specs/` SHALL return 0 matches (except in historical/archival references)
- **AND** `grep -r "infox_renderer\.py" openspec/specs/` SHALL return 0 matches
