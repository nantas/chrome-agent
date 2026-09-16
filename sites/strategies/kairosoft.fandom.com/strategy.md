---
samples:
- page: Structures (Mega Mall Story)
  label: mechanic_table sample (target page)
- page: Mega Mall Story
  label: game_main sample (Infobox game)
- page: Combos (Mega Mall Story)
  label: mechanic_table sample (medium)
domain: kairosoft.fandom.com
description: Fandom-hosted MediaWiki 1.43.9 multi-game wiki for Kairosoft titles.
  Cloudflare Managed Challenge on HTML pages; MediaWiki API endpoints are unaffected.
  Crawl scope is single-game — Mega Mall Story mechanics tables (10 ns=0 pages named
  '<Mechanic> (Mega Mall Story)').
protection_level: high
anti_crawl_refs:
- default
- rate-limit-api
structure:
  pages:
  - id: game_main_page
    label: Game Main Page
    url_pattern: /wiki/Mega_Mall_Story
    url_example: https://kairosoft.fandom.com/wiki/Mega_Mall_Story
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  - id: mechanic_table_page
    label: Mechanics Table Page
    url_pattern: /wiki/<MECHANIC>_(Mega_Mall_Story)
    url_example: https://kairosoft.fandom.com/wiki/Structures_(Mega_Mall_Story)
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  entry_points:
  - game_main_page
  - mechanic_table_page
api:
  platform: mediawiki
  base_url: https://kairosoft.fandom.com/api.php
  capabilities:
  - page_list
  - category_lookup
  - html_parse
  - wikitext_parse
  - imageinfo_query
  namespaces:
  - 0
  content_profile:
    discovery_strategy: category_members
    content_acquisition: html_rendered
    link_resolver: short_name_with_cross_namespace
    template_processor: simple_substitution
    list_page_assembler: frontmatter_driven
  platform_variant: fandom
  page_type_map:
    summary_pages:
    - Mega Mall Story
    entity_pages:
      mega_mall_story_category: Category:Mega Mall Story
  taxonomy:
    page_categories:
      Mega Mall Story: Mega Mall Story
    category_filters:
    - Article stubs
    - Banners
    - Game icons
    - Template documentation
    - Navigation templates
    - Noindexed pages
    - Manuals
    - Games
    - Android games
    - IOS games
  filename:
    replacements:
      /: _
      ':': _
      ' ': _
      (: ''
      ): ''
  rate_limit:
    tier: strict
    batch_delay_ms: 500
    retry:
      max_retries: 3
      backoff_multiplier: 2.0
  output:
    link_format: markdown_relative
    frontmatter_fields:
    - title
    - categories
    - sections
    - has_infobox
    template_map: {}
extraction:
  infobox:
    enabled: true
  selectors:
    title: '#firstHeading'
    body: .mw-parser-output
  image_handling:
    attribute: src
    lazyload_fallback: data-src
    output_format: markdown_inline
    keep_inline_in:
    - td
    - th
    - span
    - a
    - div
    - p
    - li
    base_url: https://kairosoft.fandom.com
  cleanup:
  - strip_edit_links
  - strip_fandom_infobox_tables
  - convert_ambox_to_text
  - unwrap_image_wrappers
  cleanup_selectors:
  - .mw-editsection
  - .toc
  - '#toc'
  - .hatnote
  lazyload:
    enabled: true
    placeholder_pattern: data:image/
    real_src_attr: data-src
  text_normalization:
  - fix_spaces
  - normalize_blank_lines
lifecycle:
  status: frozen
  review_evidence:
    samples: 3
    self_check: 'S1-S12: 29/30 pass, 1 known issue (KI-1 decorative images, accepted
      2026-09-15)'
    architecture_gate: pass
    regression: touhou-mystias-izakaya 5 samples 0 failures after checker fixes
    sample_pages:
    - Structures (Mega Mall Story)
    - Mega Mall Story
    - Combos (Mega Mall Story)
