---
samples:
  - page: Crops
    label: API regression sample (2026-09-10; existing cache for Bloody Gust)
domain: growagarden.fandom.com
description: "Fandom-hosted MediaWiki 1.43.9 wiki for Grow a Garden (Roblox farming/idle simulator). Cloudflare Managed Challenge on HTML pages; MediaWiki API endpoints are unaffected by the challenge but reject non-browser User-Agents. Category-driven content model with structured entity pages (Crops/Pets/Gears/Eggs) using infobox templates, plus a Game Features system-documentation family."
protection_level: high
anti_crawl_refs:
  - default
  - rate-limit-api
structure:
  pages:
    - id: wiki_main_page
      label: Grow a Garden Wiki Main Page
      url_pattern: /wiki/Grow_a_Garden_Wiki
      url_example: https://growagarden.fandom.com/wiki/Grow_a_Garden_Wiki
      type: static_article
      content_type: wiki_main_page
      pagination: none
      links_to:
        - target: summary_crops
          selector: .mw-parser-output a[href^="/wiki/"]
        - target: summary_pets
          selector: .mw-parser-output a[href^="/wiki/"]
        - target: summary_gears
          selector: .mw-parser-output a[href^="/wiki/"]
        - target: summary_events
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: summary_crops
      label: Crops Summary Page
      url_pattern: /wiki/Crops
      url_example: https://growagarden.fandom.com/wiki/Crops
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_crop
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: summary_pets
      label: Pets Summary Page
      url_pattern: /wiki/Pets
      url_example: https://growagarden.fandom.com/wiki/Pets
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_pet
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: summary_gears
      label: Gears Summary Page
      url_pattern: /wiki/Gears
      url_example: https://growagarden.fandom.com/wiki/Gears
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_gear
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: summary_eggs
      label: Eggs Summary Page
      url_pattern: /wiki/Eggs
      url_example: https://growagarden.fandom.com/wiki/Eggs
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_egg
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: summary_mechanics
      label: Mechanics / Game Features System Page
      url_pattern: /wiki/Mechanics
      url_example: https://growagarden.fandom.com/wiki/Mechanics
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_system
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: entity_crop
      label: Individual Crop Page
      url_pattern: /wiki/CROP_NAME
      url_example: https://growagarden.fandom.com/wiki/Apple
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_crop
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: entity_pet
      label: Individual Pet Page
      url_pattern: /wiki/PET_NAME
      url_example: https://growagarden.fandom.com/wiki/Bee
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_pet
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
    - id: entity_gear
      label: Individual Gear Page
      url_pattern: /wiki/GEAR_NAME
      url_example: https://growagarden.fandom.com/wiki/Sprinklers
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_gear
          selector: .mw-parser-output a[href^="/wiki/"]
      requires_auth: false
  entry_points:
    - wiki_main_page
    - summary_crops
    - summary_pets
    - summary_gears
    - summary_eggs
    - summary_mechanics
api:
  platform: mediawiki
  platform_variant: fandom
  base_url: "https://growagarden.fandom.com/api.php"
  version: "MediaWiki 1.43.9"
  capabilities:
    - page_list
    - category_lookup
    - html_parse
    - wikitext_parse
    - imageinfo_query
  namespaces: [0]
  exclude_categories:
    - Disambiguations
    - Dev Products
    - Game Assets
    - Official Links
    - People
    - Celebrity Co-Host
  content_profile:
    discovery_strategy: "allpages"
    content_acquisition: "hybrid_wikitext_plus_rendered"
    link_resolver: "short_name_with_cross_namespace"
    template_processor: "fandom_infobox"
    list_page_assembler: "hybrid_frontmatter_and_rendered"
  taxonomy:
    list_pages:
      Crops: "Crops"
      Pets: "Pets"
      Gears: "Gears"
      Eggs: "Eggs"
      Cosmetics: "Cosmetics"
      NPCs: "NPCs"
      Events: "Events"
      Update Log: "Update_Log"
      Mechanics: "Game_Features"
      Seed Packs: "Packs"
      Chests: "Chests"
      Season Pass: "Season_Pass"
    page_categories:
      Crops: "Crops"
      Pets: "Pets"
      Gears: "Gears"
      Eggs: "Eggs"
      Cosmetics: "Cosmetics"
      Crates: "Cosmetics"
      NPC: "NPCs"
      Events: "Events"
      Update Log: "Update_Log"
      Currencies: "Currencies"
      Game Features: "Game_Features"
      Shops: "Shops"
      Packs: "Packs"
      Seed Packs: "Packs"
      Chests: "Chests"
      Season Pass: "Season_Pass"
      Containers: "Cosmetics"
    category_filters:
      - "Pages with too many expensive parser function calls"
      - "Pages with broken file links"
      - "Hidden categories"
      - "Stubs"
      - "Cleanup"
      - "Citation needed"
      - "Candidates for deletion"
      - "Candidates for speedy deletion"
      - "Articles with empty sections"
      - "Pages to be merged"
      - "Pages to be moved"
      - "Disambiguations"
      - "Template documentation"
  filename:
    replacements:
      "/": "_"
      ":": "_"
      " ": "_"
  rate_limit:
    tier: strict
    concurrency: 2
    batch_delay_ms: 500
    retry:
      max_retries: 3
      backoff_multiplier: 2.0
  output:
    link_format: markdown_relative
    frontmatter_fields:
      - title
      - categories
      - has_infobox
    template_map:
      "Crop": ""
      "Pets": ""
      "Gear": ""
      "NPC": ""
      "Weatherinfobox": ""
