# Specification Delta

## Capability 对齐（已确认）

- Capability: `sample-self-check`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认自检体系从 S1-S7 升级到 S1-S12，新增 5 个检查项，升级 4 个既有检查项标准

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: self-check-s1-image-retention

The system SHALL verify that image count in converted Markdown matches the original HTML (after excluding noise images matching `skip_patterns`), AND that all retained images use full URLs (no relative `/images/` paths).

#### Scenario: s1-pass-with-full-urls
- **WHEN** sample conversion is complete
- **THEN** the system SHALL count valid images in original HTML (excluding those with `src="data:image/gif;base64"` that lack a `data-src`, AND excluding images matching `skip_patterns`)
- **THEN** the system SHALL count `![]()` occurrences in converted Markdown
- **THEN** the system SHALL verify every `![]()` uses a full URL starting with `http://` or `https://`
- **THEN** if `M == N` AND all URLs are full URLs, S1 SHALL be marked `pass`
- **THEN** if any image has a relative path (starts with `/`), S1 SHALL be marked `fail` with `fixable_type: "relative_image_url"`

### Requirement: self-check-s2-link-resolution

The system SHALL verify that all internal links in the Markdown use full URLs and there are zero relative `/wiki/` links.

#### Scenario: s2-zero-relative-links
- **WHEN** sample conversion is complete
- **THEN** the system SHALL scan all `[text](url)` patterns in the Markdown
- **THEN** if any `url` starts with `/wiki/` or `/images/`, S2 SHALL be marked `fail` with `fixable_type: "relative_link"`
- **THEN** if all `url` values are full `https://` URLs or anchor-only `#...` links, S2 SHALL be marked `pass`

### Requirement: self-check-s3-infobox-extraction

The system SHALL verify infobox extraction quality: at least 3 fields present, key fields (name, id) non-empty, and no raw HTML tag residue in field values.

#### Scenario: s3-pass-with-quality-checks
- **WHEN** sample conversion is complete and the original page has an infobox
- **THEN** the system SHALL verify the infobox table has ≥ 3 fields
- **THEN** the system SHALL verify that `Name` and at least one ID field (`Collectible ID` / `Entity ID` / `Trinket ID`) are present and non-empty
- **THEN** the system SHALL scan infobox field values for raw HTML tags (`<a`, `<img`, `<span`, `</div`)
- **THEN** if any raw HTML tag is found, S3 SHALL be marked `fail` with `fixable_type: "infobox_html_residue"`
- **THEN** if field count < 3 or key fields empty, S3 SHALL be marked `fail` with `fixable_type: "infobox_incomplete"`

### Requirement: self-check-s5-text-integrity

The system SHALL verify that the converted Markdown text has no detectable formatting anomalies, including original anomalies PLUS new HTML tag residue patterns.

#### Scenario: s5-pass-fail
- **WHEN** sample conversion is complete
- **THEN** the system SHALL scan for the following anomaly patterns:
  - Missing space around version numbers: `([a-z])(\d+(?:\.\d+)*)([a-z])`
  - Base64 placeholder residue: `data:image/gif;base64`
  - Escape artifacts: `\*\*\*` or `\\\*+`
  - Repeated link text: `(\w[\w\s]{1,15}?) +\1`
  - **NEW**: Raw closing HTML tags: `</a>` or `</span>` or `</div>` in output
  - **NEW**: Unresolved HTML entities: `&amp;` or `&lt;` or `&gt;` in output
- **THEN** if any anomaly pattern matches, S5 SHALL be marked `fail`
- **THEN** if no anomalies found, S5 SHALL be marked `pass`

### Requirement: self-check-s6-table-integrity

The system SHALL verify that list/summary tables maintain row count within a 5% tolerance of the original HTML.

#### Scenario: s6-row-count-tolerance
- **WHEN** sample conversion is complete and the original page contains data tables
- **THEN** the system SHALL count original `<tr>` rows in source HTML (excluding header rows)
- **THEN** the system SHALL count Markdown table data rows (lines starting with `|` excluding separator lines)
- **THEN** if `|MD_rows - HTML_rows| / HTML_rows > 0.05`, S6 SHALL be marked `fail`
- **THEN** if the deviation is ≤ 5%, S6 SHALL be marked `pass`

## ADDED Requirements

### Requirement: self-check-s8-section-completeness

The system SHALL verify that all `mw-headline` sections from the source HTML are preserved as Markdown headings.

#### Scenario: s8-all-sections-present
- **WHEN** sample conversion is complete
- **THEN** the system SHALL extract all `mw-headline` span texts from the source HTML
- **THEN** the system SHALL extract all `#`, `##`, `###` heading texts from the Markdown
- **THEN** if any `mw-headline` text does not appear as a Markdown heading, S8 SHALL be marked `fail` with details of missing sections
- **THEN** if the count mismatch exceeds 2, S8 SHALL be marked `fail` with `fixable_type: "section_loss"`
- **THEN** if all sections are present, S8 SHALL be marked `pass`

