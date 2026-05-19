# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-cli-entry`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: main-runnable-as-script
`__main__.py` SHALL 在被 `python3 scripts/mediawiki-api-extract` 直接运行时正确设置 `sys.path`，使包内相对导入正常工作。

#### Scenario: run-as-directory-script
- **WHEN** 执行 `python3 scripts/mediawiki-api-extract <url> --strategy <path> --output <dir>`
- **THEN** 系统 SHALL 正确初始化包路径，以退出码 0 完成管线运行

#### Scenario: run-as-module
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract <url> --strategy <path> --output <dir>`
- **THEN** 系统 SHALL 以退出码 0 完成管线运行（行为与原有方式一致）

### Requirement: cli-subcommand-routing
CLI 入口 SHALL 支持子命令路由：`pipeline`（默认）、`fetch`、`reprocess`、`fix-links`、`reconvert`。

#### Scenario: default-pipeline-subcommand
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract <url> --strategy <path> --output <dir>`（无显式子命令）
- **THEN** 系统 SHALL 执行全量管线（与当前行为一致）

#### Scenario: fetch-subcommand
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract fetch <url> --domain <d> --mode html --output <file>`
- **THEN** 系统 SHALL 路由到 `standalone-extraction` 的单页面获取逻辑

#### Scenario: reprocess-subcommand
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract reprocess <url> --pages "A,B" --manifest <path> --output <dir>`
- **THEN** 系统 SHALL 路由到 `incremental-reprocess` 的增量补救逻辑

#### Scenario: fix-links-subcommand
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract fix-links <dir> --domain <d> --manifest <path>`
- **THEN** 系统 SHALL 路由到 `unified-link-fixer` 的链接修复逻辑

### Requirement: chrome-agent-cli-fix
`chrome-agent-cli.mjs` SHALL 使用 `-m scripts.mediawiki_api_extract` 模式调用管线，而非将目录路径作为脚本参数。

#### Scenario: cli-mjs-api-route
- **WHEN** `chrome-agent-cli.mjs` 检测到 `api.platform=mediawiki`
- **THEN** 它 SHALL 执行 `spawnSync("python3", ["-m", "scripts.mediawiki_api_extract", url, "--strategy", path, "--output", dir, ...])`

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

## Requirements from change: split-fetch-convert-phases

### ADDED

#### Requirement: re-fetch-cli-flag
The system SHALL 支持 `--re-fetch` CLI flag。

当与 `--phase fetch` 或 `--phase all` 一起使用时，SHALL 忽略已有缓存，强制重新获取所有页面并覆盖缓存文件。

##### Scenario: re-fetch-flag
- **WHEN** 执行 `--phase fetch --re-fetch`
- **THEN** SHALL 不检查缓存存在性
- **AND** SHALL 对所有页面重新发起 API 请求
- **AND** SHALL 覆盖已有缓存文件

#### Requirement: cache-root-resolution
The system SHALL 在 pipeline 入口处解析缓存根目录。

解析逻辑：
1. 读取 strategy 文件
2. 提取 `api.platform`（若存在）或使用 `"scrapling"` 作为 platform
3. 提取 `domain` 字段
4. 构造 `.cache/<platform>/<domain>/` 路径
5. 自动创建目录（如不存在）

##### Scenario: cache-root-resolution-mediawiki
- **WHEN** strategy 的 `api.platform` 为 `"mediawiki"` 且 `domain` 为 `"bindingofisaacrebirth.wiki.gg"`
- **THEN** `cache_root` SHALL 解析为 `<repo_root>/.cache/mediawiki/bindingofisaacrebirth.wiki.gg/`

### MODIFIED

#### Requirement: phase-choices
`--phase` CLI 参数的 choices SHALL 更新为：

```python
choices=["all", "discover", "fetch", "convert", "assemble"]
```

移除的值：`"extract"`、`"A"`、`"B"`、`"C"`、`"homepage"`。

##### Scenario: valid-phase-choices
- **WHEN** 用户传入 `--phase fetch`
- **THEN** argparse SHALL 接受该值

##### Scenario: invalid-phase-choice
- **WHEN** 用户传入 `--phase extract`
- **THEN** argparse SHALL 拒绝，输出 `"invalid choice: 'extract' (choose from 'all', 'discover', 'fetch', 'convert', 'assemble')"`

#### Requirement: phase-forwarding-from-cli
`chrome-agent-cli.mjs` 中的 `runCrawl()` SHALL 将 `--phase` 参数传递到 Python pipeline。

当 MediaWiki API 路径被触发时，JS CLI SHALL 在 `apiArgs` 中添加 `"--phase"` + 用户指定的值。

##### Scenario: phase-forwarding
- **WHEN** JS CLI 执行 `runCrawl()` 且用户指定 `--phase fetch`
- **AND** strategy 的 `api.platform` 为 `"mediawiki"`
- **THEN** `apiArgs` SHALL 包含 `["--phase", "fetch"]`

#### Requirement: gitignore-update
`.gitignore` SHALL 排除 `.cache/` 目录，使其不进入版本管理。

##### Scenario: cache-gitignored
- **WHEN** `.cache/` 目录存在
- **THEN** `git status` SHALL NOT 显示 `.cache/` 下任何文件
