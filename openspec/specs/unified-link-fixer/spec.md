# Specification Delta

## Capability 对齐（已确认）

- Capability: `unified-link-fixer`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: fix-links-in-directory
系统 SHALL 提供函数 `fix_links_in_dir(output_dir, domain, manifest_pages)` 扫描指定目录下所有 .md 文件，统一修复链接格式。

#### Scenario: convert-wiki-path-links
- **WHEN** .md 文件中存在 `/wiki/Title` 或 `https://domain/wiki/Title` 格式的链接
- **THEN** 系统 SHALL 根据 manifest_pages 查找目标文件，将其转换为相对 .md 路径；找不到匹配时保留原始 URL

#### Scenario: preserve-fragment-anchors
- **WHEN** 链接包含 fragment（如 `/wiki/Title#Section`）
- **THEN** 系统 SHALL 剥离 fragment 用于查找目标页面，转换后将 fragment 附加到 .md 路径末尾（如 `../Dir/Title.md#Section`）

#### Scenario: strip-query-params
- **WHEN** 链接包含 query 参数（如 `/wiki/Title?action=edit`）
- **THEN** 系统 SHALL 在查找目标页面时剥离 query 参数

#### Scenario: fix-double-md-suffix
- **WHEN** 链接以 `.md.md` 结尾
- **THEN** 系统 SHALL 去除双重后缀，保留单个 `.md`

#### Scenario: fix-unresolved-relative-links
- **WHEN** .md 文件中存在 `Title.md` 格式的相对链接且对应文件不存在
- **THEN** 系统 SHALL 尝试在 manifest 中查找匹配页面并修正路径；无法解析时保留原样

### Requirement: cli-fix-links-subcommand
系统 SHALL 在 CLI 入口中提供 `fix-links` 子命令。

#### Scenario: cli-fix-links
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract fix-links <dir> --domain <d> --manifest <path>`
- **THEN** 系统 SHALL 扫描并修复目录内所有链接，输出修复统计（修复数/跳过数/失败数），退出码 0
