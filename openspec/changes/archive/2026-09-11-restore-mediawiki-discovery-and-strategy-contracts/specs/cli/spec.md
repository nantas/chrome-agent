# Specification Delta

## Capability 对齐（已确认）

- Capability: `cli`
- 来源: `proposal.md` / 用户已授权两组修复目标
- 变更类型: `modified`
- 用户确认摘要: 规划两组修复，ns0 空目录按建议归 Misc，不处理历史产物。

## 规范真源声明

- 本文件为本 capability 在本 change 的行为规范真源；design/tasks/verification 必须引用本文件。
- 项目页面回写不得替代本文件。

## 归档目标

MODIFIED `Phase-based execution` maps exactly to `openspec/specs/cli/cli-workflows.md`. ADDED requirements SHALL be appended to that same file; do not create a second canonical cli/spec.md. Existing internal failure envelope/handoff requirements in `openspec/specs/governance/handoff.md` remain applicable.

## MODIFIED Requirements

### Requirement: Phase-based execution

Public crawl SHALL route MediaWiki `--discovery-only` and the compatibility alias `--phase discover` to explore page enumeration. For MediaWiki, `fetch`, `convert`, `assemble`, and extraction `all` SHALL consume an accepted manifest via pipeline; `convert` remains cache-only conversion followed by the existing assembly behavior. Without a manifest, a crawl requesting all SHALL perform discovery and stop at confirmation, unless `--yes` explicitly authorizes continuing a complete successful discovered scope. Scrapling's supported fetch/convert/assemble behavior SHALL remain unchanged. Incompatible options SHALL be rejected rather than silently prioritized.

#### Scenario: discovery-only-stops
- **WHEN** public MediaWiki crawl uses discovery-only, including with --yes
- **THEN** it SHALL return manifest/summary without正文 extraction, conversion or assembly and SHALL NOT spawn pipeline --phase discover.

#### Scenario: discovery-phase-alias
- **WHEN** public MediaWiki crawl uses --phase discover
- **THEN** it SHALL behave as discovery-only through explore rather than sending discover to pipeline.

#### Scenario: full-crawl-confirmation
- **WHEN** a manifest-free crawl completes discovery without --yes
- **THEN** it SHALL return confirmation-required discovery artifacts and SHALL NOT extract until the caller confirms and resumes with --from-manifest.

#### Scenario: conflicting-modes
- **WHEN** discovery-only is combined with --from-manifest or an extraction phase
- **THEN** the command SHALL return structured invalid arguments before performing work.

## ADDED Requirements

### Requirement: manifest-input-compatibility

The public CLI and pipeline SHALL validate manifest shape and identity before API probing. New schema version 2 manifests SHALL validate required fields/domain/fingerprint and list eligibility. An absent schema_version SHALL select the legacy adapter; any declared version other than 2 SHALL be rejected as unsupported, not guessed as legacy. Legacy manifests without a version MAY be adapted in memory only when each row already has valid title/ns/target paths and list identity is unambiguous: exact configured title plus matching configured directory permits deriving is_list_page=true; a row not matching any list title permits false. Ambiguous aliases, conflicting directories, missing required row fields or mismatched target domain SHALL return a structured manifest-contract error with field paths and remediation. Detached legacy list content SHALL be ignored with an explicit absent-page reason, never adding pages. Existing target paths, including empty root directories, SHALL be preserved for legacy input; this change SHALL NOT migrate historical files or rewrite source manifests.

#### Scenario: unambiguous-legacy-input
- **WHEN** a versionless manifest has valid paths and exact unambiguous list-page matches
- **THEN** the command SHALL derive only missing eligibility metadata in memory, report legacy adaptation, and preserve source bytes, page membership and target paths.

#### Scenario: ambiguous-legacy-list
- **WHEN** a legacy list identity requires guessing an alias or conflicts with its directory
- **THEN** the command SHALL fail with field-specific diagnostics without fetching, rediscovering, or modifying the input.

#### Scenario: detached-legacy-content
- **WHEN** legacy list_page_content contains a title absent from pages
- **THEN** the command SHALL report that content as skipped and SHALL NOT expand confirmed scope.

#### Scenario: incompatible-v2-input
- **WHEN** required version 2 fields are missing or domain/fingerprint conflicts with the active strategy
- **THEN** validation SHALL reject the input with a manifest-contract diagnostic before probing.

### Requirement: mediawiki-error-and-fallback-semantics

MediaWiki subprocess results SHALL distinguish success, partial success, explicit contract/config/internal failures, external network failures, and spawn/timeout/signal failures. A null process status SHALL never be mapped to partial success. Contract/configuration/invalid-arguments/internal failures SHALL stop via the existing internalFailure/handoff envelope. Any allowed external fallback SHALL preserve discovery-only or accepted-manifest page/path semantics; if the target backend cannot do so the CLI SHALL return failure without fallback. Result metadata SHALL preserve upstream backend, exit code or null, process error/signal, stderr summary, requested mode and fallback decision/reason, including when fallback succeeds.

#### Scenario: invalid-arguments-do-not-fallback
- **WHEN** pipeline exits 20 or rejects strategy/manifest configuration
- **THEN** public crawl SHALL fail with original diagnostics and internal handoff without invoking Scrapling.

#### Scenario: failed-spawn-is-not-partial
- **WHEN** spawn returns status null, an error, a timeout or a signal
- **THEN** public crawl SHALL report the actual failure and SHALL NOT return partial_success merely from null coalescing.

#### Scenario: unsupported-fallback-contract
- **WHEN** an external API failure occurs during discovery-only or API manifest extraction and the proposed fallback cannot preserve the requested contract
- **THEN** the command SHALL stop with original upstream evidence and a fallback-not-compatible reason; it SHALL NOT crawl the homepage or reinterpret pages as visited URLs.

#### Scenario: compatible-fallback-retains-upstream
- **WHEN** a supported fallback is deliberately selected for an external failure
- **THEN** its final result SHALL include original failure context and preserve the approved page scope and output paths.
