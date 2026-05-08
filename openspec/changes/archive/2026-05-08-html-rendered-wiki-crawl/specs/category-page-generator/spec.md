# Specification Delta: category-page-generator

## Capability 对齐（已确认）

- Capability: `category-page-generator`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认分类页需通过 categorymembers API 获取成员列表，与 parse 描述组合生成 index.md

## 规范真源声明

- 本文件是 `category-page-generator` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: category-parse-description
The system SHALL fetch the category page description via `action=parse&prop=text` to obtain introductory text.

#### Scenario: fetch-category-cards-description
- **WHEN** generating `Category:Cards` index page
- **THEN** the system SHALL call `action=parse&page=Category:Cards&prop=text`
- **AND** extract the text content from `.mw-parser-output` (excluding NewPP limit reports and cache comments)
- **AND** use this text as the introductory paragraph of the generated index.md

### Requirement: category-members-discovery
The system SHALL fetch category members via `action=query&list=categorymembers` for all pages in the category, across both ns=0 and ns=3000.

#### Scenario: fetch-category-cards-members
- **WHEN** generating `Category:Cards` index page
- **THEN** the system SHALL call `action=query&list=categorymembers&cmtitle=Category:Cards&cmlimit=max`
- **AND** iterate through all continuation tokens to collect all members
- **AND** include members from both ns=0 and ns=3000
- **AND** exclude category pages (ns=14) from the member list

### Requirement: category-index-assembly
The system SHALL assemble a Markdown index file combining the description and a sorted list of member links.

#### Scenario: assemble-cards-index
- **WHEN** the description is "All card related information is located here." and members include `A Thousand Cuts`, `Accuracy`, `Slay the Spire 2:Accelerant`
- **THEN** the output SHALL be:
  ```markdown
  All card related information is located here.

  ## Pages

  - [A Thousand Cuts](../A_Thousand_Cuts.md)
  - [Accuracy](../Accuracy.md)
  - [Slay the Spire 2:Accelerant](../Slay_the_Spire_2/Accelerant.md)
  ```
- **AND** member links SHALL use semantic-directory-mapping rules for relative paths
- **AND** members SHALL be sorted alphabetically by title

### Requirement: category-subcategory-listing
The system SHALL include subcategories in the index if present in the categorymembers response.

#### Scenario: category-with-subcategories
- **WHEN** `categorymembers` returns entries with `ns=14` (subcategories)
- **THEN** the system SHALL group them under a `## Subcategories` section
- **AND** link them using their mapped paths (e.g., `[Ironclad Cards](../Ironclad_Cards/index.md)`)
