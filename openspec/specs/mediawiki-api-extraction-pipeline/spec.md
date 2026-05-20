# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 修复 `assemble.py` 中孤儿 index 生成问题；添加 index.md 写入防覆盖保护

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本文件是 `fix-pipeline-quality-gaps` 中同名 spec 的增量补充

## MODIFIED Requirements

### Requirement: list-page-index-existence-check

`run_assemble()` SHALL first verify that a list page exists in the manifest before generating its directory index.md. If the list page title from `taxonomy.list_pages` is not present in the manifest pages array, the assembly SHALL skip that entry entirely and SHALL NOT create an empty index.md.

#### Scenario: skip-nonexistent-list-page

- **WHEN** `taxonomy.list_pages` contains an entry `Mechanics: "Mechanics"`
- **AND** no page with title "Mechanics" exists in `manifest["pages"]`
- **AND** no entity pages have `target_directory: "Mechanics"`
- **THEN** assembly SHALL NOT create `Mechanics/index.md`
- **AND** assembly SHALL log a warning: "Skipping list page 'Mechanics': not found in manifest"

#### Scenario: create-index-only-when-content-exists

- **WHEN** `taxonomy.list_pages` contains an entry `Items: "Items"`
- **AND** page "Items" exists in `manifest["pages"]`
- **AND** the Items page was successfully converted (has content)
- **THEN** assembly SHALL create `items/index.md` with the Items page content

### Requirement: index-overwrite-protection

When generating directory index.md files from `taxonomy.list_pages`, the assembly phase SHALL only process the page title mapped from `taxonomy.list_pages` if that page has `is_list_page: true` in the manifest. This prevents excluded pages (e.g., Version History) whose target_directory happens to point to an existing directory from overwriting the correct index.

#### Scenario: excluded-page-does-not-overwrite-index

- **WHEN** `taxonomy.list_pages` contains `Version History: "Version_History"`
- **AND** a page titled "Version History" exists in `manifest["pages"]` with `target_directory: "items"`
- **AND** a page titled "Items" also exists with `target_directory: "items"` and `is_list_page: true`
- **THEN** assembly SHALL only write `items/index.md` using the "Items" page content
- **AND** SHALL NOT overwrite it with "Version History" content
