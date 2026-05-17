# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-contract`
- 来源: `changes/explore-strategy-pipeline-bridge/`
- 变更类型: new
- 用户确认摘要: explore-strategy-pipeline-bridge 实现中新增，覆盖 MediaWiki action=parse API 引擎的输入/输出/错误三维契约

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — strategy path and target URL

The mediawiki-api engine SHALL accept a strategy file path (to read `api.base_url`) and a target URL (to extract page title) as input parameters.

#### Scenario: Required parameter — strategy path (extraArgs[0])

- **WHEN** `runMediawikiApiFetch(repoRoot, targetUrl, outputPath, extraArgs)` is invoked
- **THEN** `extraArgs[0]` SHALL be a filesystem path to a strategy.md file with valid YAML frontmatter
- **AND** the strategy SHALL have `api.base_url` defined

#### Scenario: Required parameter — targetUrl

- **WHEN** `runMediawikiApiFetch` is invoked
- **THEN** `targetUrl` SHALL be a fully-formed HTTP/HTTPS URL
- **AND** the URL SHALL contain a `/wiki/` path segment from which the page title is extracted

#### Scenario: Page title extraction

- **WHEN** the target URL is `https://example.com/wiki/The_Sad_Onion`
- **THEN** the extracted page title SHALL be `"The Sad Onion"`
- **AND** underscores in the URL path SHALL be decoded to spaces

### Requirement: Output contract — HTML file

The mediawiki-api engine SHALL output a single HTML file containing the parsed page content.

#### Scenario: Successful fetch

- **WHEN** the MediaWiki `action=parse` API returns a valid response
- **THEN** a file SHALL be written to `outputPath` containing the HTML from `data.parse.text["*"]`
- **AND** the function SHALL return `{ ok: true, stdout, command, page_title }`

### Requirement: Error contract

The mediawiki-api engine SHALL handle the following error cases and return a structured error response.

#### Scenario: Missing strategy path

- **WHEN** `extraArgs[0]` is absent or undefined
- **THEN** the function SHALL return `{ ok: false, summary, stderr: "Missing strategy path." }`

#### Scenario: Missing api.base_url

- **WHEN** the strategy frontmatter has no `api.base_url`
- **THEN** the function SHALL return `{ ok: false, summary, stderr: "Missing api.base_url in strategy." }`

#### Scenario: API request failure

- **WHEN** the `curl` request fails (non-zero exit code)
- **THEN** the function SHALL return `{ ok: false, summary, stderr }`

#### Scenario: Invalid API response

- **WHEN** the API response is not valid JSON
- **THEN** the function SHALL return `{ ok: false, summary }`

#### Scenario: API error response

- **WHEN** the API response contains `data.error`
- **THEN** the function SHALL return `{ ok: false, summary }` with the error info

### Requirement: URL construction — api.base_url handling

The engine SHALL handle `api.base_url` values both with and without `/api.php` suffix.

#### Scenario: base_url ends with /api.php

- **WHEN** `api.base_url` ends with `/api.php` (e.g., `https://bindingofisaacrebirth.wiki.gg/api.php`)
- **THEN** the constructed API URL SHALL use it directly: `{base_url}?action=parse&page=...`
- **AND** no additional `/api.php` SHALL be appended

#### Scenario: base_url without /api.php suffix

- **WHEN** `api.base_url` does not end with `/api.php`
- **THEN** the engine SHALL append `/api.php`: `{base_url}/api.php?action=parse&page=...`
