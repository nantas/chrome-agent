# CLI Domain: Workflows — Merged Spec

> **Merged from**: `scrapling-first-browser-workflow`, `strategy-guided-crawl`, `scrape-command`, `full-url-parameterization`
> **Purpose**: Defines the core CLI workflows: Scrapling-first routing, strategy-guided crawl (with Markdown output, phases, concurrency), strategy-free scrape, and full URL parameterization for links and images.

---

## Part 1 — Source: `scrapling-first-browser-workflow`

### Requirement: Scrapling-first routing

Scrapling is the first tool path for all webpage grabbing tasks: public content, dynamic pages, protected pages, batch, and read-only logged-in sessions.

#### Scenario: Public content request
- **WHEN** user asks to get content from a public URL
- **THEN** workflow starts with Scrapling before `chrome-devtools-mcp` or `chrome-cdp`

#### Scenario: Dynamic or protected page request
- **WHEN** page needs JS rendering, stealth, session continuity, or bot-blocking mitigation
- **THEN** workflow selects matching Scrapling fetcher/session before escalating

### Requirement: Default workflow ordering

Route (Content Retrieval vs Platform/Page Analysis) → Scrapling CLI preflight → Scrapling fetcher selection → fallback only on verified triggers.

### Requirement: Fallback boundaries

- `chrome-devtools-mcp` for diagnostic evidence (DOM, accessibility, network, screenshots)
- `chrome-cdp` for live-session continuity
- Choose by diagnostic vs session continuity needs, NOT by tool duplication

### Requirement: Authenticated read-only boundary

Explicit user approval required. Read-only by default. Session reuse failure → record and stop. Redirect to login → stop and record failure.

### Requirement: Environment contract

`SCRAPLING_CLI_PATH` as canonical reference. No host-specific absolute paths in git-tracked files.

### Requirement: Verification baseline

Covers: static public page, dynamic page, article with images, protected page attempt. Logged-in experiments deferred without explicit approval.

---

## Part 2 — Source: `strategy-guided-crawl`

### Requirement: Default Markdown output

`crawl` defaults to Markdown output. Each page produces `.md` file via `scrapling extract`. Intermediate `.html` cleaned up after conversion.

### Requirement: Optional merged output

`--merge` → concatenate all `.md` files into `crawl-output.md` with table of contents.

### Requirement: Concurrent Markdown conversion

Default concurrency: 5. Custom: `--concurrency N`.

### Requirement: Phase 2 partial failure semantics

Phase 1 success + Phase 2 failures → `partial_success`. Failed URLs in `phase2.failed_urls`. Successful `.md` files remain.

### Requirement: Phase-based execution

Public crawl SHALL route MediaWiki `--discovery-only` and the compatibility alias `--phase discover` to explore page enumeration. For MediaWiki, `fetch`, `convert`, `assemble`, and extraction `all` SHALL consume an accepted manifest via pipeline; `convert` remains cache-only conversion followed by the existing assembly behavior. Without a manifest, a crawl requesting all SHALL perform discovery and stop at confirmation, unless `--yes` explicitly authorizes continuing a complete successful discovered scope. Scrapling's supported fetch/convert/assemble behavior SHALL remain unchanged. Incompatible options SHALL be rejected rather than silently prioritized.

#### Scenario: discovery-only-stops
- **WHEN** public MediaWiki crawl uses discovery-only, including with --yes
- **THEN** it SHALL return manifest/summary without正文 extraction, conversion or assembly and SHALL NOT spawn pipeline --phase discover.

#### Scenario: discovery-phase-alias
- **WHEN** public MediaWiki crawl uses --phase discover
- **THEN** it SHALL behave as discovery-only through explore rather than sending discover to pipeline.

#### Scenario: full-crawl-confirmation
- **WHEN** a manifest-free crawl completes discovery without --yes
- **THEN** it SHALL return confirmation-required discovery artifacts and SHALL NOT extract until the caller confirms and resumes with --from-manifest.

#### Scenario: conflicting-modes
- **WHEN** discovery-only is combined with --from-manifest or an extraction phase
- **THEN** the command SHALL return structured invalid arguments before performing work.

### Requirement: unified-cli-phase-semantics

`--phase convert` = read cache → convert → output Markdown (consistent across both paths).

### Requirement: keep-html-semantics (deprecated)

`--keep-html` deprecated. HTML persisted via `--phase fetch` cache. Warning emitted but not blocking.

### Requirement: no-markdown-alignment

`--no-markdown` skips conversion. Suggests `--phase fetch` as recommended HTML-only workflow.

---

## Part 3 — Source: `scrape-command`

### Requirement: Scrape command surface

`chrome-agent scrape <url>` — strategy-free recursive crawling.

### Requirement: No strategy dependency

`scrape` proceeds without site-strategy. If strategy exists, it is ignored.

### Requirement: Self-discovered link traversal

- Same-domain filtering (default `--same-domain`)
- `--match <glob>` for URL pattern filtering
- Dedup and cycle prevention

### Requirement: Bounded traversal

`--max-pages` (default 10).

### Requirement: Default Markdown output

Each page produces `.md` file. `--no-markdown` retains `.html`.

