# MODIFIED Requirements

### Requirement: merged-cell-asset-retention
延续合并单元格 SHALL 保留文本标签，但不得重复原始单元格图片。

#### Scenario: merged-image
- WHEN 单个图片位于 colspan 或 rowspan 单元格
- THEN 输出图片出现一次，文本上下文继续保留。

### Requirement: table-section-and-nested-data
完整宽度、单单元格、含标题的行 SHALL 输出独立 Markdown 标题。嵌套表格 SHALL 从父格移出，在所属父表片段后输出独立表格，不丢失数值、不混入父网格。

#### Scenario: nested-skill-levels
- WHEN 技能表内含 Further levels 子表
- THEN 所有等级和对应数值均保留，子表独立且顺序稳定。

### Requirement: browser-table-structures
转换 SHALL 包含直接 thead/tbody/tfoot 行、表格 caption 的资产，以及晋升标题格内的嵌套表。多行表头 SHALL 按列保留各级标签并合并为单个合法 GFM 表头。

#### Scenario: header-and-caption-assets
- WHEN 表头图标在 thead 或 caption 中
- THEN 图片出现次数与来源一致，表头关系、正文值和 tfoot 文本完整。

### Requirement: rich-pre-and-literal-text
富文本 pre 内的图片和链接 SHALL 保留为可用 Markdown，纯文本 pre SHALL 保持代码。可见文字中的尖括号 SHALL 转义，不能被解释为 HTML。

#### Scenario: warning-versus-code
- WHEN pre 含警告图标和链接
- THEN 提示可见、图标保留、链接可点击；普通代码仍使用围栏。
