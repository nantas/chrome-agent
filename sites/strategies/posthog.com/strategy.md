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
      url_example: https://posthog.com/docs/getting-started/start-here
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
  reason: "Gatsby 4.25.9 SSG renders full HTML server-side; scrapling-get retrieves the complete article without browser rendering. --ai-targeted performs generic main-content extraction robust against the Tailwind `prose` layout."
  mode: ai-targeted
  selectors:
    content: "article.prose, article.reader-view-content-container"
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
  - page: "docs/getting-started/start-here"
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
- **Content selector**: `<article class="... prose ...">` holds the docs body

## Extraction Rules

- scrapling-get retrieves raw HTML; `--ai-targeted` mode performs main-content extraction (Tailwind `prose` layout handled generically)
- Content container: `article.prose` / `article.reader-view-content-container`
- Title: first `<h1>` inside `<article>`
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
| (none yet) | | | | | | |
