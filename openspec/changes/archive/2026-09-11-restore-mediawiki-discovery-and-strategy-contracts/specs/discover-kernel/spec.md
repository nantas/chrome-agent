# Specification Delta

## Capability 对齐（已确认）

- Capability: `discover-kernel`
- 来源: `proposal.md` / 用户已授权两组修复目标
- 变更类型: `modified`
- 用户确认摘要: 规划两组修复，ns0 空目录按建议归 Misc，不处理历史产物。

## 规范真源声明

- 本文件为本 capability 在本 change 的行为规范真源；design/tasks/verification 必须引用本文件。
- 项目页面回写不得替代本文件。

## 归档目标

`openspec/specs/discover-kernel/spec.md`；下列 MODIFIED 名称与原 requirement 精确一致。

## MODIFIED Requirements

### Requirement: pipeline-manifest-source

Pipeline SHALL obtain its page manifest exclusively from `--from-manifest` or an existing `page_manifest.json` in its output directory, validate it before network activity, and run only fetch/convert/assemble. Pipeline SHALL NOT discover pages, mutate the supplied manifest, or accept a discover phase as a successful no-op. Input compatibility SHALL follow `cli`'s manifest compatibility requirement.

#### Scenario: missing-manifest
- **WHEN** neither manifest source exists
- **THEN** pipeline SHALL return a manifest-required invalid-arguments error before API probing or extraction.

#### Scenario: unsupported-discover-phase
- **WHEN** pipeline receives `--phase discover`, with or without an existing manifest
- **THEN** it SHALL reject the phase and direct callers to public crawl discovery-only, without false success.

#### Scenario: consume-confirmed-manifest
- **WHEN** a valid accepted manifest is supplied
- **THEN** pipeline SHALL preserve its included pages and target paths, subject only to explicit supported scope-reducing flags, without rediscovery.

### Requirement: explore-discovery-modules

Explore SHALL own page enumeration and its allpages/homepage implementations. It SHALL expose an entry accepting an already validated frozen strategy and run directory, dispatch to `scripts/explore/discovery_allpages.py` or `discovery_homepage.py`, and publish page manifest and summary artifacts. This entry SHALL NOT run the full site-analysis probe/scaffold workflow. Shared API/infrastructure imports MAY cross into pipeline using absolute imports; discovery logic SHALL remain in explore.

#### Scenario: frozen-allpages-strategy
- **WHEN** the accepted strategy has no homepage discovery configuration
- **THEN** explore SHALL execute allpages enumeration using the selected discovery strategy and existing API/rate-limit settings without site remeasurement.

#### Scenario: frozen-homepage-strategy
- **WHEN** the accepted strategy declares homepage discovery
- **THEN** explore SHALL execute the homepage discovery kernel through the same artifact publication contract.

## ADDED Requirements

### Requirement: discovery-manifest-contract

New manifests SHALL declare `schema_version: 2`, target domain, strategy fingerprint, pages with title/ns/target_directory/target_filename, explicit boolean `is_list_page`, and list-page eligibility decisions. Discovered identities SHALL be resolved consistently with redirect, scope and exclusion rules. Target path collisions SHALL be reported before extraction. Manifest data SHALL remain a run artifact outside strategy frontmatter.

#### Scenario: included-list-page
- **WHEN** an identified configured list page passes the same scope and exclusion rules as other pages
- **THEN** its canonical page SHALL be included once, marked `is_list_page: true`, and linked to its configured index directory.

#### Scenario: list-content-without-eligible-page
- **WHEN** list content exists but the corresponding page is missing, unresolved, outside scope or excluded
- **THEN** discovery SHALL record an explicit skip reason; content alone SHALL NOT authorize adding a page or bypassing exclusions.

#### Scenario: namespace-path-collision
- **WHEN** two retained identities map to the same target path
- **THEN** discovery SHALL report the collision and SHALL NOT publish a success manifest eligible for extraction.

### Requirement: unclassified-main-namespace-directory

Discovery SHALL assign `Misc` only when namespace is 0, classification is empty or Misc, and the existing target directory is empty. Existing classified directories and category/other namespace mappings SHALL remain intact. The same rule SHALL apply wherever either discovery route emits such an unclassified page.

#### Scenario: unclassified-ns0
- **WHEN** an ns0 page has no effective classification and no existing directory
- **THEN** the emitted target directory SHALL be `Misc` and summary SHALL count it there.

#### Scenario: preserve-special-namespaces
- **WHEN** pages have category namespace 14, namespace 3000, or existing StS1/StS2/classified directories
- **THEN** existing special directory and prefix behavior SHALL be preserved, without an added Misc layer.

### Requirement: summary-reflects-discovery-evidence

Discovery summary SHALL be derived from the published manifest and measured discovery outcomes, including retained page counts, directory tree, real versus generated indexes, exclusions, failures and timing estimates with their basis. Unknown counters/rates SHALL be null with an explicit unknown reason, never fabricated zero. Artifact references SHALL resolve relative to the summary location. Partial results SHALL identify incomplete scope; total enumeration failure SHALL return failure and SHALL NOT produce an extraction-eligible success manifest.

#### Scenario: measured-summary
- **WHEN** discovery completes with counted filters and known request outcomes
- **THEN** directory counts SHALL equal retained manifest counts, exclusions SHALL reflect observed removals, and failure rates/estimated duration SHALL expose their actual denominator/basis.

#### Scenario: unknown-or-partial-outcomes
- **WHEN** an upstream operation cannot provide reliable counts or part of enumeration fails
- **THEN** unknown values SHALL remain distinguishable from measured zero, result SHALL be partial_success or failure as appropriate, and automatic extraction SHALL be blocked pending the applicable confirmation.

### Requirement: list-index-consumer-agreement

Assembly SHALL use real list content only for included pages marked as eligible list pages, and generate ordinary member indexes for directories without such pages. Summary SHALL make the same distinction. Bare `list_page_content` entries SHALL NOT bypass page eligibility. Real list conversion SHALL preserve link targets when replacing a redundant list-page file with index.md.

#### Scenario: real-list-index
- **WHEN** an included marked list page converts successfully
- **THEN** assembly SHALL produce the configured real index content, maintain valid references to it, and SHALL NOT silently replace it with a generic member listing.

#### Scenario: excluded-or-absent-list-index
- **WHEN** a list page is absent/excluded but its directory contains eligible entities
- **THEN** assembly SHALL skip its detached content with the recorded reason and generate the ordinary directory index indicated by summary.
