# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: orchestrator 需统一 discovery phase dispatch、修复 api.homepage 自动检测逻辑、移除对 Phase 0 的独立 phase 编号引用

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: pipeline-phase-dispatch

The pipeline orchestrator (`orchestrate.py`) SHALL dispatch the Discovery phase based on the `--discovery` CLI argument and the strategy configuration, NOT based on legacy phase numbering.

The dispatch logic SHALL follow this priority:
1. If `--discovery` is explicitly `allpages` or `homepage`, use that strategy
2. If `--discovery` is `auto` (or not specified) and strategy has `api.homepage`, use homepage strategy
3. Otherwise, use allpages strategy (default)

#### Scenario: auto-detection-with-homepage

- **WHEN** `--discovery` is not specified (defaults to `auto`)
- **AND** strategy frontmatter contains `api.homepage`
- **THEN** the orchestrator SHALL dispatch to homepage discovery
- **AND** SHALL log `"Strategy has api.homepage — using homepage discovery"`

#### Scenario: auto-detection-without-homepage

- **WHEN** `--discovery` is not specified (defaults to `auto`)
- **AND** strategy frontmatter does NOT contain `api.homepage`
- **THEN** the orchestrator SHALL dispatch to allpages discovery
- **AND** SHALL log `"No api.homepage config — using allpages discovery"`

#### Scenario: explicit-override-allpages

- **WHEN** `--discovery allpages` is specified
- **AND** strategy frontmatter contains `api.homepage`
- **THEN** the orchestrator SHALL dispatch to allpages discovery
- **AND** SHALL ignore `api.homepage` for discovery purposes (exclude_categories from api top level still apply)

#### Scenario: homepage-without-config-error

- **WHEN** `--discovery homepage` is specified
- **AND** strategy frontmatter does NOT contain `api.homepage`
- **THEN** the orchestrator SHALL return `EXIT_STRATEGY_ERROR`
- **AND** SHALL log `"Strategy has no 'api.homepage' configuration"`

### Requirement: exclude-categories-top-level

The pipeline SHALL read `exclude_categories` from `api.exclude_categories` (new top-level location) with fallback to `api.homepage.exclude_categories` (legacy location) for backward compatibility.

When Phase A (allpages discovery) runs, it SHALL apply `api.exclude_categories` to filter pages whose wiki categories match excluded names before adding them to the manifest.

#### Scenario: top-level-exclude-categories-in-phase-a

- **WHEN** strategy has `api.exclude_categories: [Music, Modding, Version History]`
- **AND** Phase A (allpages) runs
- **THEN** pages with wiki category "Music", "Modding", or "Version History" SHALL be excluded from the manifest
- **AND** the excluded page count SHALL be logged

#### Scenario: fallback-to-homepage-exclude-categories

- **WHEN** strategy has `api.homepage.exclude_categories: [Music]` but NO `api.exclude_categories`
- **AND** Phase A (allpages) runs
- **THEN** the orchestrator SHALL read `api.homepage.exclude_categories` as fallback
- **AND** pages with wiki category "Music" SHALL be excluded

#### Scenario: both-locations-defined

- **WHEN** strategy has both `api.exclude_categories: [Music]` and `api.homepage.exclude_categories: [Modding]`
- **AND** Phase A (allpages) or Phase 0 (homepage) runs
- **THEN** the orchestrator SHALL merge both lists (union)
- **AND** pages matching either "Music" or "Modding" SHALL be excluded

### Requirement: pipeline-resume-state-compatibility

The resume state mechanism SHALL remain compatible with manifests produced by either discovery strategy. The state file SHALL use `completed_pages` as the resume key; the `phase` field is metadata only and SHALL NOT affect resume behavior.

The `phase` field in the state file SHALL follow the new naming convention (`"extract"` / `"extract_done"` / `"done"`) instead of legacy names (`"B"` / `"B_done"`).

#### Scenario: resume-after-discovery-strategy-switch

- **WHEN** a previous run used allpages discovery
- **AND** a new run uses homepage discovery with `--resume`
- **THEN** the pipeline SHALL detect the manifest has changed
- **AND** SHALL re-extract pages that are in the new manifest but not in the resume state
- **AND** SHALL log `"Manifest changed — re-extracting new pages"`

### Requirement: phase-naming-in-logs

Log messages SHALL use descriptive strategy names instead of legacy phase numbers.

#### Scenario: discovery-log-messages

- **WHEN** homepage discovery runs
- **THEN** log messages SHALL use terms like `"homepage discovery"` or `"Phase 0 (homepage)"`
- **AND** SHALL NOT use bare `"Phase 0"` as a standalone label

#### Scenario: allpages-discovery-log-messages

- **WHEN** allpages discovery runs
- **THEN** log messages SHALL use terms like `"allpages discovery"`
- **AND** SHALL NOT use bare `"Phase A"` as a standalone label
