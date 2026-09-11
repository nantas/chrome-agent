# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-convert-phase`
- 来源: `proposal.md` / 用户授权“按照你建议的方案创建 change”。
- 变更类型: modified
- 用户确认摘要: 落实已讨论的抽取完整性修复范围；不自动恢复全站抓取。

## 规范真源声明

本文件是该 capability 在本 change 中的行为规范真源；design/tasks/verification SHALL 以此为依据，页面回写不得替代 spec delta。

## MODIFIED Requirements

### Requirement: skip-already-converted-pages
Resume SHALL skip a page only when its completed state, expected output file, compatible raw input, and persisted conversion fingerprint all match the current request. The fingerprint SHALL cover raw conversion payload, semantic conversion configuration, acquisition mode, target/link context and converter contract revision. Missing legacy fingerprints SHALL require reconversion; filename presence alone SHALL NOT prove freshness. Disabled resume SHALL always reconvert valid inputs.

#### Scenario: resume-skip-converted-page
- **WHEN** resume is enabled and completed state, output, admitted raw input and fingerprint all match
- **THEN** the page SHALL skip conversion and be available to assembly as a valid result.

#### Scenario: changed-input-or-contract
- **WHEN** raw payload, extraction rules, target/link context, acquisition mode or converter revision changes, or a legacy completion lacks a fingerprint
- **THEN** resume SHALL NOT skip the page despite an existing Markdown file.

#### Scenario: force-reconvert-without-resume
- **WHEN** resume is disabled
- **THEN** every page with compatible raw content SHALL be converted regardless of completed state or existing output.

## ADDED Requirements

### Requirement: conversion-cache-admission
Conversion SHALL use the shared admission rules before resume acceptance or dispatch. Incompatible/missing raw content SHALL produce a per-page error with remediation to run fetch; conversion-only execution SHALL NOT implicitly fetch or fall back to another acquisition mode. Failed pages SHALL NOT enter successful assembly or remain marked completed for the current request.

#### Scenario: offline-incompatible-cache
- **WHEN** convert-only runs with an HTML strategy and a wikitext-only hybrid cache
- **THEN** the page SHALL fail with `cache_incompatible` and expected/actual mode diagnostics, without network acquisition or old-mode conversion.

#### Scenario: stale-output-after-fetch-failure
- **WHEN** a page has an old Markdown file and replacement or forced fetch failed, even when its old cache was compatible
- **THEN** resume and assembly SHALL NOT treat that old file as a successful page of the current run.


## MODIFIED Requirements

### Requirement: mirror-equivalence-golden-snapshot
Self-contained `tests/test_convert_equivalence.py` SHALL prove matching-context byte equivalence through production and explore entries against the shared full-page kernel, as defined by `convert/spec.md`. It SHALL NOT depend on external cached fixtures.

#### Scenario: golden-snapshot-diff-is-zero
- **WHEN** embedded HTML and matching rules/context pass through both paths
- **THEN** the core Markdown SHALL be identical after removing only declared wrappers.

#### Scenario: golden-snapshot-fails-on-drift
- **WHEN** either mirror omits infobox, preprocessing or shared post-ops
- **THEN** the proof SHALL fail and identify the diverging path.
