# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-cli-entry`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: exclude-category-cli-parameter

Pipeline CLI 的 `_add_pipeline_args()` SHALL 支持 `--exclude-category` 参数，类型为 `action="append"`（repeatable），默认值为 `None`。

该参数允许用户在命令行指定需要从 Phase 0 排除的分类名称。每次指定追加一个分类名，可重复多次。

#### Scenario: single-exclude-category

- **WHEN** 执行 `pipeline <url> --strategy <path> --output <dir> --exclude-category "Music"`
- **THEN** `args.exclude_category` SHALL 为 `["Music"]`

#### Scenario: multiple-exclude-category

- **WHEN** 执行 `pipeline <url> --strategy <path> --output <dir> --exclude-category "Music" --exclude-category "Modding" --exclude-category "Version History"`
- **THEN** `args.exclude_category` SHALL 为 `["Music", "Modding", "Version History"]`

#### Scenario: no-exclude-category-specified

- **WHEN** 执行 `pipeline <url> --strategy <path> --output <dir>`（无 `--exclude-category`）
- **THEN** `args.exclude_category` SHALL 为 `None`
- **AND** Phase 0 SHALL 仅使用策略文件中的 `exclude_categories`（如存在）

### Requirement: exclude-category-merge-logic

`orchestrate.py` 的 `run_pipeline()` SHALL 在 Phase 0 执行前合并策略文件的 `api.homepage.exclude_categories` 和 CLI 的 `--exclude-category`：

- 合并 SHALL 取并集（`set(strategy_excludes) | set(cli_excludes)`），自动去重
- 合并后的列表 SHALL 传递给 Phase 0 的 `run_phase_0()`
- 日志 SHALL 以 info 级别输出排除分类的来源统计

#### Scenario: merge-strategy-and-cli-takes-union

- **WHEN** 策略 `exclude_categories` 为 `["Music", "Modding"]`
- **AND** CLI 传入 `--exclude-category "Version History" --exclude-category "Music"`
- **THEN** 传递给 Phase 0 的排除列表 SHALL 为 `["Music", "Modding", "Version History"]`（顺序不保证）

#### Scenario: merge-only-strategy

- **WHEN** 策略 `exclude_categories` 为 `["Music", "Modding"]` 且 CLI 未传 `--exclude-category`
- **THEN** 传递给 Phase 0 的排除列表 SHALL 为 `["Music", "Modding"]`

#### Scenario: merge-only-cli

- **WHEN** 策略未定义 `exclude_categories` 且 CLI 传入 `--exclude-category "Music"`
- **THEN** 传递给 Phase 0 的排除列表 SHALL 为 `["Music"]`

#### Scenario: merge-log-output

- **WHEN** 合并完成
- **THEN** 日志 SHALL 输出 `"Excluded categories: <list> (source: strategy=<n>, cli=<m>)"`（info 级别）
- **AND** 若合并后列表为空，日志 SHALL 输出 `"No categories excluded"`（debug 级别）
