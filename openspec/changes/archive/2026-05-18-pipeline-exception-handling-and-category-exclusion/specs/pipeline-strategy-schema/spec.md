# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-strategy-schema`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: homepage-exclude-categories-field

策略文件 `api.homepage` 配置块 SHALL 支持可选字段 `exclude_categories: list[str]`。

该字段定义在首页驱动爬取（Phase 0）中需要排除的分类名称列表。每个元素 SHALL 与 `api.homepage.categories[].name` 进行大小写敏感的精确匹配。

该字段为可选字段，缺失时 SHALL 等同于空列表（不过滤任何分类）。

#### Scenario: exclude-categories-present

- **WHEN** 策略文件包含：
  ```yaml
  api:
    homepage:
      exclude_categories:
        - "Music"
        - "Modding"
        - "Version History"
  ```
- **THEN** pipeline 启动校验 SHALL 通过（字段格式合法）
- **AND** Phase 0 SHALL 在分类发现前排除这三个分类

#### Scenario: exclude-categories-absent

- **WHEN** 策略文件不包含 `api.homepage.exclude_categories`
- **THEN** pipeline 启动校验 SHALL 通过（字段为可选）
- **AND** Phase 0 SHALL 不过滤任何分类

#### Scenario: exclude-categories-empty-list

- **WHEN** 策略文件包含 `exclude_categories: []`
- **THEN** 行为 SHALL 等同于字段缺失（不过滤任何分类）

### Requirement: exclude-categories-backward-compatible

新增 `api.homepage.exclude_categories` 字段 SHALL 不破坏任何已有策略文件的解析和运行。

已有策略文件中不存在的该字段 SHALL 不触发解析错误、不触发警告、不改变任何管线行为。

#### Scenario: existing-strategy-unchanged

- **WHEN** 已有策略文件不含 `api.homepage.exclude_categories`
- **AND** pipeline 以该策略文件运行 Phase 0 或 Phase A
- **THEN** 管线行为 SHALL 与字段添加前完全一致

### Requirement: exclude-categories-not-applicable-to-phase-a

`api.homepage.exclude_categories` 字段 SHALL 仅影响 Phase 0（homepage-driven discovery）。Phase A（allpages 全量发现）SHALL 不读取此字段。

#### Scenario: phase-a-ignores-exclude-categories

- **WHEN** 策略包含 `api.homepage.exclude_categories: ["Music"]` 且 pipeline 运行 Phase A
- **THEN** Music 分类对应的页面 SHALL 仍被 Phase A 发现并包含在 manifest 中
- **AND** 不触发任何警告或错误
