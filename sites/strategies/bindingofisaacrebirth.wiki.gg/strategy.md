---
domain: bindingofisaacrebirth.wiki.gg
description: "The Binding of Isaac: Rebirth Wiki on wiki.gg - MediaWiki 1.43.6 covering Rebirth, Afterbirth, Afterbirth+, Repentance, and Repentance+ content. Full-site crawl via allpages API path."
protection_level: medium
anti_crawl_refs:
  - cloudflare-turnstile
  - rate-limit-api
structure:
  pages:
    - id: main_page
      label: Main Page
      url_pattern: /wiki/Binding_of_Isaac:_Rebirth_Wiki
      url_example: https://bindingofisaacrebirth.wiki.gg/wiki/Binding_of_Isaac:_Rebirth_Wiki
      type: static_article
      content_type: wiki_main_page
      pagination: none
      links_to:
        - target: content_index
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: content_index
      label: Content Index Page
      url_pattern: /wiki/{Items,Trinkets,Characters,Bosses,Chapters,...}
      url_example: https://bindingofisaacrebirth.wiki.gg/wiki/Items
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_page
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: entity_page
      label: Entity Page
      url_pattern: /wiki/*
      url_example: https://bindingofisaacrebirth.wiki.gg/wiki/The_Sad_Onion
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_page
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: category_page
      label: Category Page
      url_pattern: /wiki/Category:*
      url_example: https://bindingofisaacrebirth.wiki.gg/wiki/Category:Objects
      type: category
      content_type: wiki_category
      pagination: none
      links_to:
        - target: entity_page
          selector: ".mw-parser-output a[href^='/wiki/']"
      requires_auth: false
  entry_points:
    - main_page
api:
  platform: mediawiki
  platform_variant: wiki-gg
  base_url: "https://bindingofisaacrebirth.wiki.gg/api.php"
  capabilities:
    - page_list
    - allpages
    - category_lookup
    - html_parse
    - wikitext_parse
    - imageinfo_query
  homepage:
    page_title: "Binding_of_Isaac:_Rebirth_Wiki"
    category_sections:
      - selector: ".gallerytext a"
        type: list_page
    categories:
      - {name: "Items", dir: "items", mw_category_aliases: ["Collectibles", "Activated Collectibles", "Passive Collectibles"]}
      - {name: "Trinkets", dir: "trinkets", mw_category_aliases: ["Trinkets"]}
      - {name: "Bosses", dir: "bosses", mw_category_aliases: ["Bosses"]}
      - {name: "Monsters", dir: "monsters", mw_category_aliases: ["Monsters"]}
      - {name: "Characters", dir: "characters"}
      - {name: "Cards", dir: "cards"}
      - {name: "Challenges", dir: "challenges"}
      - {name: "Transformations", dir: "transformations"}
      - {name: "Chapters", dir: "chapters", mw_category_aliases: ["Stages"]}
      - {name: "Rooms", dir: "rooms"}
      - {name: "Mechanics", dir: "mechanics"}
      - {name: "Achievements", dir: "achievements", mw_category_aliases: ["Achievements"]}
      - {name: "Pickups", dir: "pickups"}
      - {name: "Effects", dir: "effects"}
      - {name: "Curses", dir: "curses"}
      - {name: "Seeds", dir: "seeds"}
      - {name: "Endings", dir: "endings"}
      - {name: "Music", dir: "music"}
      - {name: "Modes", dir: "modes"}
      - {name: "Objects", dir: "objects"}
    category_page_types:
      Modes: category_page
      Objects: category_page
    assignment_priority:
      - "Items"
      - "Bosses"
      - "Monsters"
      - "Characters"
      - "Cards"
      - "Challenges"
      - "Transformations"
      - "Chapters"
      - "Rooms"
      - "Mechanics"
      - "Achievements"
      - "Pickups"
      - "Effects"
      - "Curses"
      - "Seeds"
      - "Endings"
      - "Music"
      - "Trinkets"
      - "Modes"
      - "Objects"

    exclude_categories:
      - "Music"
      - "Modding"
      - "Version History"
  namespaces: [0]
  # New top-level exclude_categories. Legacy alias at api.homepage.exclude_categories
  # still works as fallback. Both are merged (union) at runtime.
  exclude_categories:
    - "Music"
    - "Modding"
    - "Version History"
  content_profile:
    # discovery_strategy is treated as hint for --discovery auto.
    # When api.homepage is defined, homepage discovery takes precedence
    # over discovery_strategy. Use --discovery allpages to override.
    discovery_strategy: "allpages"
    content_acquisition: "html_rendered"
    link_resolver: "short_name_with_cross_namespace"
    template_processor: "structured_with_lua_fallback"
    list_page_assembler: "hybrid_frontmatter_and_rendered"
  taxonomy:
    list_pages:
      Items: "Items"
      Trinkets: "Trinkets"
      Bosses: "Bosses"
      Monsters: "Monsters"
      Characters: "Characters"
      Cards: "Cards"
      Completion Marks: "Completion_Marks"
      Pickups: "Pickups"
      Challenges: "Challenges"
      Transformations: "Transformations"
      Chapters: "Chapters"
      Rooms: "Rooms"
      Mechanics: "Mechanics"
      Achievements: "Achievements"
      Attributes: "Attributes"
      Curses: "Curses"
      Effects: "Effects"
      Modding: "Modding"
      Endings: "Endings"
      Seeds: "Seeds"
      Music: "Music"
      Version History: "Version_History"
    page_categories:
      Collectibles: "Collectibles"
      Activated Collectibles: "Collectibles/Activated"
      Passive Collectibles: "Collectibles/Passive"
      Bosses: "Bosses"
      Monsters: "Monsters"
      Characters: "Characters"
      Cards: "Cards"
      Trinkets: "Trinkets"
      Challenges: "Challenges"
      Transformations: "Transformations"
      Chapters: "Chapters"
      Rooms: "Rooms"
      Mechanics: "Mechanics"
      Achievements: "Achievements"
      Pickups: "Pickups"
      Modding: "Modding"
      Stages: "Chapters"
      Runes: "Runes"
      Item pools: "Item_pools"
      Disambiguations: "Disambiguations"
      Versions: "Versions"
      Objects: "Objects"
      Bugs: "Bugs"
      Item tags: "Item_tags"
    category_filters:
      - "Binding of Isaac: Rebirth Wiki"
      - "Disambiguations"
      - "Candidates for deletion"
      - "Candidates for speedy deletion"
      - "Stubs"
      - "Cargo categories"
      - "Cargo storage pages"
      - "Cargo templates"
      - "Categories by namespace"
      - "Categories by source"
      - "Category namespace categories"
      - "Category namespace templates"
      - "Gadget definition pages"
      - "Pages with broken file links"
  filename:
    replacements:
      "/": "_"
      ":": "_"
      " ": "_"
  parse_options:
    redirects: true
    prop: "text|wikitext|sections|displaytitle"
  rate_limit:
    tier: strict
    batch_delay_ms: 1200
    retry:
      max_retries: 5
      backoff_multiplier: 2.5
  output:
    link_format: markdown_relative
extraction:
  selectors:
    title: "#firstHeading"
    body: ".mw-parser-output"
  image_handling:
    attribute: src
    output_format: markdown_inline
    base_url: https://bindingofisaacrebirth.wiki.gg
  cleanup_selectors:
    - ".mw-editsection"
    - ".toc"
    - "#toc"
    - ".hatnote"
    - "div.nav-box"
    - "div.nav-main"
    - "div.nav-header"
    - "div.nav-footer"
    - "table.navbox"
    - "table.nowraplinks"
    - ".redirectMsg"
  infobox:
    enabled: true
    selector: "aside.portable-infobox"
    field_selector: "div.pi-data"
    label_selector: "h3.pi-data-label"
    value_selector: "div.pi-data-value"
  image_filtering:
    skip_patterns:
      - "Icon_mini.png"
      - "Wiki.png"
      - "Font_TeamMeat"
      - "Dlc_.*indicator"
      - "SmallIsaac.png"
      - "MainPage.*\\.png"
  lazyload:
    enabled: true
    placeholder_pattern: "data:image/gif;base64"
    real_src_attr: "data-src"
  cleanup:
    - strip_footer
    - strip_edit_links
    - strip_skip_links
    - strip_empty_parens
    - convert_nested_images
    - normalize_internal
    - strip_category_links
    - normalize_infobox
    - fix_separators
    - unwrap_image_wrappers
  url_conversion:
    enabled: true
  youtube_cleanup:
    enabled: true
  infobox_field_handlers:
    health:
      handler: count_images
      description: "Count red heart images"
    id:
      handler: extract_cur_id
      description: "Extract current ID from infobox-nav-cur span"
    alias:
      handler: dedup_pools
      description: "Deduplicate item pool links, skip icon-only entries"
    "alias(Collection grid)":
      handler: simplify_collection
      description: "Simplify collection grid to single page link"
    tags:
      handler: extract_tags
      description: "Extract tag tooltips from icon links"
    image:
      handler: image
      description: "Extract main image as Markdown"
    portrait:
      handler: image
      description: "Extract portrait image as Markdown"
    costume:
      handler: image
      description: "Extract costume image as Markdown"
---

## Overview

bindingofisaacrebirth.wiki.gg is a MediaWiki 1.43.6 site hosted on wiki.gg. It contains comprehensive content for The Binding of Isaac: Rebirth and all its DLCs (Afterbirth, Afterbirth+, Repentance, Repentance+) in a single namespace (ns=0).

**Key stats** (probed 2026-05-16):
- Total pages (ns=0): ~3,255
- Articles: ~1,769
- Images: ~8,192
- Categories: 500+

## Namespace Configuration

| ID | Canonical | Content |
|----|-----------|---------|
| 0 | (main) | All game content |
| 14 | Category | Category pages |

No custom namespaces needed — all game content lives in ns=0.

## Content Structure

### Main Page
- Links to 28 top-level content pages: Items, Trinkets, Characters, Chapters, Rooms, Bosses, Monsters, Pickups, Effects, Curses, Seeds, Endings, Music, etc.
- Also links to game versions: Rebirth, Afterbirth, Afterbirth+, Repentance, Repentance+

### List Pages
- **Items** (~1M chars HTML): Massive list with all collectibles, split into Activated and Passive sections
- **Trinkets**: 189 items
- **Bosses**: 132 entries
- **Monsters**: 105 entries
- **Characters**: 37 entries
- **Cards**: 55 entries
- **Challenges**: 46 entries
- **Mechanics**: 51 entries
- **Rooms**: 23 entries

### Entity Pages
- Standard MediaWiki articles with infobox templates, navboxes, and category links
- Heavy use of game-specific templates (item stats, damage calculations, etc.)

## Discovery Flow

1. **allpages** (primary): `action=query&list=allpages&apnamespace=0&aplimit=500`
   - Guaranteed full coverage of all 3,255 pages
   - Continue pagination until exhausted (estimated ~7 batches of 500)

2. **category members** (supplementary): Used for taxonomy classification
   - After discovery, query categories for each page to build folder structure

## Content Acquisition Flow

### Primary: `action=parse`

```
action=parse&page=TITLE&prop=text|categories|links|sections|displaytitle
```

### Fallback: `prop=revisions` (wikitext)

```
action=query&prop=revisions&rvprop=content&rvslots=main&titles=...
```

## Rate Limiting

- wiki.gg enforces rate limiting (confirmed 429 on rapid sequential requests)
- `batch_delay_ms: 1200` (1.2s between batches)
- `max_retries: 5` with `backoff_multiplier: 2.5`
- At ~500 pages/batch with 1.2s delay, full crawl estimated at ~20-30 minutes

## Validation (2026-05-17)

Sample validation completed with 20 pages across all content categories.

**Validation method**: action=parse API → HTML → custom converter → Markdown → S1-S12 self-check

**Samples tested**: The Sad Onion, Trinkets (list), Isaac, Monstro, Gaper, Basement, Arcade, Hearts, Status Effects, Curses, Seeds, Endings, Music, Aprils Fool, Guppy, Speed, Achievements, Completion Marks, Poop (Disambiguation), 0 - The Fool

**Key findings**:
1. Infobox uses `<aside class="portable-infobox">` (wiki.gg skin), NOT `<table class="infobox">`
2. Navigation footer uses `<div class="nav-box nav-main">`, NOT `<table class="navbox">`
3. Decorative images: Font_TeamMeat letters, Dlc_*_indicator badges, SmallIsaac.png
4. All entity pages include `<a class="image"><img></a>` wrappers around infobox images
5. YouTube video embeds leave "Load video / YouTube / Privacy Policy" residue
6. Lazyload images use `data:image/gif;base64` src with real URL in `data-src` attr
7. Entity IDs like `5.100.1`, `5.350.57` appear throughout — these are NOT version numbers
8. Template-embedded headings (e.g. `UnlockableAchievements`) use camelCase, non-standard

**Content quality**: All pages produced complete, readable Markdown with correct structure, links, images, and table content. Known issues are cosmetic and do not affect content fidelity.

## Known Issues (Post-Validation)

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| KI-1 | S1 image count mismatch | open_systemic | P2 | self_check | Template-internal images not rendered by markdownify | markdownify template folding — not fixable without template rendering |
| KI-2 | S5 version regex false positive | resolved | P1 | self_check | Image URL hash fragments matched as version | Self-Check: strip `![...](...)` from scan before version regex |
| KI-3 | S6 table row deviation | resolved | P3 | self_check | Nav tables counted as data tables | Self-Check: exclude nav table classes; 5%→10% tolerance |
| KI-4 | S8 template-embedded headings | resolved | P3 | pipeline | Template headings not standard mw-headline | Template artifacts — only triggers on pages with such templates |
| KI-5 | Infobox field value concatenation | resolved | P1 | pipeline | `![]()[text](url)` without space between image and link | Pipeline: post-processing regex ensures space between image and following link |
| KI-6 | Collectible ID 'None' prefix | resolved | P0 | pipeline | Shows 'None1' instead of '1' | Pipeline: decompose `.infobox-nav-prev` + `.infobox-nav-next` before extraction |
| KI-7 | Link index construction & injection verification | open | P2 | pipeline | Homepage-driven crawl produces pages with absolute URLs after initial conversion | Pipeline auto-calls `fix_links_in_dir()` after extraction to convert to relative links |
| KI-8 | List page directory assignment bug | resolved | P0 | pipeline | All list pages assigned to `items/` directory | `_build_homepage_manifest()` uses strategy-backed `dir` mapping from `api.homepage.categories` |
| KI-9 | Exclude filter misses title-based matches | resolved | P1 | pipeline | Version History leaks through via `source_categories` | Orchestrator checks `p["title"] in exclude_set` in addition to category checks |
| KI-10 | Assembly creates orphan index.md for non-manifest list_pages | resolved | P2 | pipeline | Mechanics/Cards index.md created without content | Assembly checks `manifest_pages_by_title` + `is_list_page` guard + removes empty dirs |
| KI-11 | Parenthesis filenames break Markdown links | resolved | P3 | pipeline | 116 broken links from `(` `)` in filenames | `_to_markdown_link()` encodes `(` → `%28`, `)` → `%29`; `link_fixer` repairs existing links |
| KI-12 | YouTube "Load video" fallback text persists | resolved | P4 | pipeline | "Load video" / "YouTube might collect" text in output | `clean_html()` removes `<div>` elements containing "Load video" |
| KI-13 | Frontmatter image selects decorative icons | resolved | P5 | pipeline | Font_TeamMeat icons selected as page image | `_process_html_page()` applies `skip_patterns` before selecting frontmatter image |
## Evidence

- Siteinfo: `api.php?action=query&meta=siteinfo&siprop=general|statistics|namespaces` — validated 2026-05-16
- Allpages: `api.php?action=query&list=allpages&apnamespace=0&aplimit=500` — validated 2026-05-16
- Main page parse: `api.php?action=parse&page=Binding_of_Isaac:_Rebirth_Wiki&prop=links|sections` — validated 2026-05-16
- Items page: `api.php?action=parse&page=Items&prop=text|categories|sections` — validated 2026-05-16 (1M+ chars HTML)
- Category samples: Trinkets (189), Bosses (132), Monsters (105), Characters (37), Cards (55) — validated 2026-05-16
- Rate limit confirmed: 429 on sequential requests without delay — validated 2026-05-16
- Sample validation: 20 pages across all categories with S1-S12 self-check — validated 2026-05-17
