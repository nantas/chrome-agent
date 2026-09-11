# Specification: mediawiki-cache-integrity

## Purpose

Preserve exact MediaWiki page identity and admit only acquisition-compatible cache content.

## Requirements

### Requirement: exact-cache-identity
The cache SHALL use a versioned filesystem-safe key derived from the exact title within platform/domain scope, and SHALL verify stored title before returning data. It SHALL NOT infer titles by reversing underscore substitution. Distinct titles SHALL NOT share accepted content, including when a legacy filename collides. Writes SHALL use unique temporary files and atomic replacement.

#### Scenario: separator-and-underscore-titles
- **WHEN** pages titled `A/B`, `A_B`, `A:B`, `A B`, and a Unicode title are saved and loaded
- **THEN** each SHALL return its own original title and content without creating title-derived subdirectories
- **AND** enumeration SHALL return original titles from metadata.

#### Scenario: concurrent-writes
- **WHEN** concurrent workers save different titles or update the same title
- **THEN** readers SHALL observe complete JSON entries, and workers SHALL NOT share a temporary filename.

### Requirement: conservative-legacy-cache-read
The cache SHALL prefer valid new-format entries and MAY read legacy entries only after validating exact stored title and required content. Both the original space-normalized legacy name and the separator-sanitized patch name SHALL be considered safely within the cache directory. Missing identity, corrupt JSON, or a different title SHALL be treated as a miss with a diagnostic. Reading SHALL NOT delete or relabel legacy content.

#### Scenario: legacy-collision
- **WHEN** the legacy candidate for `A/B` contains title `A_B`
- **THEN** loading `A/B` SHALL reject it rather than returning another page.

#### Scenario: valid-legacy-html
- **WHEN** a legacy entry has exact title, compatible source metadata when present, nonempty HTML and no acquisition marker
- **THEN** an HTML request MAY reuse that entry through explicit in-memory compatibility adaptation, leaving the source file unchanged.

### Requirement: acquisition-aware-cache-admission
A shared admission function SHALL validate identity, source API identity when recorded, effective acquisition mode, and mode-required payload. The effective mode SHALL come from the resolved content strategy, including default profiles. Explicitly different or unknown modes SHALL be rejected; markerless legacy entries MAY be accepted only when one required representation is unambiguous. HTML mode SHALL require nonempty `html`; wikitext mode SHALL require a string `wikitext` (empty wikitext is a valid page); hybrid mode SHALL require wikitext plus nonempty rendered HTML when its resolved strategy requires rendered fallback. Missing rendered HTML in a hybrid entry SHALL NOT satisfy an HTML request.

#### Scenario: hybrid-to-html
- **WHEN** current mode is `html_rendered` and cached mode is hybrid with only wikitext
- **THEN** admission SHALL reject with expected/actual mode and missing-payload diagnostics, without pretending the entry is HTML.

#### Scenario: incompatible-source-or-corrupt-payload
- **WHEN** the stored API endpoint conflicts with the current source, JSON is corrupt, or required payload is absent
- **THEN** the entry SHALL NOT count as a compatible cache hit.
