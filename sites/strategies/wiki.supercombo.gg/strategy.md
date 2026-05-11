---
domain: wiki.supercombo.gg
description: Fighting game wiki pages with Cloudflare Turnstile protection
protection_level: high
anti_crawl_refs:
  - cloudflare-turnstile
engine_preference:
  preferred: cloakbrowser-fetch
structure:
  pages:
    - id: wiki_article
      label: Wiki Article
      url_pattern: /w/:article
      url_example: https://wiki.supercombo.gg/w/Street_Fighter_6
      type: static_article
      content_type: article_body
      pagination: none
      links_to: []
      requires_auth: false
  entry_points:
    - wiki_article
extraction:
  image_handling:
    attribute: src
    output_format: markdown_inline
---

## Overview

wiki.supercombo.gg is a fighting game wiki with MediaWiki-based article pages. The site is protected by Cloudflare Turnstile, requiring anti-bot challenge bypass before content can be accessed.

## Page Structure

- Single page type: wiki article.
- Standard MediaWiki layout with article title, body content, and sidebar navigation.
- Pages are static HTML once past the Cloudflare challenge.

## Extraction Flow

1. Use `cloakbrowser-fetch` as the primary engine (wait until `domcontentloaded`, then allow up to 15s for Turnstile auto-resolution).
2. CloakBrowser's source-level fingerprint patches (57 C++ Chromium patches) handle the Turnstile challenge automatically in headless mode.
3. After challenge bypass, extract article content from the rendered page.
4. For diagnostic needs (when cloakbrowser-fetch fails), escalate to `chrome-devtools-mcp`.

## Known Issues

- Earlier managed-browser runs (2026-03-21) were blocked by Cloudflare and never reached article content.
- CloakBrowser (2026-05-11) auto-resolves the Turnstile challenge in 6–14s and returns full article content (~23,000 chars).
- The Cloudflare challenge details are in `sites/anti-crawl/cloudflare-turnstile.md`.
- `scrapling-stealthy-fetch` was previously used but is now superseded by `cloakbrowser-fetch`.

## Evidence

- Validated on `wiki.supercombo.gg/w/Street_Fighter_6`.
- CloakBrowser smoke check confirmed auto-resolution: title="SuperCombo Wiki", content=23,021 chars, total time=14.42s.
- Legacy reports (2026-03-21): `reports/2026-03-21-sf6-supercombo-challenge-signals.txt`.
