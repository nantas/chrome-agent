# Specification Delta

## Purpose

Define sample recommendations and structural quality checks for the explore workflow.


## Capability 对齐（已确认）

- Capability: `explore-scaffold`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: grill session 确认——explore 流程新增样本选取步骤

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## Requirements

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

### Requirement: self-check-precision
S5 SHALL 按完整词或有界完整短语检测重复，不匹配相邻单词的局部字符。S6 SHALL 逐表计直接结构行，避免嵌套双计数，不能因 mw-collapsible 而排除游戏数据。

#### Scenario: precision-and-loss
- WHEN 输入 with the / This is
- THEN S5 通过；hero hero 仍失败。
- WHEN 嵌套等级子表在转换中丢失
- THEN S6 失败。

### Requirement: rendered-structure-checks
S6 SHALL 比较可见内容结构，排除空白／纯嵌套布局行并计入多行表头折叠；真实数据行损失仍须失败。S8 SHALL 对照渲染后的标题文本，不能因链接语法或标点空白误报缺节。S5 版本格式扫描 SHALL 排除 URL 编号，但原文重复不能静默删改。

#### Scenario: linked-heading-and-url
- WHEN 标题含超链接、标点，正文链接带字母数字散列
- THEN 标题与格式检查通过；真实缺标题和未分隔版本仍失败。
