# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-skill-gates`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: chrome-agent SKILL.md 新增「Explore Workflow Gates」和「Explore Result Interpretation」章节，定义 Gate 1-4（结构分析确认→采样转换→LLM 自检→用户确认）以及 explore 输出字段的提取映射

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: skill-gate-structure-analysis

After `chrome-agent explore` returns with deep discovery data (or a strategy scaffold), the chrome-agent SKILL.md SHALL instruct the agent to present a structure analysis to the user before proceeding.

The agent SHALL extract and present:

1. Site type and platform identification (e.g., "MediaWiki 1.43 on wiki.gg")
2. Identified page types with representative examples for each type
3. Content map (nav structure, category hierarchy, or top-level sections)
4. Protection assessment (none / rate-limit / cloudflare / etc.)
5. Estimated page scale (total pages / articles, from API if available)

#### Scenario: structure-analysis-from-discover-data

- **WHEN** the explore result includes `discovery.content_profile` and `discovery.api`
- **THEN** the agent SHALL summarise the page type classification, nav sections, and content structure
- **THEN** the agent SHALL list detected API endpoints and their capabilities
- **THEN** the agent SHALL state the protection mechanism and estimated page count

#### Scenario: structure-analysis-from-scaffold

- **WHEN** the explore result includes `scaffold.path` but shallow discovery fields may be absent
- **THEN** the agent SHALL read the scaffold strategy file and extract: `structure.pages`, `api.base_url`, `protection_level`
- **THEN** the agent SHALL present these as the structure analysis

### Requirement: skill-gate-sample-conversion

After structure analysis is confirmed by the user, the SKILL.md SHALL instruct the agent to run sample conversions on 2-4 representative pages covering each identified page type, and present the results.

#### Scenario: sample-selection

- **WHEN** page types are confirmed
- **THEN** the agent SHALL select 2-4 sample pages, with at least one from each identified page type
- **THEN** the agent SHALL prioritize content-rich pages over stub/minimal pages

#### Scenario: sample-conversion-execution

- **WHEN** samples are selected
- **THEN** the agent SHALL fetch each sample page via the recommended fetcher/API path
- **THEN** the agent SHALL convert each sample to Markdown using the extraction rules from the strategy scaffold
- **THEN** the agent SHALL present each sample's content (title, frontmatter, markdown body) to the user

#### Scenario: quality-issues-flagging

- **WHEN** a sample Markdown contains HTML artifacts, broken template rendering, or garbled content
- **THEN** the agent SHALL highlight these issues explicitly in the presentation
- **THEN** the agent SHALL NOT present the sample as acceptable without noting the quality issues

### Requirement: skill-gate-llm-self-check

After sample conversion, the SKILL.md SHALL instruct the agent to perform an LLM-based self-check on the samples before asking for user confirmation.

The self-check SHALL evaluate:

1. Completeness: does the Markdown capture all content sections from the original page?
2. Formatting: are tables, lists, images, and links properly rendered in Markdown?
3. Broken links: do wiki-internal links resolve to existing output files?
4. Content fidelity: are key data values (stats, names, descriptions) preserved accurately?

#### Scenario: self-check-execution

- **WHEN** sample conversion is complete
- **THEN** the agent SHALL examine each sample Markdown for the four quality dimensions
- **THEN** the agent SHALL produce a pass/fail summary per dimension per sample
- **THEN** the agent SHALL present the summary to the user before showing individual sample details

#### Scenario: self-check-failure-remediation

- **WHEN** self-check identifies formatting or content fidelity issues
- **THEN** the agent SHALL propose extraction rule adjustments to fix the issues
- **THEN** the agent SHALL re-run conversion on affected samples with updated rules
- **THEN** the agent SHALL re-present the self-check summary after remediation (maximum two iterations)

### Requirement: skill-gate-user-confirmation

After self-check results are presented, the SKILL.md SHALL instruct the agent to wait for explicit user confirmation before proceeding to full extraction.

#### Scenario: confirmation-prompt

- **WHEN** samples and self-check results are presented
- **THEN** the agent SHALL ask the user to confirm: (a) content structure understanding is correct, (b) sample conversion quality is acceptable, (c) ready to proceed to full extraction
- **THEN** the agent SHALL use the ask_user tool or equivalent interactive mechanism
- **THEN** the agent SHALL NOT proceed to `crawl` or `fetch` without explicit user confirmation

#### Scenario: confirmation-declined

- **WHEN** the user indicates the samples are not acceptable or requests changes
- **THEN** the agent SHALL apply the requested adjustments (strategy rules, extraction config, sample selection)
- **THEN** the agent SHALL re-run sample conversion and self-check
- **THEN** the agent SHALL re-present for confirmation

### Requirement: skill-explore-result-interpretation

The SKILL.md SHALL include a section mapping the explore result fields to their purpose and the gate in which they are used.

#### Scenario: field-mapping-table

- **WHEN** the agent reads the «Explore Result Interpretation» section
- **THEN** the section SHALL contain a table mapping these fields: `discovery.content_profile`, `discovery.api`, `discovery.protection`, `discovery.engine_chain`, `scaffold.path`, `samples`, `self_check`
- **THEN** each field SHALL have a «Purpose» column and a «Gate» column indicating which gate uses that field

#### Scenario: failure-result-handling

- **WHEN** explore returns `result: "failure"`
- **THEN** the «Explore Result Interpretation» section SHALL instruct the agent to surface the exact error and remediation
- **THEN** it SHALL state: "Do NOT invent a fallback strategy or workaround"
