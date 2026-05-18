# Specification Delta

## Capability 对齐（已确认）

- Capability: `handoff-gate`
- 来源: `proposal.md`
- 变更类型: `new`
- 用户确认摘要: SKILL.md 中的 Handoff Gate 闸门——当 CLI 返回包含 handoff_path 时，skill 必须停止工作流并路由用户到 chrome-agent 仓库修复

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: handoff-gate-interpretation

The SKILL.md SHALL define a Handoff Gate that interprets CLI results containing a `handoff_path` field.

When the CLI result contains `handoff_path`:
1. The skill SHALL NOT proceed to any further workflow dispatch (fetch / explore / crawl / scrape)
2. The skill SHALL NOT attempt to interpret or re-route the failure as a different command
3. The skill SHALL NOT attempt to work around the problem by calling engines directly or bypassing the CLI
4. The skill SHALL present the handoff_path and handoff_summary to the user
5. The skill SHALL instruct the user to fix the issue in the chrome-agent repository before retrying

#### Scenario: handoff-gate-halts-workflow

- **WHEN** a CLI command returns a JSON result containing `handoff_path`
- **THEN** the skill SHALL recognize this as a chrome-agent-repo-bound failure
- **THEN** the skill SHALL stop all further workflow dispatch
- **THEN** the skill SHALL NOT attempt to re-run the same command with different parameters
- **THEN** the skill SHALL NOT attempt alternative fetching strategies outside the CLI backend

#### Scenario: handoff-gate-forbidden-workarounds

- **WHEN** a CLI result contains `handoff_path`
- **THEN** the skill SHALL NOT:
  - write a custom curl/wget/request script as a substitute
  - call chrome-cdp or chrome-devtools-mcp directly as a bypass
  - use the Scrapling CLI directly without going through the chrome-agent CLI
  - fabricate a strategy or workaround
- **THEN** the only allowed action is: present the handoff and stop

### Requirement: handoff-gate-presentation

The SKILL.md SHALL define a structured user-facing message when the Handoff Gate is triggered.

The message SHALL contain:
1. A halting notice: "工作流中断"
2. The failure summary from `handoff_summary`
3. The absolute path to the handoff document
4. An instruction to switch to the chrome-agent repository
5. The steps to follow in the chrome-agent repository (review handoff, classify issue, create change, fix, verify)
6. The original CLI command for reproduction

#### Scenario: handoff-presentation-format

- **WHEN** the Handoff Gate is triggered
- **THEN** the skill SHALL present the handoff to the user in a structured format
- **THEN** the preferred format SHALL be:

```
result: failure
handoff_path: <absolute path>
handoff_summary: <one-line summary>

Workflow interrupted. This problem belongs in the chrome-agent repository.

Handoff document: <handoff_path>

To fix:
1. Switch to the chrome-agent repository
2. Read the handoff document for full context
3. Classify the issue (P-line: pipeline / S-line: strategy / W-line: workflow)
4. Create an openspec change proposal
5. Implement the fix
6. Re-run the original command to verify

Original command: <CLI command that was run>
```

#### Scenario: handoff-with-additional-context

- **WHEN** the CLI result includes other fields beyond `handoff_path` and `handoff_summary` (e.g., `summary`, `artifacts`, `engine_path`)
- **THEN** the skill MAY include these in the presentation
- **THEN** the skill SHALL NOT re-order or re-interpret the fields
- **THEN** the handoff_path field SHALL always be presented prominently

### Requirement: handoff-gate-differing-failure-handling

The Handoff Gate SHALL distinguish between two types of failure results:

1. **Chrome-agent-repo-bound failures** (result contains `handoff_path`): Skill MUST halt and route to chrome-agent repo.
2. **Caller-side failures** (result = `"failure"`, no `handoff_path`): Skill MUST pass through the `next_action` field as the caller-side remediation.

#### Scenario: caller-side-failure-passthrough

- **WHEN** the CLI returns `result: "failure"` without `handoff_path`
- **THEN** the skill SHALL NOT trigger the Handoff Gate
- **THEN** the skill SHALL return the CLI result as-is (same behavior as current implementation)
- **THEN** the `next_action` field SHALL guide the caller on what to fix (e.g., set CHROME_AGENT_REPO, provide a valid URL)

#### Scenario: mixed-failure-resolution

- **WHEN** the CLI returns `result: "partial_success"` with `handoff_path`
- **THEN** the skill SHALL still trigger the Handoff Gate (any `handoff_path` presence triggers the gate)
- **THEN** the skill SHALL NOT accept partial results while chrome-agent-repo-bound issues remain unresolved
