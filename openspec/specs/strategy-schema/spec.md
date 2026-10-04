# Specification Delta

## Purpose

Define validated strategy frontmatter fields and shared configuration contracts for extraction and conversion.


## Capability 对齐（已确认）

- Capability: `strategy-schema`
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: grill session 确认——frontmatter 新增 `samples` 字段（page + label）. Modified by tdd-schema-alignment: C9 TDD 引用 + tech-stack TDD 约定. Modified by maker-taptap-cn-cdp-api-bridge: `api.platform: rest`、`requires_authentication`、`api.auth`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## Requirements

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

### Requirement: semantic-heading-normalization-config
Extraction configuration SHALL accept optional heading_normalization, a list of mappings containing required nonempty heading_selector and label_selector CSS strings. An optional label_aliases map SHALL declare exact source-to-visible label pairs using nonempty strings; no fuzzy matching SHALL occur. Omitted or empty configuration SHALL disable pairing. Unknown keys, malformed mappings and invalid selectors SHALL be rejected explicitly through the shared extraction validation boundary. Pairing SHALL use the heading's immediate next element sibling with the same parent, ignoring whitespace/comments; the source heading supplies level and identifier. This configuration SHALL be consumed identically by shared preprocessing and source-audit expectation construction without a site-name branch.

#### Scenario: valid-dd2-pair-rule
- **WHEN** rules declare heading_selector selecting semantic h3 nodes and label_selector selecting .headerdd2 visible labels
- **THEN** validation SHALL admit the rule and shared conversion/audit SHALL apply the same declared pairing contract.

#### Scenario: absent-and-invalid-rules
- **WHEN** heading_normalization is absent or empty
- **THEN** legacy behavior SHALL remain; a present malformed rule SHALL instead fail explicitly rather than being ignored.

### Requirement: heading-config-registration-and-samples
Frontmatter SHALL remain authoritative over registry mirrors. Heading normalization and any retained cleanup capabilities SHALL be discoverable by existing validation/capability gates, with supported fields and behavior documented. DD2 configuration changes SHALL include representative hidden-heading and structural regression fixtures; golden updates SHALL be justified by independently verified semantic corrections, never solely by new output.

#### Scenario: configuration-through-all-entry-points
- **WHEN** strategy loading, explore freeze validation, pipeline or matched-strategy crawl reads a valid heading rule
- **THEN** the rule SHALL remain available unchanged to shared conversion and SHALL NOT be silently discarded or rejected as an unknown capability.

#### Scenario: sample-update-with-evidence
- **WHEN** corrected heading or block structure changes a DD2 sample
- **THEN** the diff SHALL show intended semantic changes with independent image/link/table checks, and the site-samples suite SHALL pass after reviewed baseline changes.

#### Scenario: explicitly-aliased-label
- **WHEN** a configured label_aliases entry exactly maps the hidden label to the adjacent visible label
- **THEN** the pair SHALL preserve the visible label text/assets and source heading level/identifier; any other mismatch SHALL remain unmatched.

### Requirement: merged-cell-icon-label-map
策略 SHALL 支持可选 `extraction.table_options.merged_cell_icon_labels`，类型为非空字符串键值的映射。键为源 img alt（只 trim 首尾空白）的精确值，值为纯文本语义名称；配置键值 SHALL 不含首尾空白或换行，禁止空名称，拒绝非映射/非字符串值，错误 SHALL 标明字段路径并显式失败，不降级通用转换。缺省或空映射 SHALL 使用共享内核默认名称解析。该字段 SHALL 只影响合并格延续槽位，frontmatter 为真源，所有共享转换路径 SHALL 接收相同配置。既有 table_options 字段 SHALL 保持兼容，未知键 SHALL 继续被拒绝。

#### Scenario: exact-mapping
- **WHEN** 配置 `Dd2 token vulnerable.png: Vulnerable` 和 `Dd2 token daze.png: Daze`
- **THEN** 仅精确命中的 alt 使用对应名称，大小写变化或相似文件名不命中。

#### Scenario: invalid-map
- **WHEN** 映射为列表、含空键值、非字符串、首尾空白或换行
- **THEN** 策略校验返回具体字段错误，不进入转换或静默忽略。

#### Scenario: absent-map-and-shared-paths
- **WHEN** 字段缺省或为空，或同一有效映射经 explore/pipeline/crawl 进入共享内核
- **THEN** 缺省行为有效，等价 HTML/config/context 的 core 输出一致。
