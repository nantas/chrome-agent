# Specification Delta

## Capability 对齐（已确认）

- Capability: `extract-kernel`
- 来源: `proposal.md` / 用户确认 4-capability 划分（本会话交互确认）。
- 变更类型: modified
- 用户确认摘要: 按清单生成 4 个 spec delta（extract-kernel / pipeline-convert-phase / pipeline / strategy）。

## 规范真源声明

本文件是该 capability 在本次 change 中的行为规范真源；design/tasks/verification 必须引用本文件，页面回写不得替代 spec delta。

## ADDED Requirements

### Requirement: infobox-table-cell-escaping
`extract_infobox` 构建结构化 `## Infobox` Markdown 表格时，label 与 value 单元格 SHALL 对裸换行执行 `\n → <br>` 替换、对裸竖线执行 `| → \|` 转义，保证每个数据行是单行 Markdown 表格行。该行为 SHALL 在 `_extract_bs4`（字符串输入）与 `_extract_selectolax`（Node 输入）两条渲染路径上一致。

#### Scenario: multi-line-value-single-row
- **WHEN** infobox 的某个 value 含多段文本（如多段 passive ability，含换行）
- **THEN** 输出的表格行 SHALL 是单行，段间以 `<br>` 连接，不产生断行

#### Scenario: both-render-paths-escape
- **WHEN** 同一含换行与竖线的 infobox 分别以 HTML 字符串与 selectolax Node 输入提取
- **THEN** 两条路径的输出 SHALL 均无裸换行/裸竖线残留在表格单元格内

#### Scenario: regression-guard
- **WHEN** 任一渲染路径移除该转义
- **THEN** `tests/test_convert_equivalence.py` 中的对应断言 SHALL 失败