---

## Overview

kairosoft.fandom.com is a Fandom-hosted MediaWiki 1.43.9 multi-game wiki covering all Kairosoft titles (~40 games, 1,119 ns=0 articles total).

Critical infrastructure note: **HTML pages are protected by Cloudflare Managed Challenge**, returning `"Just a moment..."` to non-browser clients. **MediaWiki API endpoints (`/api.php`) are completely unaffected**. Acquisition path is **MediaWiki API-first** (`action=parse`).

## Crawl Scope (user-confirmed)

Single game: **Mega Mall Story** only. The game category holds exactly 10 ns=0 pages — mechanic table pages named `<Mechanic> (Mega Mall Story)` plus the game main page. File pages (93, ns=6) and translation page (ns=112) are excluded via `namespaces: [0]`.

| Page | Content |
|------|---------|
| Mega Mall Story | main page, Infobox game, section index |
| Structures (Mega Mall Story) | large table: Types/Facilities/Stores/Special (20KB wikitext) |
| Combos (Mega Mall Story) | combo table |
| Customers (Mega Mall Story) | customer table |
| Staff (Mega Mall Story) | staff table |
| Investments / Floor compatibility / Endgame / Tips / Bugs and cheats | mechanics tables |

Images: not downloaded; URLs preserved inline in Markdown (user decision).

## Content Model

Unlike single-game wikis (e.g. neonabyss / touhou-mystias-izakaya) with hundreds of small entity pages, this wiki stores each game's data in **few large table pages**. No per-entity infobox pages exist; the only portable infobox is `Infobox game` on the game main page.

## Protection & Engine Selection

| Layer | Status | Recommended Engine |
|-------|--------|-------------------|
| HTML (`/wiki/*`) | Cloudflare Managed Challenge | `cloakbrowser-fetch` fallback only |
| API (`/api.php`) | Unrestricted | Direct HTTP / `scrapling-get` |

## Discovery Flow

1. `action=query&list=categorymembers&cmtitle=Category:Mega Mall Story&cmnamespace=0` → 10 pages
2. Redirect resolution: `action=query&titles=...&redirects=1`

Estimated crawl set: 10 pages.

## Content Acquisition

`action=parse&page=TITLE&prop=text|wikitext|sections|displaytitle|categories&redirects=true`

## Output Structure

```
mega-mall-story/
├── Mega_Mall_Story.md
├── Structures_Mega_Mall_Story.md
├── Combos_Mega_Mall_Story.md
└── ... (7 more mechanic pages)
```

## Known Issues

- **KI-1 (S1 cosmetic)**: game main page HTML carries ~26 `<img>` tags but only ~15 are content-bearing; the delta is the infobox wds-tabber banner (2nd+ tabs), tiny platform logos embedded in pi-data-labels, and `data:` lazyload placeholders counted by the checker. Zero content images lost — verified by container-level audit 2026-09-15. Status: accepted (wontfix).
- Multi-game wiki: category taxonomy must stay scoped to the confirmed game
- Parenthesized filenames need normalization (see `filename.replacements`)

## Evidence

- Siteinfo: API `meta=siteinfo` — MediaWiki 1.43.9, pages 47450, articles 1119 — validated 2026-09-15
- API unrestricted: `curl /api.php?action=query&list=allcategories` returns 200 JSON — validated 2026-09-15
- HTML challenge: `scrapling-get` returns "Just a moment..." (6054 bytes) — validated 2026-09-15 (explore probe)
- Category members: `Category:Mega Mall Story` → ns0=10, ns6=93 (files), ns112=1 — validated 2026-09-15
- Page structure: Structures (Mega Mall Story) → sections Types/Facilities/Stores/Special, wikitext 20691 chars, no entity infobox templates — validated 2026-09-15
- Game main page: `Infobox game` template + Main navigation template — validated 2026-09-15