### Requirement: Structured directory output

Output reflects URL pathname hierarchy. Internal links rewritten as relative paths.

### Requirement: Optional merged output

`--merge` → `scrape-output.md` with table of contents.

### Requirement: Concurrent Markdown conversion

Default: 5. Custom: `--concurrency N`.

### Requirement: Fetcher override

`--fetcher <name>` (default: `scrapling-get`).

### Requirement: Partial failure semantics

Phase 1 or Phase 2 partial failure → `partial_success`. Failed URLs recorded in manifest.

### Requirement: HTML intermediate cleanup

`.html` files cleaned after Phase 2. `--keep-html` retains them as `disposable` artifacts.

---

## Part 4 — Source: `full-url-parameterization`

### Requirement: convert-internal-links-to-full-urls

`convert_links_to_md(html: str, wiki_domain: str) -> str` converts:
- `/wiki/*` → `https://{wiki_domain}/wiki/*`
- `/images/*` → `https://{wiki_domain}/images/*`
- Any `/...` → `https://{wiki_domain}/...`
- Preserves external URLs and anchor-only links
- Strips `javascript:` links to text only
- `wiki_domain` is REQUIRED (no default — raises TypeError if missing)

### Requirement: convert-internal-images-to-full-urls

`convert_images_to_md(html: str, wiki_domain: str, skip_patterns: list[str] = []) -> str` converts:
- `/images/*` src → `https://{wiki_domain}/images/*`
- `skip_patterns` — regex patterns; matching images excluded
- External images preserved unchanged

### Requirement: base-url-from-strategy

`wiki_domain` extracted from strategy `domain` field or `api.base_url`. Passed to converter functions.

### Requirement: manifest-input-compatibility

The public CLI and pipeline SHALL validate manifest shape and identity before API probing. New schema version 2 manifests SHALL validate required fields/domain/fingerprint and list eligibility. An absent schema_version SHALL select the legacy adapter; any declared version other than 2 SHALL be rejected as unsupported, not guessed as legacy. Legacy manifests without a version MAY be adapted in memory only when each row already has valid title/ns/target paths and list identity is unambiguous: exact configured title plus matching configured directory permits deriving is_list_page=true; a row not matching any list title permits false. Ambiguous aliases, conflicting directories, missing required row fields or mismatched target domain SHALL return a structured manifest-contract error with field paths and remediation. Detached legacy list content SHALL be ignored with an explicit absent-page reason, never adding pages. Existing target paths, including empty root directories, SHALL be preserved for legacy input; this change SHALL NOT migrate historical files or rewrite source manifests.

#### Scenario: unambiguous-legacy-input
- **WHEN** a versionless manifest has valid paths and exact unambiguous list-page matches
- **THEN** the command SHALL derive only missing eligibility metadata in memory, report legacy adaptation, and preserve source bytes, page membership and target paths.

#### Scenario: ambiguous-legacy-list
- **WHEN** a legacy list identity requires guessing an alias or conflicts with its directory
- **THEN** the command SHALL fail with field-specific diagnostics without fetching, rediscovering, or modifying the input.

#### Scenario: detached-legacy-content
- **WHEN** legacy list_page_content contains a title absent from pages
- **THEN** the command SHALL report that content as skipped and SHALL NOT expand confirmed scope.

#### Scenario: incompatible-v2-input
- **WHEN** required version 2 fields are missing or domain/fingerprint conflicts with the active strategy
- **THEN** validation SHALL reject the input with a manifest-contract diagnostic before probing.

### Requirement: mediawiki-error-and-fallback-semantics

MediaWiki subprocess results SHALL distinguish success, partial success, explicit contract/config/internal failures, external network failures, and spawn/timeout/signal failures. A null process status SHALL never be mapped to partial success. Contract/configuration/invalid-arguments/internal failures SHALL stop via the existing internalFailure/handoff envelope. Any allowed external fallback SHALL preserve discovery-only or accepted-manifest page/path semantics; if the target backend cannot do so the CLI SHALL return failure without fallback. Result metadata SHALL preserve upstream backend, exit code or null, process error/signal, stderr summary, requested mode and fallback decision/reason, including when fallback succeeds.

#### Scenario: invalid-arguments-do-not-fallback
- **WHEN** pipeline exits 20 or rejects strategy/manifest configuration
- **THEN** public crawl SHALL fail with original diagnostics and internal handoff without invoking Scrapling.

#### Scenario: failed-spawn-is-not-partial
- **WHEN** spawn returns status null, an error, a timeout or a signal
- **THEN** public crawl SHALL report the actual failure and SHALL NOT return partial_success merely from null coalescing.

#### Scenario: unsupported-fallback-contract
- **WHEN** an external API failure occurs during discovery-only or API manifest extraction and the proposed fallback cannot preserve the requested contract
- **THEN** the command SHALL stop with original upstream evidence and a fallback-not-compatible reason; it SHALL NOT crawl the homepage or reinterpret pages as visited URLs.

#### Scenario: compatible-fallback-retains-upstream
- **WHEN** a supported fallback is deliberately selected for an external failure
- **THEN** its final result SHALL include original failure context and preserve the approved page scope and output paths.
