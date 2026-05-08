# Specification Delta

## Capability 对齐（已确认）

- Capability: `incremental-reprocess`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: reprocess-specified-pages
系统 SHALL 提供函数 `reprocess_pages(page_titles, api_base_url, domain, output_dir, manifest_path)` 支持对指定页面列表重新执行内容获取与转换，跳过 Phase A discovery。

#### Scenario: reprocess-failed-pages
- **WHEN** 调用 `reprocess_pages` 传入失败页面标题列表和已有 manifest 路径
- **THEN** 系统 SHALL 从 manifest 加载页面元数据，对每个指定页面执行 Phase B（fetch + convert），将结果写入 `output_dir` 对应目录，返回成功/失败统计

#### Scenario: reprocess-without-manifest
- **WHEN** 调用 `reprocess_pages` 且 `manifest_path=None`
- **THEN** 系统 SHALL 对每个页面标题使用 `title_to_filepath` 计算目标路径，执行获取与转换

### Requirement: reprocess-preserves-successful
系统 SHALL 在增量补救时跳过不在指定列表中的页面，不覆盖已有成功文件。

#### Scenario: skip-unlisted-pages
- **WHEN** 增量补救指定了 7 个页面
- **THEN** 系统 SHALL 只重新处理这 7 个页面，其他已有 .md 文件保持不变

### Requirement: cli-reprocess-subcommand
系统 SHALL 在 CLI 入口中提供 `reprocess` 子命令。

#### Scenario: cli-reprocess-pages
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract reprocess <url> --pages "A,B,C" --manifest <path> --output <dir>`
- **THEN** 系统 SHALL 对指定页面执行增量补救，输出统计信息，退出码 0 表示全部成功，1 表示部分失败
