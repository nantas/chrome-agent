# Specification: fetch-content-admission

## Purpose

Prevent challenge interstitials and invalid HTML outputs from being consumed as successful page content across acquisition, conversion and cache reuse.

## Requirements


### Requirement: raw-html-admission
The system SHALL validate acquired HTML before declaring content success, selecting an engine, extracting selectors, converting, or admitting it as reusable successful content. A zero process exit or a successful HTTP status SHALL NOT alone establish content success. Missing, unreadable and empty output SHALL be rejected.

#### Scenario: captured-challenge-with-successful-process
- **WHEN** an engine exits zero and produces the sanitized wiki.gg challenge fixture with a Just a second title, visible verification prompt and challenge-platform script
- **THEN** admission SHALL reject it as a challenge, even with HTTP 200 or unknown HTTP status
- **AND** no successful content artifact SHALL be published

#### Scenario: invalid-output
- **WHEN** an engine reports success but output is absent, unreadable or empty
- **THEN** admission SHALL fail with a distinct output reason rather than fabricate successful content

### Requirement: evidence-based-challenge-classification
The shared classifier SHALL combine challenge-specific DOM or script evidence with page-level verification presentation. It SHALL distinguish an interstitial from ordinary content mentioning Cloudflare or embedding a verification widget. HTTP 403, document size, a generic keyword or a widget alone SHALL NOT identify a Cloudflare challenge. A failed HTTP response SHALL remain unsuccessful regardless of challenge classification.

#### Scenario: normal-article-and-widget
- **WHEN** a normal article mentions Cloudflare or quotes Just a moment, or a normal content page embeds Turnstile without an interstitial
- **THEN** it SHALL NOT be rejected as a challenge solely on that evidence

#### Scenario: unknown-http-forbidden
- **WHEN** a response is 403 without challenge evidence
- **THEN** the fetch SHALL fail without claiming Cloudflare as the cause

### Requirement: admission-evidence-contract
Each attempt SHALL retain process outcome separately from admission outcome and include a machine-readable reason, bounded non-secret evidence, page title, content length and diagnostic artifact reference when available. HTTP status SHALL be observed metadata or null, never inferred as 200 from process success. Evidence pages SHALL remain distinct from successful content artifacts.

#### Scenario: unknown-status
- **WHEN** an adapter provides HTML but no reliable HTTP metadata
- **THEN** http_status SHALL be null and the classifier SHALL still evaluate HTML

#### Scenario: rejected-artifact
- **WHEN** a challenge is rejected
- **THEN** its HTML MAY be retained for diagnosis but SHALL NOT be exposed as the selected successful HTML or reusable successful cache
- **AND** summaries SHALL exclude challenge tokens, cookies and authentication values

### Requirement: shared-consumer-admission
Explore probes, sample acquisition, fetch/crawl HTML acquisition and production HTML cache consumption SHALL use the same classification semantics. Selector extraction and Markdown conversion SHALL consume admitted HTML from the same acquisition, not a separately fetched unchecked response. Existing cache identity, payload and conversion-fingerprint checks SHALL remain in force.

#### Scenario: rejected-sample
- **WHEN** a sample fetch produces a challenge
- **THEN** that sample SHALL have ok=false and SHALL NOT be converted or counted as a passed self-check

#### Scenario: selector-cannot-hide-challenge
- **WHEN** fetch or crawl uses a content selector that would remove challenge markers
- **THEN** admission SHALL evaluate the original HTML before selection and prevent successful publication of rejected content

#### Scenario: cached-challenge-resume
- **WHEN** a legacy HTML cache entry or resumed conversion corresponds to challenge HTML
- **THEN** the consumer SHALL reject it before resume or conversion success and SHALL exclude stale successful output from current assembly
- **AND** the diagnostic cache file SHALL NOT be automatically deleted

#### Scenario: normal-cross-path-equivalence
- **WHEN** the same admitted normal HTML is supplied through probe, sample and production boundaries
- **THEN** all boundaries SHALL agree on admission and preserve existing extraction/selector behavior
