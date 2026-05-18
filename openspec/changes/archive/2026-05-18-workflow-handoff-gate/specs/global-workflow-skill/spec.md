# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-workflow-skill`
- 来源: `proposal.md`
- 变更类型: `modified`
- 用户确认摘要: 在 Result Packaging 中增加 handoff_path 处理；新增 Handoff Gate 章节

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Structured result passthrough (modified)

The global workflow skill SHALL derive its final user-facing result from the CLI JSON contract.

When the CLI result contains `handoff_path`, the skill SHALL NOT pass through the result to the caller unchanged. Instead, the skill SHALL:
1. Recognize `handoff_path` as a chrome-agent-repo-bound signal
2. Invoke the Handoff Gate protocol (see requirement: handoff-gate-interpretation in `handoff-gate` spec)
3. Present the structured halting message defined in the Handoff Gate

When the CLI result does NOT contain `handoff_path`, the existing passthrough behavior SHALL apply unchanged.

#### Scenario: CLI result passthrough without handoff

- **WHEN** a routed CLI command completes
- **AND** the result does not contain `handoff_path`
- **THEN** the skill SHALL use the CLI JSON result as the source of truth for `result`, `summary`, `artifacts`, and remediation (unchanged from existing behavior)
- **AND** it MAY re-render that result for the caller
- **AND** it SHALL not claim success if the backend CLI result does not provide evidence for it

#### Scenario: CLI result with handoff blocks passthrough

- **WHEN** a routed CLI command completes
- **AND** the result contains `handoff_path`
- **THEN** the skill SHALL NOT pass through the result to the caller as normal output
- **THEN** the skill SHALL trigger the Handoff Gate protocol
- **THEN** the Handoff Gate SHALL take precedence over normal result packaging

### Requirement: Result packaging format (modified)

The preferred final shape of the skill's output SHALL be updated to include optional handoff fields.

The previous preferred shape:

```
result: <success|partial_success|failure>
command: <fetch|explore|crawl|doctor>
target: <url or runtime>
repo_ref: <repo://chrome-agent|path:...|env:CHROME_AGENT_REPO>
summary: <brief backend-grounded summary>
artifacts:
- <absolute path>
next_action: <none or remediation>
workflow: <content_retrieval|platform_analysis|runtime_support>
engine_path: <backend path summary>
```

The updated preferred shape SHALL additionally include:

```
handoff_path: <absolute path to handoff.md>   (present only when handoff was generated)
handoff_summary: <one-line failure summary>    (present only when handoff_path is present)
```

When `handoff_path` is present, `next_action` SHALL contain: "The problem must be resolved in the chrome-agent repository. See handoff document at <handoff_path>."

#### Scenario: handoff-fields-in-output

- **WHEN** the CLI result contains `handoff_path`
- **THEN** the skill's final output SHALL include `handoff_path` and `handoff_summary` lines
- **THEN** the skill SHALL render `next_action` with the chrome-agent-repo-bound text
- **THEN** the skill SHALL precede the output with a blank-line-separated Handoff Gate notice
