# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: deep discovery 管线增加启动前依赖预检查（explore_python_deps），缺失时硬阻断并给出安装指令

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: pipeline-dependency-preflight

The deep discovery pipeline (`scripts/explore/main.py`) SHALL verify all required Python dependencies at startup and exit with a clear error message if any are missing. The CLI caller (`runExplore()`) SHALL run a separate preflight check before spawning the pipeline process, and SHALL NOT silently catch import errors.

#### Scenario: main-py-dependency-self-check

- **WHEN** `python3 scripts/explore/main.py` is invoked
- **THEN** the script SHALL attempt to import `bs4` and `yaml` before executing any pipeline phase
- **THEN** if either import fails, the script SHALL print to stderr: `FATAL: Missing dependencies: <package-list>`
- **THEN** the script SHALL print to stderr: `Install with: pip3 install <package-list>`
- **THEN** the script SHALL exit with code 1

#### Scenario: main-py-dependencies-present

- **WHEN** `python3 scripts/explore/main.py` is invoked and all dependencies are importable
- **THEN** the script SHALL proceed to the normal pipeline execution without any additional output from the preflight check

#### Scenario: cli-preflight-before-spawn

- **WHEN** `runExplore()` prepares to spawn `scripts/explore/main.py`
- **THEN** the system SHALL first run `runExplorePythonDepsCheck()` to verify `bs4` and `yaml` are importable
- **THEN** if the preflight fails, the system SHALL return `result: "failure"` with installation instructions
- **THEN** the system SHALL NOT invoke `spawnSync` for the pipeline process

#### Scenario: deps-file-declaration

- **WHEN** a developer or operator inspects `scripts/explore/`
- **THEN** a `requirements.txt` file SHALL be present listing `beautifulsoup4>=4.12` and `pyyaml>=6.0`
- **THEN** the file SHALL serve as the authoritative dependency declaration for the explore pipeline
