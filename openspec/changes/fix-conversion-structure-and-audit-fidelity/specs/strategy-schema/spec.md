# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy-schema`
- 来源: `proposal.md` / 用户要求按已讨论的完整修复方案创建单一 change。
- 变更类型: modified（为既有能力补充本次诊断所得契约）。
- 用户确认摘要: 修复共享结构根因、来源自检和声明式标题语义，不重新抓取、不以检查全绿代替内容验证。

## 规范真源声明

本文件是本 change 的行为规范真源；design/tasks/verification SHALL 引用本文件，项目页面不替代 delta。

## ADDED Requirements

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
