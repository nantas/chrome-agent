# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-schema`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: grill session 确认——frontmatter 新增 `samples` 字段（page + label）. Modified by tdd-schema-alignment: C9 TDD 引用 + tech-stack TDD 约定. Modified by maker-taptap-cn-cdp-api-bridge: `api.platform: rest`、`requires_authentication`、`api.auth`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

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

The system SHALL accept an optional `api.auth` object in strategy frontmatter for `api.platform: rest`, containing `source` (token storage location), `key` (storage key name), and `header_format` (Authorization header template).

#### Scenario: Strategy with auth config
- **WHEN** a strategy file declares `api.platform: rest` with `api.auth` containing valid `source`, `key`, and `header_format`
- **THEN** the system SHALL parse these fields and make them available to the fetch phase

### Requirement: Platform Validation

The `validate_api_config()` function SHALL no longer reject non-`mediawiki` platform values unconditionally. It SHALL accept `rest` as a valid platform. For `rest` platform, it SHALL NOT require MediaWiki-specific capabilities.

#### Scenario: rest platform passes validation
- **WHEN** `validate_api_config()` receives a strategy with `api.platform: rest`
- **THEN** it SHALL return `None` (no error)

#### Scenario: Unknown platform still rejected
- **WHEN** `validate_api_config()` receives a strategy with an unknown `api.platform` value
- **THEN** it SHALL return an error message as before

### Requirement: Samples frontmatter field
The strategy YAML frontmatter SHALL support an optional `samples` field containing a list of sample page declarations.

Each entry SHALL have:
- `page` (string, required): URL path or cache-safe path identifying the page
- `label` (string, required): Human-readable description of the page's representative characteristics

#### Scenario: Strategy with samples
- **WHEN** strategy.md frontmatter includes:
  ```yaml
  domain: developer.nintendo.com
  samples:
    - page: "Packages/Docs/Guides/Online_Play_Guide/contents/Pages/Page_239857945.html"
      label: "复杂嵌套表格页面"
    - page: "Packages/Network/Guides/NX-Account_Guide/contents/Pages/Page_106359813.html"
      label: "纯文本无表格页面"
  ```
- **THEN** parsers SHALL extract the `samples` list as an array of dicts with `page` and `label` keys

#### Scenario: Strategy without samples
- **WHEN** strategy.md has no `samples` field
- **THEN** the field SHALL default to an empty list; no error SHALL be raised

### Requirement: C9 references TDD vertical slice
AGENTS.md §0.5 C9 SHALL reference the TDD vertical slice methodology, directing developers to `08-tech-stack.md` §4 for detailed guidance.

#### Scenario: Developer reads C9
- **WHEN** a developer reads AGENTS.md §0.5 C9
- **THEN** the constraint text SHALL include "遵循 vertical slice TDD（详见 `08-tech-stack.md` §4 TDD 约定）"

### Requirement: TDD conventions paragraph in tech-stack
`docs/architecture/08-tech-stack.md` §4 SHALL include a "TDD 约定" subsection documenting the project's test-driven development methodology.

The subsection SHALL cover:
- Vertical slice principle: one test → one implementation → pass, repeated
- Anti-horizontal slicing: do not write all tests then all code
- Behavior over implementation: tests verify public interfaces, not internals
- Refactor only after GREEN

#### Scenario: Developer reads TDD conventions
- **WHEN** a developer reads `08-tech-stack.md` §4
- **THEN** a "TDD 约定" subsection SHALL be present with the four principles listed above
