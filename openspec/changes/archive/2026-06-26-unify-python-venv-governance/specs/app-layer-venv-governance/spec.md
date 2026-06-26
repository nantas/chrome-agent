# Specification Delta

## Capability 对齐（已确认）

- Capability: `app-layer-venv-governance`
- 来源: `proposal.md` → New Capabilities
- 变更类型: `new`
- 用户确认摘要: grill 决策树 Q1(B) 应用层单 venv + Q2(A) 根 requirements.txt + Q5(A) 懒触发生命周期

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Single Root Dependency Manifest

The system SHALL maintain a single `requirements.txt` at the repository root that declares all application-layer Python dependencies: `beautifulsoup4`, `pyyaml`, `selectolax`, `markdownify`, `requests` (used by `scripts/pipeline/client.py`, `scripts/explore/probe_chain.py`, and 4 other modules). The file SHALL be the single source of truth for application-layer dependency versions.

#### Scenario: Developer inspects application-layer dependencies
- **WHEN** a developer or tool reads the repository
- **THEN** exactly one `requirements.txt` at the repo root SHALL list all application-layer Python dependencies
- **AND** the file `scripts/explore/requirements.txt` SHALL NOT exist

#### Scenario: Dependency change affects both explore and pipeline
- **WHEN** a shared dependency (e.g., `selectolax` used by `lib/extraction/converter.py`) is upgraded
- **THEN** only the root `requirements.txt` SHALL be updated

### Requirement: resolveAppPython Resolver

The system SHALL provide a `resolveAppPython(repoRoot)` function in `scripts/lib/python-resolver.mjs` that resolves the Python interpreter for application-layer spawns. Priority: `CHROME_AGENT_PYTHON` environment variable > `<repoRoot>/.venv/bin/python` (if it exists and is executable) > system `python3`.

#### Scenario: Repo venv exists
- **WHEN** `<repoRoot>/.venv/bin/python` exists
- **THEN** `resolveAppPython(repoRoot)` SHALL return the absolute path to `<repoRoot>/.venv/bin/python`

#### Scenario: No repo venv
- **WHEN** `<repoRoot>/.venv/bin/python` does NOT exist
- **THEN** `resolveAppPython(repoRoot)` SHALL return the string `"python3"`

#### Scenario: Environment variable overrides all
- **WHEN** `CHROME_AGENT_PYTHON` environment variable is set
- **THEN** `resolveAppPython(repoRoot)` SHALL return the environment variable value regardless of venv existence

### Requirement: Lazy-Trigger Venv Creation

The system SHALL provide `scripts/repo-venv.sh preflight` that follows the same preflight pattern as `scripts/scrapling-cli.sh preflight`: detect whether `.venv/bin/python` is runnable with `import bs4, yaml, selectolax, markdownify, requests`, and if not, automatically create the venv via `uv venv` and install dependencies from root `requirements.txt`.

#### Scenario: First run on clean clone
- **WHEN** `scripts/repo-venv.sh preflight` is invoked on a repository without `.venv/`
- **THEN** it SHALL create the venv at `<repoRoot>/.venv/` using `uv venv --python <system_python>`
- **AND** SHALL install all dependencies from `requirements.txt` via `uv pip install`
- **AND** SHALL emit `STATUS=repaired` and `SOURCE=installed` (same output format as scrapling-cli.sh)

#### Scenario: Venv already valid
- **WHEN** `scripts/repo-venv.sh preflight` is invoked and `.venv/bin/python` already importable with all dependencies
- **THEN** it SHALL emit `STATUS=available` and `SOURCE=managed`
- **AND** SHALL NOT reinstall or modify the venv

#### Scenario: Doctor explore_deps check
- **WHEN** `chrome-agent doctor --format json` runs `explore_deps`
- **THEN** it SHALL use `resolveAppPython(repoRoot)` to select the Python interpreter for `import bs4, yaml`

### Requirement: Application-Layer Spawn Points

All application-layer `spawnSync` calls in `scripts/chrome-agent-cli.mjs` that invoke Python scripts SHALL use `resolveAppPython(repoRoot)` instead of hardcoded `"python3"`. These include: explore `main.py`, explore `freeze.py`, explore `iterate.py`, and pipeline `-m scripts.pipeline`.

#### Scenario: Explore freeze spawn
- **WHEN** `runExplore` initiates the freeze step
- **THEN** `spawnSync(resolveAppPython(repoRoot), [path.join(repoRoot, "scripts", "explore", "freeze.py"), ...])` SHALL be used

#### Scenario: Pipeline spawn
- **WHEN** pipeline `-m scripts.pipeline` is spawned
- **THEN** `spawnSync(resolveAppPython(repoRoot), ["-m", "scripts.pipeline", ...])` SHALL be used

### Requirement: Test Runner Python Source

The test runner invocation documented in `08-tech-stack.md` SHALL use `.venv/bin/python` instead of system `python3`: `.venv/bin/python scripts/test_runner.py all`. The test runner script itself (`shebang: #!/usr/bin/env python3`) MAY remain unchanged; the governance change is at the invocation level.

#### Scenario: Running unit tests after initialization
- **WHEN** user runs `.venv/bin/python scripts/test_runner.py unit`
- **THEN** `selectolax` and all other application-layer dependencies SHALL be importable
- **AND** the 2 existing `ModuleNotFoundError: selectolax` test errors SHALL be resolved
