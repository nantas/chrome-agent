# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-workflow-skill`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认 workflow skill 继续依赖 CLI preflight，但默认仓库解析契约改为 env-first；当 `CHROME_AGENT_REPO` 缺失或无效时，skill 应停止并要求用户显式指定仓库路径

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: CLI-backed preflight
The global workflow skill SHALL use the repo-backed CLI as its only supported execution backend.

Before routing user work, the skill SHALL validate backend readiness through `chrome-agent doctor --format json`, using the CLI's env-first repository resolution contract.

#### Scenario: Backend ready via env default
- **WHEN** `chrome-agent doctor --format json` reports that `CHROME_AGENT_REPO` resolves to a valid repository
- **THEN** the skill SHALL continue to the routed workflow command
- **AND** it SHALL preserve the resolved repository and backend remediation details from the CLI

#### Scenario: Backend not ready due to missing or invalid env
- **WHEN** the CLI doctor result reports `failure` because `CHROME_AGENT_REPO` is missing or invalid
- **THEN** the skill SHALL stop before dispatching `fetch`, `explore`, or `crawl`
- **AND** it SHALL return the doctor-provided remediation instead of improvising a non-CLI fallback path
- **AND** it SHALL not silently depend on repo-registry as the default repository source

### Requirement: Structured result passthrough
The global workflow skill SHALL derive its final user-facing result from the CLI JSON contract.

#### Scenario: CLI result passthrough
- **WHEN** a routed CLI command completes
- **THEN** the skill SHALL use the CLI JSON result as the source of truth for `result`, `summary`, `artifacts`, and remediation
- **AND** it MAY re-render that result for the caller
- **AND** it SHALL not claim success if the backend CLI result does not provide evidence for it
- **AND** it SHALL preserve the CLI's env-first repository resolution semantics in any surfaced `repo_ref` or remediation text
