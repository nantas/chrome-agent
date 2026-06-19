---
domain: posthog.com
description: PostHog Docs — Gatsby 4.25.9 static docs site covering product analytics, session replay, feature flags, experiments, data warehouse, CDP, error tracking, and SDK references. Sitemap-index driven discovery with /docs/references/** excluded.
protection_level: low
anti_crawl_refs:
  - default
structure:
  pages:
    - id: doc_page
      label: Documentation Page
      type: static_article
      content_type: documentation_section
      pagination: none
      requires_auth: false
      url_example: https://posthog.com/docs/getting-started/install
      page_pattern:
        # Matches the /docs landing page AND every /docs/<...> subpath.
        - "regex:^https://posthog\\.com/docs(/.*)?$"
  entry_points:
    - doc_page
discovery:
  method: sitemap
  # Points at the sitemap INDEX so the sitemap-index resolution pipeline is
  # exercised end-to-end (design D6 explicitly sanctions this). The index
  # lists one child sitemap (sitemap-0.xml) holding ~14.5k URLs.
  sitemap_url: "https://posthog.com/sitemap/sitemap-index.xml"
  # Drop auto-generated SDK reference pages (thousands of versioned duplicates)
  # AFTER the page_pattern include stage. Glob: ** matches any path tail.
  exclude_patterns:
    - "exact:/docs/references/**"

extraction:
  engine: scrapling-get
  reason: "Gatsby 4.25.9 SSG renders full HTML server-side; scrapling-get retrieves the complete page without browser rendering. NOTE: PostHog redesigned the docs template (no more <article> wrapper) — main content now lives in <div class='reader-content-container'>. The pipeline must pass this selector via scrapling -s; --ai-targeted alone mis-extracts the nav bar (see KI-1)."
  mode: css-selector
  selectors:
    content: "div[class*='@container/reader-content']"
    title: "article h1, h1"
  cleanup:
    - "Remove site header/footer, left navigation sidebar, and right-side table-of-contents"
    - "Remove decorative banners and on-page call-to-action cards"
  text_normalization:
    - "Collapse 3+ blank lines to 2"
    - "Trim trailing whitespace per line"
  notes: |
    Site: Gatsby 4.25.9 (static site generator) + Tailwind CSS. The proposal
    originally assumed Docusaurus; live probe confirms Gatsby. No robots.txt
    restriction on /docs, no anti-crawl protection (HTTP 200 on plain GET).
    Main content lives in <article class="... prose dark:prose-invert ...">.
    The sitemap-0.xml child exposes ~14,576 URLs: 5,668 under /docs, of which
    3,943 are /docs/references/** (auto-generated SDK API references, mostly
    versioned duplicates of posthog-js). exclude_patterns removes those,
    leaving ~1,725 documentation pages for crawl.
samples:
  - page: "docs/getting-started/install"
    note: "redirected from /docs/getting-started/start-here via HTTP 308"
    label: "Getting started — prose + callouts"
  - page: "docs/feature-flags"
    label: "Feature flags category hub — link lists"
  - page: "docs/data-warehouse"
    label: "Data warehouse — mixed prose + SQL code blocks"
  - page: "docs/experiments"
    label: "Experiments — prose + configuration tables"
  - page: "docs/cdp"
    label: "CDP — pipeline + event reference"
---

# posthog.com Strategy

## Platform Notes

- **Tech**: Gatsby 4.25.9 SSG (`<meta name="generator" content="Gatsby 4.25.9">`) + Tailwind CSS — content is server-side rendered, no JS needed for the article body
- **Protection**: none (verified via plain GET probe, HTTP 200)
- **Discovery**: sitemap **index** at `https://posthog.com/sitemap/sitemap-index.xml` → single child `sitemap-0.xml` (~14,576 URLs). The sitemap-index resolution capability is what makes this site reachable.
- **Exclude**: `/docs/references/**` removed post-include (3,943 auto-generated SDK reference pages — mostly versioned `posthog-js-*` duplicates)
- **Content selector**: `<div class="@container/reader-content ...">` wraps both the page `<h1>` and the inner `<div class="reader-content-container">` body. Using the outer wrapper (matched via `div[class*='@container/reader-content']`) captures the title AND body in one shot — verified across all 5 samples (PostHog redesigned the docs template; the legacy `<article class="prose">` wrapper no longer exists as of 2026-06).

## Extraction Rules

- scrapling-get retrieves raw HTML; the strategy-sourced CSS selector `div[class*='@container/reader-content']` is passed via scrapling `-s` to extract the main content (h1 + body) precisely
- ✅ **Pipeline gap (KI-1) RESOLVED** (change `strategy-selector-passthrough`, 2026-06-19): `chrome-agent fetch` and `crawl` now read `extraction.selectors.content` via shared helper `buildScraplingExtractionArgs()` and pass it to scrapling `-s`. Native `chrome-agent fetch <url>` produces correct output (no manual `-s` needed). Fallback to `--ai-targeted` only when a strategy declares no content selector.
- Content container: `div[class*='@container/reader-content']` (outer wrapper; includes h1 + `div.reader-content-container` body)
- Title: first `<h1>` inside the `@container/reader-content` wrapper (now captured by the unified selector)
- Code blocks: `<pre><code>` with `prism-code` / `language-*` classes → fenced code blocks
- Internal links: rewrite to relative paths under the mirror root

## Discovery Shape (after include + exclude)

| Stage | URL count | Notes |
|-------|-----------|-------|
| sitemap-0.xml total | 14,576 | full child sitemap |
| page_pattern include (`/docs*`) | 5,668 | all docs URLs |
| exclude_patterns (`/docs/references/**`) | -3,943 | auto-generated SDK references |
| **final crawl scope** | **~1,725** | documentation pages |

## Top-level docs categories (representative)

`getting-started`, `feature-flags`, `experiments`, `session-replay`, `product-analytics`, `data-warehouse`, `cdp`, `error-tracking`, `ai-engineering`, `api`, `integrations`, `libraries`, `glossary`, and more.

## Known Issues

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| KI-1 | `chrome-agent fetch` hardcodes `--ai-targeted`, ignores `extraction.selectors`; ai-targeted mis-extracts PostHog nav bar (397B vs expected ~6KB+) | resolved | P1 | pipeline | (historical) All PostHog /docs fetches returned empty/nav-only content | **RESOLVED** by change `strategy-selector-passthrough` (2026-06-19): `runFetch()` + crawl paths now source `extraction.selectors.content` via shared helper `buildScraplingExtractionArgs()` → scrapling `-s`. E2E verified: `chrome-agent fetch docs/feature-flags` now yields 6106B (was 397B). See `openspec/changes/strategy-selector-passthrough/verification.md`. |
| KI-2 | Sample URL `docs/getting-started/start-here` 308-redirects to `docs/getting-started/install` | resolved | P3 | strategy | Stale sample URL produced confusing redirect in fetch logs | Updated sample[0].page to `docs/getting-started/install` with redirect note (2026-06-19) |
