# Specification Delta

## Capability 对齐（已确认）

- Capability: `page-assignment`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: excluded-categories-not-in-input

`assign_pages()` SHALL 不接收已被排除的分类的页面数据。排除在 Phase 0 的 `run_phase_0()` 中完成（源头过滤），`assign_pages()` 无需内部感知排除逻辑。

#### Scenario: assigner-receives-filtered-input

- **WHEN** Phase 0 排除了 Music、Modding、Version History 三个分类
- **THEN** `assign_pages()` 接收的 `categories` 参数 SHALL 不包含这三个分类
- **AND** `assign_pages()` 接收的 `pages` 参数 SHALL 不包含任何 `source_categories` 仅为已排除分类的页面
- **AND** 分配逻辑 SHALL 无需任何代码变更即可正确处理

#### Scenario: page-in-multiple-categories-one-excluded

- **WHEN** 页面 "Sacrificial Altar" 同时属于 Items（未排除）和 Music（已排除）两个分类
- **AND** Music 被排除
- **THEN** 该页面的 `source_categories` SHALL 仅包含 `["Items"]`
- **AND** 页面 SHALL 被分配至 Items 目录（通过 MW category 匹配或 category_page_member 分配）

## MODIFIED Requirements

*(无已有 requirement 被修改。page-assignment 的分配逻辑、优先级链、batch lookup 均保持不变。排除在源头完成，assigner 透明消费已过滤的输入。)*
