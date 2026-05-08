# Specification Delta

## Capability 对齐（已确认）

- Capability: `standalone-extraction`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: single-page-fetch-and-convert
系统 SHALL 提供独立函数 `fetch_and_convert(url, domain, output, mode, manifest_pages)` 支持对单个 URL 执行获取与转换，无需启动全量管线。

#### Scenario: fetch-html-mode
- **WHEN** 调用 `fetch_and_convert` 且 `mode="html"`
- **THEN** 系统 SHALL 使用 `ApiClient` 调用 `action=parse&prop=text` 获取 HTML，通过 `HtmlToMarkdownConverter` 转换为 Markdown，写入 `output` 指定路径，返回文件路径

#### Scenario: fetch-wikitext-mode
- **WHEN** 调用 `fetch_and_convert` 且 `mode="wikitext"`
- **THEN** 系统 SHALL 使用 `ApiClient` 调用 `action=parse&prop=wikitext` 获取 wikitext，通过 `convert_wikitext_to_markdown` 转换，写入 `output` 指定路径，返回文件路径

#### Scenario: no-manifest-pages
- **WHEN** 调用 `fetch_and_convert` 且 `manifest_pages=None`
- **THEN** 系统 SHALL 在无链接索引的情况下完成转换，内部链接保留为原始格式

### Requirement: reconvert-existing-file
系统 SHALL 提供独立函数 `reconvert_file(filepath, domain, manifest_pages)` 支持对已有 HTML/Markdown 文件重新转换。

#### Scenario: reconvert-html-file
- **WHEN** 调用 `reconvert_file` 且目标文件包含 HTML 内容
- **THEN** 系统 SHALL 使用 `HtmlToMarkdownConverter` 重新转换并覆盖原文件，返回转换后内容

#### Scenario: reconvert-with-manifest
- **WHEN** 调用 `reconvert_file` 且提供了 `manifest_pages`
- **THEN** 系统 SHALL 构建链接索引，将 wiki 内部链接转换为相对 Markdown 链接

### Requirement: cli-fetch-subcommand
系统 SHALL 在 CLI 入口中提供 `fetch` 子命令，支持命令行方式的单页面获取。

#### Scenario: cli-fetch-html
- **WHEN** 执行 `python3 -m scripts.mediawiki_api_extract fetch <url> --domain <d> --mode html --output <file>`
- **THEN** 系统 SHALL 获取页面并写入指定文件，退出码为 0

#### Scenario: cli-fetch-failure
- **WHEN** 获取失败（网络错误、API 错误等）
- **THEN** 系统 SHALL 输出错误信息到 stderr，退出码为 10