extraction:
  selectors:
    title: "#firstHeading"
    content: "#mw-content-text"
    nav: ".mw-parser-output"
  infobox:
    selector: ".portable-infobox, .infobox, table.item-table-header"
  cleanup:
    - strip_fandom_infobox_tables
    - convert_ambox_to_text
    - unwrap_image_wrappers
    - convert_nested_images
    - strip_edit_links
    - strip_category_links
    - strip_skip_links
    - strip_footer
    - fix_separators
    - normalize_internal
    - strip_empty_parens
  lazyload:
    enabled: true
    placeholder_pattern: "data:image/gif;base64"
    real_src_attr: "data-src"
  image_handling:
    base_url: "https://growagarden.fandom.com"
  text_normalization:
    - fix_spaces
    - normalize_blank_lines
    - deduplicate_words
---

# growagarden.fandom.com Strategy

## Overview

Fandom-hosted MediaWiki 1.43.9 wiki for **Grow a Garden**, a Roblox farming/idle
simulator. It is the largest game wiki by article count in this strategy registry:

| Metric | Value |
|--------|-------|
| Total pages (ns=0, incl. redirects) | 1,797 |
| Non-redirect content pages (ns=0) | 1,681 |
| Images | 36,909 |
| Templates | 279 |
| Categories | 147 |

## Protection & Engine Selection

| Layer | Status | Engine |
|-------|--------|--------|
| HTML (`/wiki/*`) | Cloudflare Managed Challenge (403 / "Just a moment...") | `cloakbrowser-fetch` (not used by default) |
| API (`/api.php`) | Open, but rejects non-browser User-Agents with 403 | Direct HTTP (`scrapling-get`) |

**Critical**: `python-urllib`'s default User-Agent is blocked with HTTP 403 even on
`/api.php`. `curl`'s UA and a browser UA both pass. Any client must send a browser
User-Agent.

**Primary acquisition path is API-first.** HTML is never required.

## Content Model

Two-tier structure, identical in shape to other Fandom game wikis but with unusually
consistent infobox templates:

### Entity pages (structured, template-driven)

```
{{Crop|produce_image=|crop_image=|seed_image=|tier=|seed_chance=|obtainable?=|multi-harvest?=|seed_price=}}
{{Pets|image1=|tier=|hatch_chance=|passive_ability=|date_added=|obtaining method=|Hunger=}}
{{Gear|gear_image=}}
{{NPC|...}}   {{Weatherinfobox|...}}
```

Fixed section vocabulary: `Overview / Appearance / Obtainment / Trait / Favorite Foods /
Trivia / Gallery`.

### System pages (`Category:Game Features`, 40 members)

Long-form system documentation: `Mechanics` (40 sections covering currencies, harvesting,
weight & value formulas, mutations, trading, ascension, garden level), `Trade System`,
`Weather`, `Crafting`, `Season Pass`, `Crop Mutations`, `Garden Ascension`, etc.

### Content families (non-redirect pages)

| Family | Pages | Directory |
|--------|------:|-----------|
| Crops | 554 | `Crops/` |
| Pets | 368 | `Pets/` |
| Gears | 196 | `Gears/` |
| Eggs | 68 | `Eggs/` |
| NPCs | 60 | `NPCs/` |
| Update Log | 60 | `Update_Log/` |
| Crates + Cosmetics | 100 | `Cosmetics/` |
| Events | 38 | `Events/` |
| Game Features + misc systems | ~60 | `Game_Features/` |
| Packs + Seed Packs | 64 | `Packs/` |
| Chests | 20 | `Chests/` |
| Shops | 19 | `Shops/` |
| Currencies | 17 | `Currencies/` |
| Season Pass | 7 | `Season_Pass/` |

## Discovery

`discovery_strategy: allpages` with `apfilterredir=nonredirects` (the strategy
implementation hardcodes the nonredirect filter), then classification by category and
removal of `exclude_categories`.

