# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 加固 explore 后端的错误处理——移除静默 try/catch 和 legacy fallback，deep discovery 管线失败时返回明确 failure 而非降级到 "strategy gap"

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: explore-command-backend

The system SHALL route `explore` into the full deep-discovery workflow when no strategy exists, while retaining the existing behavior when a strategy IS matched.

Deep discovery SHALL be the only path for strategy-gap scenarios. The legacy backend-detection fallback (HTML fetch → DOM fingerprint → bootstrap recommendation) SHALL NOT be invoked.

#### Scenario: strategy-matched

- **WHEN** `explore <url>` is called and a strategy exists in the registry for the domain
- **THEN** the system SHALL continue with the existing behavior (load strategy, return structured report)
- **THEN** no change in this scenario

#### Scenario: strategy-gap

- **WHEN** `explore <url>` is called and no strategy exists for the domain
- **THEN** the system SHALL NOT simply return "strategy gap"
- **THEN** the system SHALL NOT invoke legacy backend-detection fallback
- **THEN** the system SHALL enter the deep discovery pipeline (see `explore-workflow` spec)
- **THEN** the system SHALL proceed through: preflight → probe chain → API discovery → structure mapping → protection identification
- **THEN** the system SHALL engage interactive scope confirmation with the user
- **THEN** the system SHALL generate strategy scaffold
- **THEN** the system SHALL produce and self-check samples
- **THEN** the system SHALL present results for user review
- **THEN** on approval, the system SHALL freeze the strategy

## ADDED Requirements

### Requirement: explore-preflight-failure

When deep discovery pipeline dependencies are missing, the system SHALL return a clear failure result with actionable remediation, not a degraded "strategy gap" report.

#### Scenario: python-deps-missing

- **WHEN** `runExplore()` checks Python dependencies (`bs4`, `yaml`) and one or more are not importable
- **THEN** the system SHALL return `result: "failure"` with `summary` containing the missing package names and installation command
- **THEN** `next_action` SHALL include an exact `pip3 install` command
- **THEN** `engine_path` SHALL include `strategy_registry -> strategy_gap -> preflight_failed`
- **THEN** the system SHALL NOT proceed to probe chain or legimport yamlcy fallback

#### Scenario: deep-discovery-execution-failure

- **WHEN** deep discovery pipeline (`scripts/explore/main.py`) executes but returns non-zero exit code
- **THEN** the system SHALL return `result: "failure"` with `summary` containing the first 500 characters of stderr
- **THEN** `engine_path` SHALL include `strategy_registry -> strategy_gap -> deep_discovery_failed`
- **THEN** the system SHALL NOT fall through to legacy behavior

### Requirement: explore-legacy-fallback-removal

The legacy fallback path that scrapes raw HTML and runs backend detection SHALL be removed from `runExplore()`.

#### Scenario: no-legacy-fallback

- **WHEN** deep discovery is unavailable or fails
- **THEN** `runExplore()` SHALL NOT attempt to fetch HTML via `runEngineFetch` or invoke `detectBackend`
- **THEN** the function SHALL NOT produce a "strategy gap" result through the legacy code path
- **THEN** all code related to legacy fallback (HTML fetch, backend detection, `bootstrap-strategy` suggestion from explore) SHALL be removed from `runExplore()`
