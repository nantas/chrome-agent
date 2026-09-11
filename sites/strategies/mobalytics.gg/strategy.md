---
domain: mobalytics.gg
description: PoE2/game build guide pages on mobalytics.gg (Cloudflare-managed protection)
protection_level: high
anti_crawl_refs:
  - cloudflare-managed
engine_preference:
  preferred: cloakbrowser-fetch
structure:
  pages:
    - id: poe2_build_guide
      label: PoE2 Build Guide
      url_pattern: /poe-2/builds/:slug
      url_example: https://mobalytics.gg/poe-2/builds/twister-spirit-walker-snoobae
      type: dynamic_content
      content_type: article_body
      pagination: none
      links_to: []
      requires_auth: false
  entry_points:
    - poe2_build_guide
extraction:
  engine: cloakbrowser-fetch
  selectors:
    content: body
    title: title
  cleanup: []
  text_normalization: []
---

# mobalytics.gg Strategy

## Platform Notes

mobalytics.gg hosts game build guides (PoE2 and others). Pages are SPA-like with Cloudflare-managed protection. Variant tabs, equipment cards, skill gem links, and How it Plays/Works sections are client-rendered after challenge bypass.

## Extraction Flow

1. Use `cloakbrowser-fetch` as the primary engine (Cloudflare managed challenge).
2. Wait for full page render after challenge resolution — equipment/skill/variant content is dynamic.
3. Do not use scrapling-get: it returns 403 or empty content, or the Cloudflare interstitial ("Just a moment...").

## Known Issues

- 2026-08-14: scrapling-get returned HTTP 403 with empty content.md while CLI still reported success.
- 2026-08-14: explore probe treated Cloudflare interstitial (title "Just a moment...", ~6KB) as success and did not auto-escalate the probe chain.
- jina reader can get partial text but loses variant-specific gear, dynamic How it Plays/Works sections, and item affix values.

## Evidence

- Target: https://mobalytics.gg/poe-2/builds/twister-spirit-walker-snoobae
- Explore discovery: protection=cloudflare-managed, engine_override=cloakbrowser-fetch
