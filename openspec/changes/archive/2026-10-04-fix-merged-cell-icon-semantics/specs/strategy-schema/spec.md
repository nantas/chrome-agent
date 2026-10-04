# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-schema`
- 来源: proposal.md；用户要求按已讨论的显式名称映射方案创建 change。
- 变更类型: modified（新增既有能力的配置 requirement）

## 规范真源声明

本文件是本次配置行为真源，design/tasks/verification 必须引用本文件。

## ADDED Requirements

### Requirement: merged-cell-icon-label-map
策略 SHALL 支持可选 `extraction.table_options.merged_cell_icon_labels`，类型为非空字符串键值的映射。键为源 img alt（只 trim 首尾空白）的精确值，值为纯文本语义名称；配置键值 SHALL 不含首尾空白或换行，禁止空名称，拒绝非映射/非字符串值，错误 SHALL 标明字段路径并显式失败，不降级通用转换。缺省或空映射 SHALL 使用共享内核默认名称解析。该字段 SHALL 只影响合并格延续槽位，frontmatter 为真源，所有共享转换路径 SHALL 接收相同配置。既有 table_options 字段 SHALL 保持兼容，未知键 SHALL 继续被拒绝。

#### Scenario: exact-mapping
- **WHEN** 配置 `Dd2 token vulnerable.png: Vulnerable` 和 `Dd2 token daze.png: Daze`
- **THEN** 仅精确命中的 alt 使用对应名称，大小写变化或相似文件名不命中。

#### Scenario: invalid-map
- **WHEN** 映射为列表、含空键值、非字符串、首尾空白或换行
- **THEN** 策略校验返回具体字段错误，不进入转换或静默忽略。

#### Scenario: absent-map-and-shared-paths
- **WHEN** 字段缺省或为空，或同一有效映射经 explore/pipeline/crawl 进入共享内核
- **THEN** 缺省行为有效，等价 HTML/config/context 的 core 输出一致。
