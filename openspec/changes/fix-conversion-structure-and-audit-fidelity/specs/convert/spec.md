# Specification Delta

## Capability 对齐（已确认）

- Capability: `convert`
- 来源: `proposal.md` / 用户要求按已讨论的完整修复方案创建单一 change。
- 变更类型: modified（为既有能力补充本次诊断所得契约）。
- 用户确认摘要: 修复共享结构根因、来源自检和声明式标题语义，不重新抓取、不以检查全绿代替内容验证。

## 规范真源声明

本文件是本 change 的行为规范真源；design/tasks/verification SHALL 引用本文件，项目页面不替代 delta。

## ADDED Requirements

### Requirement: tooltip-normalization-preserves-dom
Tooltip normalization SHALL use structural DOM operations, unwrap only targeted tooltip/icon-size containers, and preserve unrelated elements and their nesting. It SHALL NOT globally delete closing span tags. Icon/text link merging SHALL retain image identity and visible text, merge only adjacent compatible links with the same destination, and leave different-target links distinct. Shared conversion SHALL retain block boundaries following ordinary, empty and nested spans without requiring site-specific nowrap cleanup.

#### Scenario: ordinary-span-before-block
- **WHEN** an ordinary or nowrap span containing an image precedes a heading and table
- **THEN** the heading SHALL remain a standalone heading and table rows SHALL remain separate, with or without the nowrap cleanup setting.

#### Scenario: nested-tooltip-and-links
- **WHEN** targeted tooltip containers coexist with nested ordinary spans and same-target icon/text links
- **THEN** only targeted wrappers SHALL be unwrapped and compatible links SHALL merge without losing image/text content or affecting surrounding block structure.

#### Scenario: distinct-link-targets
- **WHEN** adjacent icon and text links have different destinations
- **THEN** both destinations SHALL remain distinct.

### Requirement: wrapped-list-items-preserved
The configured unwrap_list_item_wrappers cleanup SHALL preserve list items hidden behind supported presentation wrappers, item order, images, and genuine nested list ownership. It SHALL handle arbitrary finite wrapper depth without a fixed three-pass limit, terminate by structurally removing wrappers, and leave ordinary inline content within list items intact. It SHALL NOT flatten child lists into parent siblings.

#### Scenario: wrapped-reward-list
- **WHEN** ul contains big wrapping li with reward images
- **THEN** full conversion SHALL retain every item and image once, as proven by the Shambler four-image regression.

#### Scenario: deep-wrappers-and-nested-numbering
- **WHEN** more than three presentation wrappers surround list items containing nested ordered lists
- **THEN** conversion SHALL retain outer order, inner numbering and hierarchy without duplication or loss.

### Requirement: configured-semantic-heading-pairs
Full conversion SHALL normalize explicitly configured pairs of a semantic heading containing hidden label text and its adjacent visible group label into one heading with the source heading level and source identifier, preserving visible label text/assets. Pair matching SHALL require the configured selectors, same parent and next element sibling, and equal nonempty normalized labels or an explicitly configured exact label_aliases correspondence. Visible label images and links SHALL be retained once. Unmatched or ambiguous pairs SHALL remain unchanged with diagnostic evidence; unrelated hidden content SHALL remain excluded. Repeated preprocessing SHALL NOT duplicate headings.

#### Scenario: enemies-group-headings
- **WHEN** DD2 declares matching hidden h3 and visible group-label pairs
- **THEN** the 14 DD2 and 3 Kingdoms group labels SHALL render once each as level-three headings, with following content in original order.

#### Scenario: mismatched-or-unconfigured-pair
- **WHEN** labels differ, selectors are absent, or the visible label is not the next element sibling
- **THEN** no heading pair SHALL be synthesized and no unrelated hidden element SHALL be exposed.

#### Scenario: repeat-normalization
- **WHEN** already normalized content is preprocessed again
- **THEN** heading count, order, identifiers and visible assets SHALL remain unchanged.

### Requirement: cleanup-workarounds-require-conversion-evidence
The change SHALL evaluate strip_empty_inline_tags, strip_empty_paragraphs and unwrap_nowrap_spans independently after the tooltip root fix, using real full conversion. A workaround without demonstrated independent benefit SHALL be removed from this site's active configuration; removal of a registered operation SHALL require a reference audit and compatibility decision. Retained operations SHALL preserve meaningful empty anchor identifiers and media. Structure-only cleanup tests SHALL NOT be treated as proof of conversion correctness.

#### Scenario: fallen-templar-ablation
- **WHEN** each combination of the three cleanup settings is evaluated after the root fix
- **THEN** the evidence SHALL identify which, if any, has independent benefit, and Skills SHALL remain a standalone heading without the nowrap workaround.

#### Scenario: anchor-and-media-safety
- **WHEN** cleanup encounters empty a elements with id/name or elements containing meaningful media
- **THEN** valid anchor information and media SHALL NOT be discarded as empty noise.

### Requirement: structural-fix-shared-entry-proof
Self-contained tests SHALL exercise convert_page_full through existing mirrors and assert content structure as well as byte equivalence under equal rules/context. Fixtures SHALL cover image and link retention, headings, lists and tables without external caches or network. DD2 replay SHALL remain supplemental evidence rather than a formal-suite dependency.

#### Scenario: mirror-and-loss-canaries
- **WHEN** the structural fixtures traverse shared, explore, pipeline and matched-strategy crawl paths
- **THEN** core outputs SHALL be equivalent after only declared wrappers, while deliberate item/image/heading loss SHALL fail independent assertions.
