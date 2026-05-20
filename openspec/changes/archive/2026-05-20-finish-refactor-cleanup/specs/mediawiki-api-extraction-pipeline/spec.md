# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 将 5 个 phase 函数名从 `run_phase_0`/`run_phase_a`/`run_phase_c`/`run_phase_fetch`/`run_phase_convert` 重命名为与文件名对齐的名称

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## RENAMED Requirements

- FROM: `### Requirement: phase-naming-in-logs`
- TO: `### Requirement: phase-naming-in-logs` (requirement 名称不变，但实现范围扩展至模块级函数名)

## MODIFIED Requirements

### Requirement: phase-function-naming

All phase module entry-point functions SHALL use names aligned with their file names and conceptual roles, replacing legacy phase numbering.

The following function renames SHALL be applied:

| File | Old Name | New Name |
|------|---------|---------|
| `phases/discovery_homepage.py` | `run_phase_0` | `run_homepage_discovery` |
| `phases/discovery_allpages.py` | `run_phase_a` | `run_allpages_discovery` |
| `phases/fetch.py` | `run_phase_fetch` | `run_fetch` |
| `phases/convert.py` | `run_phase_convert` | `run_convert` |
| `phases/assemble.py` | `run_phase_c` | `run_assemble` |

The pipeline orchestrator (`orchestrator.py`) SHALL import and call the renamed functions.

#### Scenario: orchestrator-imports-renamed-functions

- **WHEN** `orchestrator.py` imports phase functions
- **THEN** import statements SHALL use the new names:
  - `from .phases.discovery_homepage import run_homepage_discovery`
  - `from .phases.discovery_allpages import run_allpages_discovery`
  - `from .phases.fetch import run_fetch`
  - `from .phases.convert import run_convert`
  - `from .phases.assemble import run_assemble`

#### Scenario: orchestrator-calls-renamed-functions

- **WHEN** `run_pipeline()` dispatches to discovery, fetch, convert, or assembly phases
- **THEN** it SHALL call the renamed functions
- **AND** the runtime behavior SHALL be identical to the old function names

#### Scenario: no-old-function-names-remain

- **WHEN** the rename is complete
- **THEN** `grep -rn "def run_phase_\|run_phase_0\|run_phase_a\|run_phase_c\|run_phase_fetch\|run_phase_convert" scripts/ --include="*.py"` SHALL return zero matches for function definitions or calls
- **AND** only comments or changelog entries MAY contain old names

### Requirement: phase-naming-in-logs

Log messages SHALL use descriptive strategy names instead of legacy phase numbers. This requirement is unchanged from the `fix-pipeline-quality-gaps` change; the function rename in this change completes the alignment.

#### Scenario: discovery-log-messages

- **WHEN** homepage discovery runs
- **THEN** log messages SHALL use terms like `"homepage discovery"`
- **AND** SHALL NOT use bare `"Phase 0"` as a standalone label

#### Scenario: allpages-discovery-log-messages

- **WHEN** allpages discovery runs
- **THEN** log messages SHALL use terms like `"allpages discovery"`
- **AND** SHALL NOT use bare `"Phase A"` as a standalone label
