# Specification Delta

## Capability 对齐（已确认）

- Capability: `isaac-strategy-dir-completeness`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: Isaac wiki 策略文件 api.homepage.categories 缺少首页 gallery 中的 Completion Marks 和 Attributes 的 dir 映射

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: homepage-categories-cover-all-gallery-links

The Isaac wiki strategy file (`sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`) SHALL include `dir` mappings for all homepage gallery links that are not in the `exclude_categories` list.

Specifically, the following entries SHALL be added to `api.homepage.categories`:

- `{name: "Completion Marks", dir: "completion_marks"}`
- `{name: "Attributes", dir: "attributes"}`

These use underscores (matching existing convention like `completion_marks` in other wikis) rather than hyphens.

#### Scenario: strategy-dir-mapping-complete

- **GIVEN** the homepage gallery returns 22 category links
- **AND** `exclude_categories` is `["Music", "Modding", "Version History"]`
- **WHEN** the strategy's `api.homepage.categories` is loaded
- **THEN** every non-excluded gallery link SHALL have a corresponding entry with a `dir` field
- **AND** "Completion Marks" SHALL map to `dir: "completion_marks"`
- **AND** "Attributes" SHALL map to `dir: "attributes"`
