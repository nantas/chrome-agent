# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-registry`
- 来源: `proposal.md` → Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: grill Q3b(C) cloakbrowser 独立 managed venv + Q4a(A) Chromium 留包默认 + Q4b(A) uv+py3.11

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: CloakBrowser Managed Venv Preflight

The system SHALL provide `scripts/cloakbrowser-cli.sh preflight` that follows the same preflight pattern as `scripts/scrapling-cli.sh preflight`: detect whether the managed venv at `$HOME/.cache/chrome-agent-cloakbrowser/bin/python` can `import cloakbrowser`, and if not, automatically create the managed venv via `uv venv --python 3.11` and install `cloakbrowser` via `uv pip install`.

#### Scenario: First run, cloackbrowser venv nonexistent
- **WHEN** `scripts/cloakbrowser-cli.sh preflight` is invoked on a system without the managed venv
- **THEN** it SHALL create the managed venv at `$HOME/.cache/chrome-agent-cloakbrowser/` using `uv venv --python 3.11`
- **AND** SHALL install `cloakbrowser` via `uv pip install cloakbrowser`
- **AND** SHALL emit `STATUS=repaired` and `SOURCE=installed`

#### Scenario: Managed venv already valid
- **WHEN** managed venv exists and `import cloakbrowser` succeeds
- **THEN** preflight SHALL emit `STATUS=available` and `SOURCE=managed`
- **AND** SHALL NOT reinstall

### Requirement: CloakBrowser engine-versions.json managed_path

The `cloakbrowser` entry in `configs/engine-versions.json` SHALL declare:
- `detection.managed_path`: `"$HOME/.cache/chrome-agent-cloakbrowser/bin/python"` (was `null`)
- `detection.method`: `"python_importlib"` (was `"python_attribute"`)
- `detection.command`: uses the managed venv python, not bare `python3`

#### Scenario: Doctor cloakbrowser version check
- **WHEN** `chrome-agent doctor --format json` invokes `scripts/engine-version-check.sh`
- **THEN** the cloakbrowser detection SHALL use `$HOME/.cache/chrome-agent-cloakbrowser/bin/python` to import and read `cloakbrowser.__version__`
- **AND** SHALL NOT use system `python3`

### Requirement: CloakBrowser Chromium Binary Isolation

The patched Chromium binary downloaded by `cloakbrowser` SHALL remain at its upstream default location `~/.cloakbrowser/chromium-{version}/`. The managed venv at `$HOME/.cache/chrome-agent-cloakbrowser/` governs only the Python package; it SHALL NOT manage or relocate the Chromium binary.

#### Scenario: Chromium auto-download on first use
- **WHEN** `cloakbrowser.launch()` is first invoked inside the managed venv
- **THEN** the patched Chromium SHALL download to `~/.cloakbrowser/chromium-{version}/` (upstream default)
- **AND** the managed venv SHALL NOT intercept or redirect this download

### Requirement: Redundant Script Cleanup

The existing `scripts/cloakbrowser-preflight.sh` (read-only detection only, no install capability) SHALL be removed. Its functionality is superseded by `scripts/cloakbrowser-cli.sh preflight`.

#### Scenario: Legacy preflight no longer referenced
- **WHEN** any tool or workflow references `scripts/cloakbrowser-preflight.sh`
- **THEN** it SHALL be updated to reference `scripts/cloakbrowser-cli.sh preflight` instead
