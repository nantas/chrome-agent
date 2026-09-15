---
samples:
- page: Agony Oden
  label: entity_cuisine sample
- page: Bamboo
  label: entity_ingredient sample
- page: Akatsuki
  label: entity_beverage sample
- page: Alice
  label: entity_rare_customer sample
- page: Tags
  label: gameplay_article sample
domain: touhou-mystias-izakaya.fandom.com
description: Fandom-hosted MediaWiki 1.43.9 game wiki for Touhou Mystia's Izakaya.
  Cloudflare Managed Challenge on HTML pages; MediaWiki API endpoints are unaffected.
  Highly templated entity pages (InfoboxCuisine/InfoboxIngredient/InfoboxBeverage/InfoboxRareCustomer)
  plus gameplay mechanic articles.
protection_level: high
anti_crawl_refs:
- default
- rate-limit-api
structure:
  pages:
  - id: wiki_main_page
    label: Wiki Main Page
    url_pattern: /wiki/Touhou_Mystia%27s_Izakaya_Wiki
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Touhou_Mystia%27s_Izakaya_Wiki
    type: static_article
    content_type: wiki_main_page
    pagination: none
    requires_auth: false
  - id: summary_cuisines
    label: Cuisines Summary Page
    url_pattern: /wiki/Cuisines
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Cuisines
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: summary_ingredients
    label: Ingredients Summary Page
    url_pattern: /wiki/Ingredients
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Ingredients
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: summary_beverages
    label: Beverages Summary Page
    url_pattern: /wiki/Beverages
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Beverages
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: entity_cuisine
    label: Individual Cuisine Page
    url_pattern: /wiki/CUISINE_NAME
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Agony_Oden
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  - id: entity_ingredient
    label: Individual Ingredient Page
    url_pattern: /wiki/INGREDIENT_NAME
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Bamboo
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  - id: entity_beverage
    label: Individual Beverage Page
    url_pattern: /wiki/BEVERAGE_NAME
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Akatsuki
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  - id: entity_rare_customer
    label: Individual Rare Customer Page
    url_pattern: /wiki/CHARACTER_NAME
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Alice
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  - id: gameplay_article
    label: Gameplay Mechanic Article
    url_pattern: /wiki/MECHANIC_NAME
    url_example: https://touhou-mystias-izakaya.fandom.com/wiki/Tags
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  entry_points:
  - wiki_main_page
  - summary_cuisines
  - summary_ingredients
  - summary_beverages
api:
  platform: mediawiki
  base_url: https://touhou-mystias-izakaya.fandom.com/api.php
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
    template_processor: fandom_infobox
    list_page_assembler: hybrid_frontmatter_and_rendered
  platform_variant: fandom
  page_type_map:
    summary_pages:
    - Cuisines
    - Ingredients
    - Beverages
    entity_pages:
      cuisines_category: Category:Cuisines
      ingredients_category: Category:Ingredients
      beverages_category: Category:Beverages
      rare_customers_category: Category:Rare Customers
  taxonomy:
    page_categories:
      Cuisines: Cuisines
      Ingredients: Ingredients
      Beverages: Beverages
      Rare Customers: Rare Customers
      Gameplay: Gameplay
    category_filters:
    - Candidates for deletion
    - Disambiguation
    - Hidden categories
    - Template documentation
    - Documentation templates
    - General wiki templates
    - Beverage Icons
    - Cuisine Icons
    - Base Game
    - DLC1
    - DLC2
    - DLC2.5
    - DLC3
    - DLC4
    - DLC5
  filename:
    replacements:
      /: _
      ':': _
      ' ': _
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
    template_map:
      InfoboxCuisine: ''
      InfoboxIngredient: ''
      InfoboxBeverage: ''
      InfoboxRareCustomer: ''
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
    base_url: https://touhou-mystias-izakaya.fandom.com
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
    samples: 5
    self_check: S1-S12 pass 60/60, 0 failures (2026-09-15, 3rd iteration after converter
      fixes)
    architecture_gate: pass
    sample_pages:
    - Agony Oden
    - Bamboo
    - Akatsuki
    - Alice
    - Tags
---

## Overview

touhou-mystias-izakaya.fandom.com is a Fandom-hosted MediaWiki 1.43.9 wiki for *Touhou Mystia's Izakaya* (东方夜雀食堂), a cooking/izakaya management game set in Gensokyo.

