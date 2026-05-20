# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 既有 spec: `openspec/specs/pipeline-converters/spec.md`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源（delta）
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: infobox-link-source-dir-passthrough

`_extract_selectolax()` SHALL 接收 `source_dir: str = ""` 参数，并在调用 `render_inline_children_fn` 时将其作为 `source_dir` 关键字参数传入。

`extract_infobox()` SHALL 接收 `source_dir: str = ""` 参数，并在调用 `_extract_selectolax()` 时透传。

`HtmlToMarkdownConverter._render_infobox_table()` SHALL 在调用 `extract_infobox()` 时传入当前的 `source_dir` 参数值。

#### Scenario: infobox-link-uses-correct-relative-path

- **WHEN** 转换 `bosses/Ultra_Greed.md` 的 infobox
- **AND** infobox 包含指向 `Endings` 页面的链接（`target_directory=endings, target_filename=index.md`）
- **THEN** infobox 内链接 SHALL 为 `[Ending 18](../endings/index.md)`
- **AND** SHALL NOT 为 `[Ending 18](endings/index.md)`

#### Scenario: infobox-link-same-directory

- **WHEN** 转换 `items/Item_Pool.md` 的 infobox
- **AND** infobox 包含指向 `Item Pool` 页面的链接（`target_directory=items, target_filename=Item_Pool.md`）
- **THEN** infobox 内链接 SHALL 为 `[Item Pool](Item_Pool.md)`（同目录，无前缀）

#### Scenario: bs4-path-unaffected

- **WHEN** `extract_infobox()` 使用 BS4 模式（explore 路径）
- **THEN** 行为 SHALL 与变更前完全一致（BS4 路径不使用 `source_dir`）
