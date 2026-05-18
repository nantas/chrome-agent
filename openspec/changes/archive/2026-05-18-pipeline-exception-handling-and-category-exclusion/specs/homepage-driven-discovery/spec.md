# Specification Delta

## Capability 对齐（已确认）

- Capability: `homepage-driven-discovery`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

*(无已有 requirement 被修改。`exclude_categories` 过滤是现有 `category-discovery-strategy-selection` 流程的前置步骤，以 ADDED 形式追加。)*

## ADDED Requirements

### Requirement: category-exclusion-filtering

The system SHALL 在 Phase 0 的 `run_phase_0()` 中，`parse_homepage()` 完成后、`_discover_category_pages()` 调用前，按 `api.homepage.exclude_categories` 列表过滤分类。

排除匹配按 `categories[].name` 字段进行名称匹配（大小写敏感）。被排除的分类不进入 `_discover_category_pages()` 的后续遍历。

`exclude_categories` 为可选字段，缺失或为空时 SHALL 不过滤任何分类（行为与当前一致）。

#### Scenario: exclude-three-categories

- **WHEN** `api.homepage.exclude_categories` 为 `["Music", "Modding", "Version History"]`
- **AND** `parse_homepage()` 返回 19 个分类（含 Music、Modding、Version History）
- **THEN** `run_phase_0()` SHALL 过滤掉这三个分类
- **AND** `_discover_category_pages()` SHALL 仅接收 16 个分类
- **AND** 日志 SHALL 输出 `"Excluded N categories: Music, Modding, Version History"`（info 级别）

#### Scenario: no-exclusion-configured

- **WHEN** `api.homepage.exclude_categories` 未定义或为空列表 `[]`
- **THEN** `run_phase_0()` SHALL 不过滤任何分类
- **AND** 行为与当前完全一致

#### Scenario: exclude-category-not-found

- **WHEN** `exclude_categories` 包含 `"NonExistent"`
- **AND** `parse_homepage()` 返回的分类中无名称匹配 `"NonExistent"` 的分类
- **THEN** `run_phase_0()` SHALL 记录 `log.info("Exclude category 'NonExistent' not found in homepage categories — ignoring")`
- **AND** SHALL 不阻断流程，继续处理未排除的分类

### Requirement: excluded-categories-absent-from-manifest

被排除的分类 SHALL 不在最终 manifest 的任何位置出现（不在 `source_categories`、不在 `assigned_category`、不在 `categories_discovered` 计数中）。

#### Scenario: manifest-excludes-filtered-categories

- **WHEN** Music 分类被排除
- **THEN** manifest 中所有 page 的 `source_categories` SHALL 不包含 `"Music"`
- **AND** manifest 中所有 page 的 `assigned_category` SHALL 不为 `"Music"`
- **AND** `manifest.categories_discovered` SHALL 不包含被排除的分类

### Requirement: exclude-categories-merge-with-cli

Phase 0 SHALL 在运行时合并策略文件的 `api.homepage.exclude_categories` 和 CLI 传入的 `--exclude-category` 参数，取并集。合并逻辑由 `orchestrate.py` 的 `run_pipeline()` 负责，Phase 0 消费合并后的最终列表。

#### Scenario: merge-strategy-and-cli-excludes

- **WHEN** 策略 `exclude_categories` 为 `["Music", "Modding"]`
- **AND** CLI 传入 `--exclude-category "Version History" --exclude-category "Music"`
- **THEN** 最终排除列表 SHALL 为 `{"Music", "Modding", "Version History"}`（并集，去重）
- **AND** 日志 SHALL 输出 `"Excluded categories: Music, Modding, Version History (source: strategy=2, cli=2)"`
