# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-capability-cli`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认整个 CLI 默认解析链路改为 env-first；`CHROME_AGENT_REPO` 为默认权威；若 env 缺失或无效则停止并要求用户显式指定仓库路径；repo-registry 仅保留给显式 repo-ref 调用路径

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Repo-backed execution authority
The CLI SHALL treat the target repository as the execution authority for `explore`, `fetch`, and `crawl`.

The global CLI SHALL only normalize input, resolve the repository, and dispatch into the repository-local workflow. Repository-local `AGENTS.md` and `openspec/specs/` SHALL remain authoritative for workflow routing and execution behavior.

#### Scenario: Repository-local dispatch
- **WHEN** `chrome-agent fetch <target>` or `chrome-agent explore <target>` is invoked
- **THEN** the global CLI SHALL dispatch the request into the resolved target repository
- **AND** the downstream execution SHALL read and follow the target repository `AGENTS.md`
- **AND** the global CLI SHALL not replace repository routing logic with a separate parallel ruleset

### Requirement: Repo resolution precedence
The CLI SHALL resolve the target repository using explicit override first, `CHROME_AGENT_REPO` second, and failure-with-remediation third.

The default resolution precedence SHALL be:
1. explicit CLI override, if supplied
2. `CHROME_AGENT_REPO` environment variable
3. failure with remediation guidance

Repo-registry MAY still be used, but only when the caller explicitly supplies a `repo://...` override.

#### Scenario: Explicit override resolution
- **WHEN** a caller supplies `--repo <path|repo://id>`
- **THEN** the CLI SHALL prefer that override over the default env-first resolution path

#### Scenario: Environment default resolution
- **WHEN** no explicit `--repo` override is supplied
- **AND** `CHROME_AGENT_REPO` points to an existing repository containing `AGENTS.md`
- **THEN** the CLI SHALL use `CHROME_AGENT_REPO` as the default repository source
- **AND** it SHALL not read repo-registry as part of that default hot path

#### Scenario: Repository resolution failure
- **WHEN** no explicit `--repo` override is supplied
- **AND** `CHROME_AGENT_REPO` is missing or does not point to a valid repository
- **THEN** the CLI SHALL fail before dispatch
- **AND** it SHALL return a remediation message telling the caller to set `CHROME_AGENT_REPO` or supply an explicit `--repo <path|repo://id>`

#### Scenario: Explicit repo-ref resolution
- **WHEN** the caller explicitly supplies `--repo repo://chrome-agent`
- **THEN** the CLI MAY resolve that repo reference through repo-registry
- **AND** that explicit path SHALL remain outside the default env-first resolution flow

### Requirement: JSON-first result contract
The CLI SHALL produce a JSON-first result contract for all first-class commands.

The JSON result SHALL include at least:
- `result`
- `command`
- `target`
- `repo_ref`
- `summary`
- `artifacts`
- `next_action`
- `workflow`
- `engine_path`

#### Scenario: Structured success result
- **WHEN** a command completes successfully
- **THEN** the CLI SHALL emit a machine-readable result object with all fields above
- **AND** `workflow` SHALL identify whether the command executed `content_retrieval`, `platform_analysis`, `runtime_support`, or another explicit backend workflow
- **AND** `engine_path` SHALL summarize the actual engine or escalation path used for execution

#### Scenario: Resolution mode disclosure
- **WHEN** a command completes after default env-based resolution
- **THEN** the CLI SHALL expose a machine-readable indicator that the repository was resolved from the default environment-variable path
- **AND** it SHALL not label that path as a fallback

## REMOVED Requirements

### Requirement: Registry-first resolution
**Reason**: High-frequency skill-first usage should not require repo-registry lookup on the default runtime path when `CHROME_AGENT_REPO` is already configured.
**Migration**: Treat `CHROME_AGENT_REPO` as the default repository source, and use explicit `--repo repo://...` when registry-based resolution is intentionally needed.
