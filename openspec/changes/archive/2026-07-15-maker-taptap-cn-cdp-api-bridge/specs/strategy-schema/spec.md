# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-schema`
- 来源: `proposal.md` / grill-with-docs session
- 变更类型: modified
- 用户确认摘要: 经 grill 确认，新增 `api.platform: rest` 合法值、`requires_authentication` 顶层字段、`api.auth` 子字段。`anti_crawl_refs` 中的 `auth_wall` 和 `spa_js_render` 不属于反爬范畴，移除。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: REST Platform Type

The system SHALL accept `rest` as a valid value for `api.platform` in strategy frontmatter, alongside the existing `mediawiki` value.

#### Scenario: Strategy with rest platform

- **WHEN** a strategy file declares `api.platform: rest`
- **THEN** the system SHALL recognize it as a RESTful JSON API backend and route accordingly

### Requirement: Requires Authentication Field

The system SHALL accept an optional `requires_authentication` boolean field at the top level of strategy frontmatter, indicating whether site content is behind a login gate.

#### Scenario: Authenticated site declaration

- **WHEN** a strategy file declares `requires_authentication: true`
- **THEN** the system SHALL treat this as an access control signal, distinct from anti-crawl measures

#### Scenario: Public site (default)

- **WHEN** a strategy file omits `requires_authentication`
- **THEN** the system SHALL default to `false`

### Requirement: API Auth Configuration

The system SHALL accept an optional `api.auth` object in strategy frontmatter for `api.platform: rest`, containing:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | yes | Token storage location (`localStorage`, `cookie`, `sessionStorage`) |
| `key` | string | yes | Storage key name (e.g., `taptap_access_token`) |
| `header_format` | string | yes | Authorization header template (e.g., `"Bearer {token}"`) |

#### Scenario: Strategy with auth config

- **WHEN** a strategy file declares `api.platform: rest` with `api.auth` containing valid `source`, `key`, and `header_format`
- **THEN** the system SHALL parse these fields and make them available to the fetch phase

#### Scenario: Missing auth for rest platform

- **WHEN** a strategy declares `api.platform: rest` but omits `api.auth`
- **THEN** the system SHALL still accept the strategy (auth may not apply to all rest endpoints)

## MODIFIED Requirements

### Requirement: Platform Validation

The `validate_api_config()` function SHALL no longer reject non-`mediawiki` platform values unconditionally. It SHALL accept `rest` as a valid platform when the strategy declares `backend: cdp-api-bridge`. For `rest` platform, it SHALL NOT require MediaWiki-specific capabilities or probe the MediaWiki API endpoint.

#### Scenario: rest platform passes validation

- **WHEN** `validate_api_config()` receives a strategy with `api.platform: rest` and `backend: cdp-api-bridge`
- **THEN** it SHALL return `None` (no error) instead of an unsupported platform error message

#### Scenario: Unknown platform still rejected

- **WHEN** `validate_api_config()` receives a strategy with `api.platform: <unknown_value>` where `<unknown_value>` is neither `mediawiki` nor `rest`
- **THEN** it SHALL return an error message as before
