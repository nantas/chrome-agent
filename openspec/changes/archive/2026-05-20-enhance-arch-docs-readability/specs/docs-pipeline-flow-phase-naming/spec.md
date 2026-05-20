# Specification Delta

## Capability 对齐（已确认）

- Capability: `docs-pipeline-flow-phase-naming`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 更新管线数据流文档中过时的 Phase 命名

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: phase-naming-in-docs

The document `docs/architecture/02-pipeline-flow.md` SHALL use phase names consistent with the current codebase (after `finish-refactor-cleanup` change).

All references to legacy phase numbering SHALL be updated:

| Old Reference | New Reference |
|--------------|---------------|
| `Phase 0` / `Homepage Discovery` | `homepage discovery` |
| `Phase A` / `Allpages Discovery` | `allpages discovery` |
| `Phase B` / `Phase Fetch` / `Phase Convert` | `fetch` / `convert` |
| `Phase C` / `Assembly` | `assembly` |
| `run_phase_0()` | `run_homepage_discovery()` |
| `run_phase_a()` | `run_allpages_discovery()` |
| `run_phase_c()` | `run_assemble()` |

The pipeline flowchart in §2 SHALL use the updated names.

#### Scenario: phase-headings-updated

- **WHEN** reading the five-stage pipeline sections
- **THEN** all section headings SHALL use descriptive names (not "Phase 0", "Phase A", "Phase C")
- **AND** all function references SHALL match current code (`run_homepage_discovery`, `run_allpages_discovery`, `run_assemble`)

#### Scenario: flowchart-names-updated

- **WHEN** viewing the end-to-end data flow diagram
- **THEN** phase nodes SHALL use the current naming
- **AND** no "Phase 0", "Phase A", "Phase B", or "Phase C" labels SHALL appear

#### Scenario: function-names-updated

- **WHEN** reading the "入口" field in the phase tables
- **THEN** function names SHALL reference the current code (`run_homepage_discovery`, `run_allpages_discovery`, `run_assemble`)
- **AND** SHALL NOT reference old names (`run_phase_0`, `run_phase_a`, `run_phase_c`)
