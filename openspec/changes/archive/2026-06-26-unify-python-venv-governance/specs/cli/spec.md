# Specification Delta

## Capability 对齐（已确认）

- Capability: `cli`
- 来源: `proposal.md` → Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: grill Q3a(B) resolveAppPython 覆盖全部应用层 spawn + Q3b(C) cloakbrowser 独立 managed venv

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Python Interpreter Resolution for Application-Layer Spawns

The system SHALL resolve the Python interpreter for application-layer spawns (explore `main.py`, `freeze.py`, `iterate.py`, pipeline `-m scripts.pipeline`) using `resolveAppPython(repoRoot)` from `scripts/lib/python-resolver.mjs`. Priority: `CHROME_AGENT_PYTHON` env > `<repoRoot>/.venv/bin/python` > system `python3`. Hardcoded `"python3"` in these spawn points SHALL NOT be used.

#### Scenario: Application-layer spawn with venv
- **WHEN** cli.mjs spawns explore `freeze.py` and `.venv/bin/python` exists
- **THEN** the spawn SHALL use `.venv/bin/python`

#### Scenario: Application-layer spawn without venv (fallback)
- **WHEN** cli.mjs spawns pipeline `-m scripts.pipeline` and `.venv/bin/python` does not exist
- **THEN** the spawn SHALL fall back to system `python3`

### Requirement: CloakBrowser Engine Spawn via Managed Venv

The system SHALL resolve the Python interpreter for `cloakbrowser_fetcher.py` via `scripts/cloakbrowser-cli.sh preflight`. The preflight script SHALL manage a dedicated venv at `$HOME/.cache/chrome-agent-cloakbrowser/` using `uv venv --python 3.11` and `uv pip install cloakbrowser`. The hardcoded `"python3"` in the cloakbrowser spawn point SHALL NOT be used.

#### Scenario: CloakBrowser spawn with managed venv ready
- **WHEN** cli.mjs spawns `cloakbrowser_fetcher.py` and the managed venv exists with `cloakbrowser` importable
- **THEN** the spawn SHALL use `$HOME/.cache/chrome-agent-cloakbrowser/bin/python`

#### Scenario: CloakBrowser spawn triggers lazy install
- **WHEN** cli.mjs spawns `cloakbrowser_fetcher.py` and the managed venv does not exist
- **THEN** `cloakbrowser-cli.sh preflight` SHALL create the managed venv and install `cloakbrowser`
- **AND** the spawn SHALL then proceed with the newly created venv python
