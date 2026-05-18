# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户选择三层方案，需新增 Phase 0、redirect 修复、自动 link fix

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: phase-homepage-entry-point

The system SHALL support `--phase homepage` as a pipeline entry point that runs homepage-driven discovery followed by Phase B and Phase C.

When `--phase homepage` is specified:
- Phase 0 SHALL execute before Phase B
- Phase A SHALL be skipped (discovery is homepage-driven, not allpages)
- The manifest produced by Phase 0 SHALL be consumed by Phase B

#### Scenario: phase-homepage-with-bc

- **WHEN** `chrome-agent mediawiki pipeline --phase homepage,B,C` is invoked
- **THEN** Phase 0 (homepage discovery + page assignment) SHALL execute
- **THEN** Phase B SHALL consume the Phase 0 manifest
- **THEN** Phase C SHALL execute normally
- **THEN** Phase A SHALL NOT execute

#### Scenario: phase-homepage-only

- **WHEN** `chrome-agent mediawiki pipeline --phase homepage` is invoked
- **THEN** only Phase 0 SHALL execute, producing a manifest
- **THEN** no extraction or assembly SHALL be performed

#### Scenario: phase-homepage-missing-strategy

- **WHEN** `--phase homepage` is specified but strategy has no `api.homepage` config
- **THEN** pipeline SHALL log error and return non-zero exit code
- **THEN** no API calls SHALL be made

### Requirement: standalone-redirect-handling

The system SHALL include `redirects=true` in all MediaWiki `action=parse` API calls made by `standalone.py`.

`fetch_and_convert()` SHALL pass `redirects=true` when calling `client.parse()`.

#### Scenario: standalone-follows-redirect

- **WHEN** `fetch_and_convert()` is called for a page that is a redirect (e.g., `Main_Page`)
- **THEN** the API call SHALL include `redirects=true`
- **THEN** the returned content SHALL be from the resolved page
- **THEN** the output SHALL contain content, not an empty file

### Requirement: explore-redirect-handling

The system SHALL include `redirects=true` in the `_fetch_wikitext()` MediaWiki API call in `scripts/explore/main.py`.

#### Scenario: explore-wikitext-fetch-follows-redirect

- **WHEN** `_fetch_wikitext()` is called for a page that is a redirect
- **THEN** the API call SHALL include `redirects=true`
- **THEN** the returned wikitext SHALL be from the resolved page

### Requirement: auto-link-fix-after-pipeline

The system SHALL automatically invoke `fix_links_in_dir()` after Phase C completes (or after Phase B if Phase C is not run).

#### Scenario: link-fix-after-phase-c

- **WHEN** pipeline completes Phase C successfully
- **THEN** `fix_links_in_dir(output_dir, domain, manifest_pages)` SHALL be called
- **THEN** link fix statistics SHALL be logged
- **THEN** link fix failure SHALL NOT cause pipeline failure (logged as warning)

#### Scenario: link-fix-after-phase-b-only

- **WHEN** pipeline runs only Phase B (no Phase C)
- **THEN** `fix_links_in_dir()` SHALL still be called after Phase B completes
