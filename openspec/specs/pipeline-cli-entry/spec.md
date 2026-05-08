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