#### Scenario: s8-toc-heading-excluded
- **WHEN** the source HTML contains a "Contents" heading from the TOC
- **THEN** this heading SHALL NOT be counted in the expected section list

### Requirement: self-check-s9-navigation-leakage

The system SHALL verify that navigation sidebar content has NOT leaked into the Markdown body.

#### Scenario: s9-no-nav-leak
- **WHEN** sample conversion is complete
- **THEN** the system SHALL scan the Markdown for clusters of known navigation keywords
- **THEN** if ≥ 3 consecutive lines contain known nav keywords (Achievements, Challenges, Characters, Bosses, Trinkets, Items, Modes, Curses, Objects, Seeds, Effects, Endings, Collection, Version History, Modding, Music), S9 SHALL be marked `fail` with `fixable_type: "nav_leak"`
- **THEN** if no such clusters exist, S9 SHALL be marked `pass`

### Requirement: self-check-s10-youtube-title-quality

The system SHALL verify that YouTube video links use descriptive titles rather than generic "YouTube Video" text, OR have no video links at all if the page has no videos.

#### Scenario: s10-no-generic-titles
- **WHEN** sample conversion is complete
- **THEN** the system SHALL scan for `[YouTube Video](https://www.youtube.com/...)` patterns
- **THEN** if any such generic title is found, S10 SHALL be marked `fail` with `fixable_type: "youtube_title"`
- **THEN** if all YouTube links have unique, non-generic titles, S10 SHALL be marked `pass`
- **THEN** if no YouTube links exist at all, S10 SHALL be marked `skip`

### Requirement: self-check-s11-zero-relative-links

The system SHALL verify that the Markdown output contains ZERO relative `/wiki/` or `/images/` link references.

#### Scenario: s11-no-relative-residue
- **WHEN** sample conversion is complete
- **THEN** the system SHALL grep the Markdown for `](/wiki/` and `](/images/` patterns
- **THEN** if any matches are found, S11 SHALL be marked `fail` with `fixable_type: "relative_link"` and the count of occurrences
- **THEN** if zero matches are found, S11 SHALL be marked `pass`

### Requirement: self-check-s12-infobox-semantic-quality

The system SHALL verify infobox field semantic quality: Name field has spaces between words, ID fields contain only digits/dots (no navigation text), and no field values are image filenames masquerading as text.

#### Scenario: s12-name-has-spaces
- **WHEN** sample conversion is complete and infobox has a Name field
- **THEN** the system SHALL check if the Name value contains camelCase concatenation (e.g., "TheSadOnion")
- **THEN** if Name matches `[a-z][A-Z]` pattern, S12 SHALL be marked `fail` with `fixable_type: "name_spacing"`
- **THEN** if Name ends with `.png`, `.jpg`, or `.gif`, S12 SHALL be marked `fail` with `fixable_type: "name_is_filename"`

#### Scenario: s12-id-fields-clean
- **WHEN** sample conversion is complete and infobox has ID fields (Collectible ID, Trinket ID, Entity ID)
- **THEN** the system SHALL verify ID values contain only digits, dots, and optional dashes
- **THEN** if any ID value contains link text (e.g., "[...](/wiki/...)") or navigation text ("None", "[](...)"), S12 SHALL be marked `fail` with `fixable_type: "id_navigation_leak"`

### Requirement: auto-remediation-extended

The system SHALL recognize the following new fixable types in addition to the existing set:

- `relative_image_url` — remediate by re-running `convert_images_to_md()` with full URL domain
- `relative_link` — remediate by re-running `convert_links_to_md()` with full URL domain
- `infobox_html_residue` — remediate by re-running `convert_infobox()` with balanced div matching
- `infobox_incomplete` — NOT auto-fixable; requires strategy field handler configuration
- `section_loss` — test balanced element removal; auto-fixable via TOC/navbox removal retry
- `nav_leak` — auto-fixable via additional `remove_all()` calls for nav-header/sidebar dl
- `youtube_title` — auto-fixable via oEmbed API retry
- `name_spacing` — NOT auto-fixable; requires font image alt processing in strategy
- `name_is_filename` — NOT auto-fixable; requires strategy extraction handler
- `id_navigation_leak` — auto-fixable via infobox-nav-cur extraction retry

#### Scenario: auto-remediation-new-types
- **WHEN** self-check fails on a new fixable type (`relative_link`, `nav_leak`, `section_loss`, `youtube_title`, `infobox_html_residue`, `id_navigation_leak`)
- **THEN** the auto-remediation loop SHALL attempt remediation up to 2 iterations
- **THEN** after remediation, the system SHALL re-run the failed checks
