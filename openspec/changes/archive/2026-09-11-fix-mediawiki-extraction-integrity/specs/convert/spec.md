# Specification Delta

## Capability 对齐（已确认）

- Capability: `convert`
- 来源: `proposal.md` / 用户授权按建议创建 change。
- 变更类型: modified
- 用户确认摘要: 收敛共享编排，修复 infobox 丢失并保护生产链接上下文。

## 规范真源声明

本文件是该 capability 在本 change 中的行为规范真源；design/tasks/verification SHALL 引用本文件。

## MODIFIED Requirements

### Requirement: convert-kernel-three-layer-interface
The shared kernel SHALL retain four public entry points: the stateful `HtmlToMarkdownConverter` implementation class, the stateless `convert_html_to_markdown()` convenience function, the single full-page `convert_page_full()` orchestration function, and `apply_post_conversion_ops()` as the sole Markdown post-transform implementation. The full-page function SHALL remain compatible with existing two-argument callers and SHALL accept optional stateful converter and source-directory context.

The full-page sequence SHALL be extract infobox → preprocess HTML → convert body → prepend extracted infobox → apply post-ops exactly once. CV3 SHALL delegate to this entry. CV4 SHALL build its link-index/redirect state and supply that converter to the same entry, keeping frontmatter, heading and card-stat wrapping outside the core. It SHALL NOT independently repeat or omit those five steps. CV5 SHALL retain generic empty-domain behavior. Extraction rules supplied to the full-page entry and the converter SHALL agree; conflicting contexts SHALL be rejected.

The shared entry SHALL resolve infobox URL context from configured image base URL first, then supplied converter domain, then empty string. It SHALL preserve the supplied link index and source directory in both infobox and body link rendering. No caller-specific domain derivation SHALL duplicate this rule.

#### Scenario: cv4-stateful-full-page-entry
- **WHEN** CV4 converts a page with an existing link index and source directory
- **THEN** the full-page core SHALL use that state for both infobox and body without rebuilding an empty converter.

#### Scenario: post-ops-have-one-implementation-in-kernel
- **WHEN** any path applies text normalization, URL conversion, YouTube cleanup, escape cleanup or Markdown cleanup operations
- **THEN** it SHALL use `apply_post_conversion_ops`, once after infobox prepend in the full-page flow, without mirrored transform logic.

#### Scenario: legacy-two-argument-call
- **WHEN** `convert_page_full(html, rules)` is called without context
- **THEN** it SHALL retain stateless behavior, including configured base URL or generic empty-domain handling.

#### Scenario: contextual-infobox-links
- **WHEN** a page in `bosses/` links from its infobox to a manifest page in `endings/`
- **THEN** the link SHALL resolve relative to `bosses/`, using the same link index as body links.

#### Scenario: conflicting-converter-rules
- **WHEN** the provided converter has extraction rules inconsistent with the full-page request
- **THEN** conversion SHALL reject the conflicting context rather than apply two different rule sets.

#### Scenario: escape-artifact-cleanup-is-uniform-safety-net
- **WHEN** Markdown contains backslash-escape artifacts
- **THEN** the shared post-op safety net SHALL clean them uniformly, including when no optional normalization keys are configured.

#### Scenario: convert-page-full-includes-post-op-step
- **WHEN** `convert_page_full(html, extraction_rules)` returns
- **THEN** shared post-ops SHALL have run after infobox prepend, including unconditional escape cleanup and configured optional transforms.

#### Scenario: cv3-and-cv4-honor-same-post-ops-for-real-strategies
- **WHEN** rules enable text normalization, URL conversion, YouTube cleanup or Markdown cleanup
- **THEN** both CV3 and CV4 SHALL obtain the identical transforms through the shared full-page entry, as proven by an enabled-key fixture.


### Requirement: mirror-equivalence-golden-snapshot
Self-contained tests in `tests/test_convert_equivalence.py` SHALL prove shared-core byte equivalence for matching HTML, rules and rendering context across CV3/CV4 and generic CV5. They SHALL strip only declared path wrappers (pipeline YAML/title/card-stat wrapping), never infobox or shared post-ops. Existing coverage of wiki links, row/col spans, pipe cells, asterisks, parenthesized/apostrophe titles, image/link adjacency, tooltip pairs and preprocessing-only footer removal SHALL remain. Tests SHALL enable real post-op keys and include an enabled infobox with unique field labels and values.

#### Scenario: cv3-explore-mirror-matches-kernel
- **WHEN** an embedded fixture is converted by explore and the shared entry with the same context
- **THEN** core Markdown SHALL be byte-identical.

#### Scenario: cv4-pipeline-mirror-matches-kernel
- **WHEN** the public `convert_single_page` entry and shared core convert the same fixture with matching context
- **THEN** core Markdown SHALL be byte-identical after removing only declared wrappers.

#### Scenario: cv5-generic-mirror-matches-kernel
- **WHEN** CV5 and the full-page entry convert generic HTML with empty rules and domain
- **THEN** outputs SHALL remain byte-identical.

#### Scenario: infobox-canary
- **WHEN** the fixture has `Seed Chance` and a unique value solely inside an enabled infobox
- **THEN** both production and shared output SHALL retain the field/value once under `## Infobox`, and a mirror omitting extraction/prepend SHALL fail.

#### Scenario: fixture-discriminates-preprocessing
- **WHEN** a mirror omits preprocessing of the fixture footer
- **THEN** equivalence SHALL fail.

#### Scenario: test-never-skips
- **WHEN** the checkout lacks external caches
- **THEN** all embedded-fixture proofs SHALL execute without network or skip.
