# Specification Delta

## Capability 对齐（已确认）

- Capability: `agents-governance`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: AGENTS.md 新增「Explore→Crawl Confirmation Gate」治理规则段，明确禁止 agent 在 explore 未完成确认前直接进入全量提取

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: explore-crawl-confirmation-gate

AGENTS.md SHALL include an «Explore→Crawl Confirmation Gate» section within the Governance Rules area. This section SHALL define the mandatory confirmation sequence an agent must follow after `explore` identifies a strategy gap, before proceeding to `crawl` or `fetch`.

The section SHALL state:

1. When `explore` returns `partial_success` with a strategy gap, the agent MUST follow the Explore Workflow Gates defined in the chrome-agent skill.
2. The agent MUST NOT proceed directly to `crawl` or `fetch` without user confirmation.
3. The agent MUST present at minimum: structure analysis, sample conversions, and self-check results.
4. When `explore` returns `failure`, the agent MUST surface the exact failure reason and remediation, MUST NOT fabricate a strategy or workaround, and MUST NOT attempt to fall back to a different extraction path without user approval.

#### Scenario: agent-reads-confirmation-gate

- **WHEN** an agent reads AGENTS.md after `explore` returns a strategy gap
- **THEN** the agent SHALL find an explicit rule prohibiting direct progression to `crawl` or `fetch`
- **THEN** the rule SHALL reference the chrome-agent skill for the detailed gate sequence
- **THEN** the rule SHALL enumerate minimum requirements: structure analysis, sample conversions, self-check results

#### Scenario: explore-failure-prohibition

- **WHEN** `explore` returns `result: "failure"`
- **THEN** the agent SHALL NOT attempt to create a strategy, run any extraction pipeline, or invent a workaround
- **THEN** the agent SHALL surface the failure reason and suggested remediation from the explore result as-is
- **THEN** the agent SHALL wait for user direction before taking any further action on the target URL

#### Scenario: section-placement

- **WHEN** AGENTS.md is rendered
- **THEN** the «Explore→Crawl Confirmation Gate» section SHALL appear within the Governance Rules area
- **THEN** it SHALL be placed after the existing «Intent Routing» subsection (which defines the route rules for fetch/explore/crawl) and before any subsequent governance section
