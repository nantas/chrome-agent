# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-cli-entry`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: handoff P-1 修复——CLI crawl 命令添加 `--output` 参数

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: crawl-output-directory
The `chrome-agent crawl` command SHALL accept an optional `--output <dir>` argument. When specified, the crawl output SHALL be written to the specified directory instead of the auto-generated `outputs/<timestamp>-crawl-<slug>/` path.

#### Scenario: custom-output-directory
- **WHEN** user runs `chrome-agent crawl <url> --output /path/to/dir`
- **THEN** all crawl artifacts (manifest, extracted pages, reports) SHALL be written to `/path/to/dir`
- **AND** `buildRunPaths` auto-generation SHALL be bypassed for `runDir`

#### Scenario: no-output-flag-default-behavior
- **WHEN** user runs `chrome-agent crawl <url>` without `--output`
- **THEN** output SHALL be written to `outputs/<timestamp>-crawl-<slug>/` as before (no behavior change)

#### Scenario: output-path-for-mediawiki-api-pipeline
- **WHEN** `--output <dir>` is specified AND the strategy routes to MediaWiki API pipeline
- **THEN** the CLI SHALL pass `--output <dir>` to the internal Python pipeline
- **AND** the Python pipeline SHALL use `<dir>` as its output root

### Requirement: output-flag-parsing
The `parseArgs()` function SHALL parse `--output <dir>` and `--output=<dir>` as a string argument, stored as `parsed.outputDir`.

#### Scenario: output-flag-separated
- **WHEN** CLI args contain `--output /some/path`
- **THEN** `parsed.outputDir` SHALL be `"/some/path"`

#### Scenario: output-flag-equals
- **WHEN** CLI args contain `--output=/some/path`
- **THEN** `parsed.outputDir` SHALL be `"/some/path"`

#### Scenario: output-flag-absent
- **WHEN** CLI args do not contain `--output`
- **THEN** `parsed.outputDir` SHALL be `null`

## ADDED Requirements

_None_

## REMOVED Requirements

_None_

## RENAMED Requirements

_None_
