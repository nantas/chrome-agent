# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-cli-entry`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: explore 阶段确认 —— `--phase` 新增 `discover` 值；discovery 完成后生成 `discovery_summary.json`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- 本次 change 的完整 spec 真源为：`openspec/specs/pipeline-cli-entry/spec.md`（已冻结版本） + 本文件 delta
- design / tasks / verification 必须同时引用两者，不一致时以本文件为准
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: phase-discover-value

The `--phase` argument SHALL support a `discover` value that runs only the discovery phase and stops, producing `page_manifest.json` and `discovery_summary.json` without proceeding to extraction or assembly.

#### Scenario: phase-discover-homepage

- **WHEN** `pipeline <url> --strategy <path> --output <dir> --discovery homepage --phase discover` is executed
- **THEN** the pipeline SHALL run homepage discovery (Phase 0) only
- **AND** the pipeline SHALL write `page_manifest.json` to the output directory
- **AND** the pipeline SHALL write `discovery_summary.json` to the output directory
- **AND** the pipeline SHALL exit with code 0 without running extraction or assembly

#### Scenario: phase-discover-allpages

- **WHEN** `pipeline <url> --strategy <path> --output <dir> --discovery allpages --phase discover` is executed
- **THEN** the pipeline SHALL run allpages discovery (Phase A) only
- **AND** the pipeline SHALL write `page_manifest.json` and `discovery_summary.json`
- **AND** the pipeline SHALL exit without extraction or assembly

#### Scenario: phase-discover-auto

- **WHEN** `pipeline <url> --strategy <path> --output <dir> --discovery auto --phase discover` is executed
- **AND** the strategy has `api.homepage` defined
- **THEN** the pipeline SHALL run homepage discovery
- **AND** the pipeline SHALL resolve discovery strategy according to the existing auto-detection logic

#### Scenario: phase-discover-respects-exclusions

- **WHEN** `--phase discover` is combined with `--exclude-category`
- **THEN** the exclusions SHALL be applied during discovery
- **AND** excluded categories SHALL appear in `discovery_summary.excluded` with their page counts
- **AND** excluded pages SHALL NOT appear in `page_manifest.json`

### Requirement: discovery-summary-generation

The `orchestrate.py` `run_pipeline()` function SHALL, after discovery completes (regardless of `--phase discover` or `--phase all` or `--phase extract`), generate `discovery_summary.json` in the output directory.

The summary SHALL conform to the `discovery-summary-schema` spec.

#### Scenario: summary-generated-after-discovery

- **WHEN** discovery completes in any phase configuration
- **THEN** the pipeline SHALL call `build_discovery_summary(manifest, strategy)` 
- **AND** the pipeline SHALL write the result to `<output>/discovery_summary.json`
- **AND** the summary SHALL include `manifest_path` pointing to the absolute path of `page_manifest.json`

#### Scenario: summary-fields-from-manifest

- **WHEN** `build_discovery_summary()` is called with a manifest from homepage discovery
- **THEN** `discovery_method` SHALL be `"homepage"`
- **AND** `categories` SHALL be derived from the strategy's `api.homepage.categories` crossed with manifest page counts
- **AND** `sample_pages` SHALL be the first 3-5 page titles per directory from the manifest
- **AND** `excluded` SHALL list categories excluded via `_resolve_exclude_categories()`
- **AND** `unclassified` SHALL count pages assigned to `"misc"` directory

#### Scenario: summary-for-allpages-discovery

- **WHEN** `build_discovery_summary()` is called with a manifest from allpages discovery
- **THEN** `discovery_method` SHALL be `"allpages"`
- **AND** `categories` SHALL be derived from manifest `target_directory` groupings
- **AND** `sample_pages` SHALL be the first 3-5 page titles per directory

#### Scenario: summary-estimated-time

- **WHEN** `build_discovery_summary()` calculates `estimated_time_minutes`
- **THEN** the estimate SHALL consider the strategy's rate limit configuration
- **AND** the estimate SHALL be `ceil(total_pages * avg_seconds_per_page / 60)`
- **AND** `avg_seconds_per_page` SHALL be derived from `rate_limit_config.batch_delay_ms` and `rate_limit_config.concurrency`
- **AND** the estimate SHALL be at minimum 1 minute for any non-empty manifest

#### Scenario: summary-error-handling

- **WHEN** discovery produces a manifest with `failure_rate > 0`
- **THEN** `discovery_summary.failure_rate` SHALL reflect the actual failure rate
- **AND** `discovery_summary.warnings` SHALL include a summary of failures
- **AND** `discovery_summary.total_pages` SHALL include only successfully discovered pages

### Requirement: phase-discover-with-resume

When `--phase discover` is used with resume enabled, the pipeline SHALL initialize the resume state but not perform extraction.

#### Scenario: discover-initializes-state

- **WHEN** `--phase discover` is used with resume enabled (default)
- **THEN** the pipeline SHALL initialize the pipeline state file with `phase: "discover_done"`
- **AND** the state file SHALL record `total_pages` from the manifest
- **AND** subsequent `--phase extract` SHALL be able to resume from this state

## MODIFIED Requirements

### Requirement: chrome-agent-cli-fix

`chrome-agent-cli.mjs` SHALL 使用 `-m scripts.mediawiki_api_extract` 模式调用管线，而非将目录路径作为脚本参数。

`chrome-agent-cli.mjs` SHALL pass `--phase discover` when `--discovery-only` is set, and `--phase extract` (or `--phase all`) when `--from-manifest` is set.

#### Scenario: cli-mjs-api-route

- **WHEN** `chrome-agent-cli.mjs` 检测到 `api.platform=mediawiki`
- **THEN** 它 SHALL 执行 `spawnSync("python3", ["-m", "scripts.mediawiki_api_extract", url, "--strategy", path, "--output", dir, ...])`

#### Scenario: cli-mjs-discovery-only-route

- **WHEN** `chrome-agent-cli.mjs` 检测到 `--discovery-only` 且 `api.platform=mediawiki`
- **THEN** 它 SHALL 传递 `--phase discover` 到 Python 管线
- **AND** 它 SHALL NOT 传递 `--phase all`、`--phase extract` 或 `--phase assemble`

#### Scenario: cli-mjs-from-manifest-route

- **WHEN** `chrome-agent-cli.mjs` 检测到 `--from-manifest` 且 `api.platform=mediawiki`
- **THEN** 它 SHALL 传递 `--phase all` 到 Python 管线（或 `--phase extract` 如果仅需 extraction）
- **AND** 它 SHALL NOT 传递 `--phase discover`
- **AND** 管线 SHALL 从已有 manifest 加载页面列表
