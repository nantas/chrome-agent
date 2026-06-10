# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-scaffold`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: grill session 确认——explore 流程新增样本选取步骤

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Sample recommendation during explore
The explore workflow SHALL provide a sample recommendation step where `scope_confirmer.recommend_samples()` analyzes discovered page structure characteristics and presents a recommended sample list to the user.

- The agent SHALL analyze page diversity (table presence, nesting depth, image density, content length) to recommend a minimal set covering all structural variants.
- The user SHALL review the recommendation and manually write the confirmed `samples` field into the strategy frontmatter.

> **Note**: Full end-to-end wiring (explore auto-writing `samples` to strategy frontmatter) is deferred to a future enhancement. The current scope provides the recommendation infrastructure (`recommend_samples()`) and the frontmatter schema (`samples` field) so that manual integration is straightforward.

#### Scenario: Agent recommends diverse samples
- **WHEN** explore discovers pages with mixed structures (some with tables, some without)
- **THEN** the agent SHALL recommend at least one representative from each structural category

#### Scenario: User reviews sample recommendation
- **WHEN** the agent presents a recommended sample list
- **THEN** the user SHALL be able to confirm, add, or remove entries before the list is persisted

#### Scenario: Samples written to strategy (manual)
- **WHEN** the user confirms the sample list
- **THEN** the user SHALL write the `samples` field to `sites/strategies/<domain>/strategy.md` frontmatter based on the recommendation
