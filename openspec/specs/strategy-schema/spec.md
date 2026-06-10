# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-schema`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: grill session 确认——frontmatter 新增 `samples` 字段（page + label）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: Samples frontmatter field
The strategy YAML frontmatter SHALL support an optional `samples` field containing a list of sample page declarations.

Each entry SHALL have:
- `page` (string, required): URL path or cache-safe path identifying the page
- `label` (string, required): Human-readable description of the page's representative characteristics

#### Scenario: Strategy with samples
- **WHEN** strategy.md frontmatter includes:
  ```yaml
  domain: developer.nintendo.com
  samples:
    - page: "Packages/Docs/Guides/Online_Play_Guide/contents/Pages/Page_239857945.html"
      label: "复杂嵌套表格页面"
    - page: "Packages/Network/Guides/NX-Account_Guide/contents/Pages/Page_106359813.html"
      label: "纯文本无表格页面"
  ```
- **THEN** parsers SHALL extract the `samples` list as an array of dicts with `page` and `label` keys

#### Scenario: Strategy without samples
- **WHEN** strategy.md has no `samples` field
- **THEN** the field SHALL default to an empty list; no error SHALL be raised