Critical infrastructure note: **HTML pages are protected by Cloudflare Managed Challenge**, returning a `"Just a moment..."` interstitial to non-browser clients. However, **MediaWiki API endpoints (`/api.php`) are completely unaffected** and return valid JSON without any challenge. The acquisition path is therefore **MediaWiki API-first** (`action=parse`).

## Site Scale

| Metric | Value |
|--------|-------|
| Total pages | 1,626 |
| Articles (ns=0) | 397 |
| Images | 881 |
| Edits | 6,128 |
| Categories | 88 |

## Content Model

Content is organized by entity type across Base Game + DLC1–5. Scope (user-confirmed): core content categories only.

| Category | Pages | Infobox template | Typical sections |
|----------|-------|------------------|------------------|
| Cuisines | 163 | `InfoboxCuisine` | Info, How to Unlock, Cooking |
| Ingredients | 63 | `InfoboxIngredient` | Info, How to Obtain, Merchants, Gathering, Usage |
| Beverages | 47 | `InfoboxBeverage` | Info, How to Obtain, Merchants, Gathering, Trivia |
| Rare Customers | 46 | `InfoboxRareCustomer` | Descriptions, Bond Lv1/3/5, Tag Requests, Spell Cards |
| Gameplay | 9 | (none) | e.g. Tags: Cuisine Tags, Beverage Tags |

Summary/list pages exist (`Cuisines`, `Ingredients`, `Beverages`) and appear inside their own category members.

### Excluded (per user decision)

- Icon file categories (Beverage Icons, Cuisine Icons, ~150+ file pages)
- Template documentation categories
- Maintenance categories (Candidates for deletion, Disambiguation)
- Cross-content umbrella categories (Base Game, DLC1–5) — members duplicate entity categories
- Location categories (Bamboo Forest of the Lost, Forest of Magic, etc.) — outside confirmed scope
- Images: not downloaded (URLs preserved inline in Markdown)

## Protection & Engine Selection

| Layer | Status | Recommended Engine |
|-------|--------|-------------------|
| HTML (`/wiki/*`) | Cloudflare Managed Challenge ("Just a moment...") | `cloakbrowser-fetch` fallback only |
| API (`/api.php`) | Unrestricted | Direct HTTP / `scrapling-get` |

**Engine priority**:
1. MediaWiki API direct (`action=query`, `action=parse`) — primary
2. `cloakbrowser-fetch` — HTML fallback only if API insufficient

## Discovery Flow

1. Category-based discovery: `action=query&list=categorymembers&cmtitle=Category:{Cuisines|Ingredients|Beverages|Rare Customers|Gameplay}&cmnamespace=0`
2. Filter out `/tr`, `/zh` etc. translation suffixes and non-ns0 pages
3. Redirect resolution: `action=query&titles=...&redirects=1`

Estimated crawl set: ~328 pages (163+63+47+46+9).

## Content Acquisition

`action=parse&page=TITLE&prop=text|wikitext|sections|displaytitle|categories&redirects=true`

- `text`: rendered HTML (primary conversion input)
- `wikitext`: infobox template extraction
- `categories`: page classification
- `sections`: section structure for frontmatter

## Extraction & Conversion Rules

- Fandom infobox tables (`item-table-*` classes): strip from HTML; structured data from wikitext templates
- ambox notices: convert to ⚠️ paragraph
- TOC / edit links / hatnotes: strip
- Internal links: known pages → relative `.md` links; unknown → external wiki URL
- Images: preserve `static.wikia.nocookie.net` URLs inline (lazyload `data-src` unwrap); no download

## Output Structure

```
cuisines/ ingredients/ beverages/ rare-customers/ gameplay/ + summary pages
```

## Known Issues

- Cloudflare on HTML pages: bypassed entirely via API path
- Translation subpages may appear in category members — filter by suffix
- DLC umbrella categories overlap entity categories — use entity categories only

## Evidence

- Siteinfo: API `meta=siteinfo` — MediaWiki 1.43.9, pages 1626, articles 397 — validated 2026-09-15
- API unrestricted: `curl /api.php?action=query&list=allcategories` returns 200 JSON — validated 2026-09-15
- HTML challenge: `scrapling-get` to wiki main page returns "Just a moment..." (6073 bytes) — validated 2026-09-15 (explore probe)
- Infobox templates: Agony Oden→InfoboxCuisine, Bamboo→InfoboxIngredient, Akatsuki→InfoboxBeverage, Alice→InfoboxRareCustomer — validated via `action=parse&prop=wikitext` 2026-09-15
- Category members: Cuisines/Ingredients/Beverages/Rare Customers/Gameplay all return ns=0 members — validated 2026-09-15
