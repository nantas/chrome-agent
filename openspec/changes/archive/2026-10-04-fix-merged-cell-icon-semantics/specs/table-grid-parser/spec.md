# Specification Delta

## Capability 对齐（已确认）

- Capability: `table-grid-parser`
- 来源: proposal.md；用户要求按已讨论方案创建后续 change。
- 变更类型: modified
- 前置 requirement: fix-wiki-table-sample-integrity 的 merged-cell-asset-retention；归档时先同步此前置，再应用本 MODIFIED block。

## 规范真源声明

本文件是本次表格行为规范真源；design/tasks/verification 必须引用本文件，页面摘要不得替代它。

## MODIFIED Requirements

### Requirement: merged-cell-asset-retention
共享 HTML 转换内核 SHALL 在合并单元格原始槽位保留允许输出的图片，在 colspan/rowspan 的所有延续槽位保留文本上下文并将图标替换为可读文本，不得复制图片资产或直接删除图标语义。每个源图片出现次数 SHALL 保持一次（不对不同源节点的同 URL 图片作全局去重）。被既有过滤规则排除的图片 SHALL NOT 被名称替换复活。

名称 SHALL 按“策略精确 alt 映射 → 可靠 alt → 可靠 title → 固定占位 `（未命名图标）`”解析；属性匹配前只 trim 首尾空白，映射区分大小写、不做模糊匹配。可靠名称 SHALL 非空，且不是 URL、图片文件名或通用占位名 image/icon；文件名包括 png/jpg/jpeg/gif/svg/webp/avif/ico 扩展名，不区分大小写。系统 SHALL NOT 从路径猜测名称。替代名称 SHALL 作为文本节点渲染，保留图标原有链接目的、相邻文字和顺序，并安全转义 Markdown 特殊字符；同一链接已有相同可见名称，或同一单元格内紧邻的可见标签与可靠名称完全相同时 SHALL 不重复添加该名称。邻接匹配 SHALL 不跨其他文字、图片、换行或块边界；不同链接目的 SHALL 保持独立。系统 SHALL 保留原标签文字、格式和链接目的，不对独立源图片或文字全局去重。

#### Scenario: crypt-keeper-colspan
- **WHEN** 跨两列的效果格包含 `or` 分隔的 Blind、Weak、Vulnerable、Daze 图标
- **THEN** 原格图片保留，第二格具有对应文字名称及原有百分比/顺序，不再产生删除图标导致的 `or or`。

#### Scenario: mixed-span-and-repeated-source-assets
- **WHEN** 图片格同时具有 colspan 和 rowspan，另一个源格也使用相同图片 URL
- **THEN** 每个源图片各输出一次，所有延续槽位含名称，行列占位与邻接数据不变。

#### Scenario: explicit-name-or-unknown
- **WHEN** alt 为 `Dd2 token vulnerable.png` 且存在精确映射
- **THEN** 延续格使用映射值 Vulnerable；未命中且 title 不可靠时使用 `（未命名图标）`，不输出猜测的状态名。

#### Scenario: linked-icon-and-existing-label
- **WHEN** 图标被链接包裹，链接已有同名文本，或名称含管道/方括号
- **THEN** 链接目的与原文字保留，同名不重复，表格行列及 Markdown 链接语法不被破坏。

#### Scenario: ordinary-and-filtered-content
- **WHEN** 表格没有合并格，合并格仅有文字，或图片被过滤
- **THEN** 普通格与纯文本展开保持原行为，过滤图片不产生新标签。

#### Scenario: adjacent-exact-label
- **WHEN** 图标和同名标签位于相邻 inline 节点（可以跨透明包装或空白），标签是纯文字或同目的链接
- **THEN** 延续格只保留一次名称，原文字格式及链接目的不丢失；不同目的链接、其他内容间隔和不同名称不合并。