Allpages was chosen over `category_members` because a category-driven walk misses
~60 pages whose only signals are subtype categories (`Fruit Type Crops`, `Limited`,
`Stubs`). Allpages + exclusions reaches the full content set with one mechanism.

**Exclusions** (navigation/meta only, decided after inspecting all 147 categories):

| Category | Pages | Why excluded |
|----------|------:|--------------|
| Disambiguations | 69 | Navigation stubs, zero content |
| Dev Products | 5 | Store metadata |
| Game Assets | 2 | Wiki maintenance |
| Official Links | 1 | Outbound links |
| People | 5 | Contributor pages |
| Celebrity Co-Host | 3 | Event guest metadata |

Deliberately **kept** despite looking like noise: `Scrapped` (29) and `Unreleased` (101)
— cut and unreleased content is design-relevant. `Stubs` (638) is not an exclusion
because it overlaps heavily with real entity pages.

## Acquisition

`hybrid_wikitext_plus_rendered`: `prop=wikitext` is the primary source (templates are
consistent, so tier/drop-rate/price/passive-ability extract structurally). Rendered HTML
is fetched only for pages containing dynamic parser functions (`{{#invoke}}`, `#dpl`,
`#lst`), which is where list pages and the `Mechanics` tables live.

This differs from the sibling `neonabyss.fandom.com` strategy, which used
`html_rendered` and produced image-heavy output. Wikitext-primary avoids that.

## Images

The pipeline does **not** download image files — it only rewrites image URLs into
Markdown links. No image acquisition is configured; the 36,909 wiki images are left
untouched on the CDN. Inline icon spam from infoboxes is the known downside of Fandom
entity pages; if output readability suffers, strip `![...](...)` lines in post-processing
rather than adding pipeline config.

## Filename & Link Rules

- Filenames replace `/`, `:`, and space with `_` (e.g. `Update Log/1.04.0` →
  `Update_Log_1.04.0.md`).
- Internal links resolve to relative `.md` paths via `short_name_with_cross_namespace`.
- Sub-page titles such as `Update Log/1.04.0` and `Season Pass/Season 1` are real
  content pages and are kept.

## Known Issues

- **Cloudflare on HTML pages**: `/wiki/*` returns 403 to non-browser clients. Irrelevant
  to the API-first path.
- **UA-based WAF on the API**: `python-urllib` UA is rejected with 403. Resolved by
  sending a browser UA.
- **Category-order classification trap**: several summary pages carry both their own
  category and `Game Features` (e.g. `Gears` → `[Game Features, Gears]`). Alphabetical
  category order would misroute them, so every summary page is pinned explicitly in
  `taxonomy.list_pages`, which `classify_page` consults before category matching. Each
  directory has exactly one pinned list page to avoid index collisions.
- **Uncategorized summary pages**: `Crates`, `Seed Packs`, `Shops`, `Chests`,
  `Currencies`, `Events` carry no categories of their own. Those bound for a directory
  are pinned via `list_pages`; `Crates` is the one that still falls through to `Misc`
  because `Cosmetics` already holds that directory's index slot.
- **Rarity and type categories are layered, not exclusive**: a single crop carries
  `Crops` plus up to a dozen subtype/rarity categories. Classification uses the first
  matching key, which is always the family category.

## Evidence

- Siteinfo: `api.php?action=query&meta=siteinfo&siprop=general|statistics` — validated
  2026-09-10. Returns `MediaWiki 1.43.9`, `pages: 42440`, `articles: 1719`, `images: 36909`.
- API availability: `curl` to `/api.php?action=query&list=allpages&aplimit=1` returns 200
  JSON without challenge — validated 2026-09-10.
- HTML challenge: `scrapling-get` to `/wiki/Grow_a_Garden_Wiki` returns the
  `"Just a moment..."` interstitial — validated 2026-09-10.
- UA rejection: `python-urllib` default UA to `/api.php` returns HTTP 403; browser UA
  returns 200 — validated 2026-09-10.
- Non-redirect count: full `list=allpages&apfilterredir=nonredirects` walk returns 1,681
  pages — validated 2026-09-10.
- Category inventory: 147 categories enumerated via
  `action=query&list=allcategories&acprop=size` — validated 2026-09-10.
- Entity template shape: `action=parse&page=Apple&prop=wikitext` returns
  `{{Crop|...|seed_chance=7.14%|...}}`; `page=Bee` returns
  `{{Pets|...|hatch_chance=65%|passive_ability=...|Hunger=25000}}` — validated 2026-09-10.
- Summary page set: `action=query&titles=Crops|Pets|Gears|Eggs|...&prop=info` confirms
  which summary pages exist — validated 2026-09-10.
