---
domain: docs.gameanalytics.com
description: GameAnalytics official documentation — Docusaurus v3.10.1 static site covering SDK integration, event tracking, product features (analytics-iq / pipeline-iq / segment-iq), and settings
protection_level: low
anti_crawl_refs:
  - default
structure:
  pages:
    - id: home
      label: Homepage
      type: static_article
      content_type: documentation_hub
      pagination: none
      requires_auth: false
      url_example: https://docs.gameanalytics.com/
      page_pattern:
        - "exact:https://docs.gameanalytics.com/"
      links_to:
        - target: doc_page
          selector: "nav a, .navbar__link, .menu__link, a.pagination-nav__link"
    - id: doc_page
      label: Documentation Page
      type: static_article
      content_type: documentation_section
      pagination: none
      requires_auth: false
      page_pattern:
        - "regex:^https://docs\\.gameanalytics\\.com/.+"
      links_to:
        - target: doc_page
          selector: ".theme-doc-sidebar-menu a.menu__link, a.pagination-nav__link, a.table-of-contents__link, nav.pagination-nav a"
  entry_points:
    - home
    - doc_page
discovery:
  method: sitemap

extraction:
  engine: scrapling-get
  reason: "Docusaurus SSG renders full HTML server-side; scrapling-get retrieves complete article content without browser rendering"
  selectors:
    content: "div.theme-doc-markdown"
    title: "article header h1, h1"
    nav: ".theme-doc-sidebar-menu"
  cleanup:
    - "Remove .navbar, .footer, .theme-doc-toc-mobile, .breadcrumbs, .mcp-install-dropdown"
    - "Remove HubSpot/GTM <script> and <noscript> blocks"
    - "Remove .tocCollapsible mobile TOC buttons"
  text_normalization:
    - "Collapse 3+ blank lines to 2"
    - "Trim trailing whitespace per line"
  notes: |
    Site: Docusaurus v3.10.1 (static site generator). No robots.txt restriction,
    no anti-crawl protection. sitemap.xml exposes 193 URLs deterministically.
    Main content lives in div.theme-doc-markdown.markdown (contains <header><h1>
    then <p>/<div class="theme-admonition">/<pre><code>/tables). scrapling --ai-targeted
    extraction handles the conversion generically.
samples:
  - page: "event-tracking-and-integrations/sdks-and-collection-api/game-engine-sdks/unity"
    label: "Unity SDK setup page — code-block heavy, admonitions"
  - page: "products-and-features/pipeline-iq/data-warehouse/datasets-and-schemas/event-schemas"
    label: "Event schemas page — tables + structured fields"
  - page: "events-metrics-and-filtering/event-types/business-events"
    label: "Business events — prose + lists"
  - page: "event-tracking-and-integrations/sdks-and-collection-api/api/event-types"
    label: "Collection API event types — mixed code + tables"
  - page: "getting-started/plan-your-sdk-implementation"
    label: "Getting started planning page — prose-heavy"
---

# docs.gameanalytics.com Strategy

## Platform Notes

- **Tech**: Docusaurus v3.10.1 SSG (server-side rendered HTML, no JS required for content)
- **Protection**: none (verified via explore scrapling-get probe, HTTP 200)
- **Discovery**: sitemap.xml (193 URLs) — deterministic, no crawling heuristics needed
- **Content selector**: `div.theme-doc-markdown` holds the full article body (header H1 + prose + code + tables)

## Extraction Rules

- scrapling-get retrieves raw HTML; `--ai-targeted` mode performs main-content extraction
- Content container: `div.theme-doc-markdown`
- Title: first `<h1>` inside `article > header`
- Code blocks: `<pre><code>` preserved with language class → fenced code blocks
- Admonitions: `div.theme-admonition` → blockquote-style callouts
- Internal links: rewrite to relative paths under the mirror root

## Page Taxonomy (192 doc pages)

| Top-level category | Pages | Notes |
|--------------------|-------|-------|
| event-tracking-and-integrations/ | 116 | SDK + integrations core (largest) |
| events-metrics-and-filtering/ | 9 | Event types + metrics reference |
| getting-started/ | 2 | Onboarding |
| products-and-features/ | 61 | analytics-iq / pipeline-iq / segment-iq |
| settings-and-billing/ | 3 | Account/billing |
| (root homepage) | 1 | What is GameAnalytics? |

## Known Issues

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| (none yet) | | | | | | |
