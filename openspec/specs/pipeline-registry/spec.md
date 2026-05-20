# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-registry`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 确保 `taxonomy.list_pages` 条目与发现到的页面对齐，assembly 据此判断是否生成 index

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: list-pages-manifest-alignment

`build_pipeline()` (registry) SHALL provide a method or signal that indicates which entries in `taxonomy.list_pages` have corresponding pages in the manifest. This information SHALL be consumed by `run_assemble()` to decide whether to generate index files.

#### Scenario: manifest-gaps-reported

- **WHEN** `taxonomy.list_pages` contains an entry `Mechanics: "Mechanics"`
- **AND** the manifest does not contain a page titled "Mechanics"
- **AND** no entity pages have `target_directory: "Mechanics"`
- **THEN** the pipeline SHALL report this as a gap in the discovery summary
- **AND** assembly SHALL skip generating `Mechanics/index.md`

### Requirement: assembly-discovery-consistency

The assemble phase SHALL only create index.md files for directories that have at least one discovered and converted page, OR for list pages that were explicitly discovered and marked `is_list_page: true` in the manifest. Stub directories without content SHALL NOT be created.

#### Scenario: no-stub-directories

- **WHEN** the manifest has no pages with `target_directory: "Mechanics"`
- **THEN** assembly SHALL NOT create the `Mechanics/` directory
- **AND** SHALL NOT create `Mechanics/index.md`
