---
domain: wiki.supercombo.gg
description: Fighting game wiki pages with Cloudflare Turnstile protection
protection_level: high
anti_crawl_refs:
  - cloudflare-turnstile
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

1. Use Scrapling `stealthy-fetch` with `solve_cloudflare: true` as the primary engine.
2. The stealthy fetcher's browser fingerprint spoofing and Cloudflare challenge solver handle the Turnstile challenge.
3. After challenge bypass, extract article content from the rendered page.
4. For diagnostic needs (when stealthy-fetch fails), escalate to `chrome-devtools-mcp`.

## Known Issues

- Earlier managed-browser runs (2026-03-21) were blocked by Cloudflare and never reached article content.
- Scrapling `stealthy-fetch` with `--solve-cloudflare` successfully solved the Turnstile challenge and reached article content.
- The Cloudflare challenge details are in `sites/anti-crawl/cloudflare-turnstile.md`.

## Evidence

- Validated on `wiki.supercombo.gg/w/Street_Fighter_6`.
- Scrapling smoke check confirmed `stealthy-fetch` with `solve_cloudflare` works.
- Reports: `reports/2026-03-21-sf6-supercombo-challenge-signals.txt`.
