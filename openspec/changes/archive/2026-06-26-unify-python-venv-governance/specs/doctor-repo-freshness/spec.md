# Specification Delta

## Capability 对齐（已确认）

- Capability: `doctor-repo-freshness`
- 来源: `proposal.md` → Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: grill Q5(A) 懒触发 repo venv + Q6(A) test_runner 走 venv

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: explore_deps Check Uses resolveAppPython

The `explore_deps` doctor check SHALL use `resolveAppPython(repoRoot)` (from `scripts/lib/python-resolver.mjs`) as the Python interpreter for `import bs4, yaml`. It SHALL NOT hardcode `"python3"`.

#### Scenario: explore_deps check with application-layer venv present
- **WHEN** `chrome-agent doctor --format json` runs and `.venv/bin/python` exists with `bs4` and `yaml` importable
- **THEN** `explore_deps` SHALL report `ok: true` with detail `"bs4, yaml available"`

#### Scenario: explore_deps check triggers lazy venv creation
- **WHEN** `chrome-agent doctor` runs and `.venv/bin/python` does not exist
- **THEN** `resolveAppPython(repoRoot)` SHALL return `"python3"` (fallback)
- **AND** `explore_deps` MAY report the dependency as missing (no auto-install from doctor context)
- **AND** the first application-layer spawn SHALL trigger lazy venv creation via `scripts/repo-venv.sh preflight`

### Requirement: version_cloakbrowser Check Uses Managed Venv

The `version_cloakbrowser` doctor check SHALL use the managed venv Python at the path declared in `configs/engine-versions.json` `cloakbrowser.detection.managed_path`. It SHALL NOT use system `python3`.

#### Scenario: version_cloakbrowser check with managed venv present
- **WHEN** `chrome-agent doctor --format json` runs and the managed venv at `$HOME/.cache/chrome-agent-cloakbrowser/bin/python` can `import cloakbrowser` and read `__version__`
- **THEN** `version_cloakbrowser` SHALL report `ok: true` with the detected version

#### Scenario: version_cloakbrowser check triggers lazy install
- **WHEN** `chrome-agent doctor --format json` runs and the managed venv does not exist
- **THEN** the check SHALL trigger `scripts/cloakbrowser-cli.sh preflight` to create the managed venv
- **AND** `version_cloakbrowser` SHALL report `ok: true` after successful preflight install

### Requirement: explore_deps Handoff Removed

The `explore` command's preflight logic that generates a handoff file on `explore_deps_missing` SHALL be removed. The dependency check is handled at the spawn level via `resolveAppPython(repoRoot)` which falls back to system `python3` if `.venv` is unavailable; the explore pipeline itself SHALL not block on missing deps at the CLI routing level.

#### Scenario: Explore command runs without venv
- **WHEN** `chrome-agent explore <url>` runs and `.venv/bin/python` does not exist
- **THEN** the spawn SHALL use system `python3` (fallback)
- **AND** SHALL NOT generate an `explore_deps_missing` handoff file
- **AND** any `ModuleNotFoundError` from the Python script SHALL be reported as a normal spawn failure
