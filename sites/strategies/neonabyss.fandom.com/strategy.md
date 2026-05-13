---
domain: neonabyss.fandom.com
description: Fandom-hosted MediaWiki 1.43.8 game wiki for Neon Abyss. Cloudflare Managed Challenge on HTML pages; MediaWiki API endpoints are unaffected. Dual-content model with summary list pages and individual entity pages.
protection_level: high
anti_crawl_refs:
  - default
  - rate-limit-api
structure:
  pages:
    - id: wiki_main_page
      label: Neon Abyss Wiki Main Page
      url_pattern: /wiki/Neon_Abyss_Wiki
      url_example: https://neonabyss.fandom.com/wiki/Neon_Abyss_Wiki
      type: static_article
      content_type: wiki_main_page
      pagination: none
      links_to:
        - target: summary_items
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_weapons
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_characters
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_monsters
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_pets
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_upgrades
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_pickups
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_patchnotes
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: summary_items
      label: Items Summary Page
      url_pattern: /wiki/Items
      url_example: https://neonabyss.fandom.com/wiki/Items
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_item
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: summary_weapons
      label: Weapons Summary Page
      url_pattern: /wiki/Weapons
      url_example: https://neonabyss.fandom.com/wiki/Weapons
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_weapon
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: summary_characters
      label: Characters Summary Page
      url_pattern: /wiki/Characters
      url_example: https://neonabyss.fandom.com/wiki/Characters
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_character
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: summary_monsters
      label: Monsters Summary Page
      url_pattern: /wiki/Monsters
      url_example: https://neonabyss.fandom.com/wiki/Monsters
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - target: entity_monster
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: summary_pets
      label: Pets Summary Page
      url_pattern: /wiki/Pets
      url_example: https://neonabyss.fandom.com/wiki/Pets
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to: []
      requires_auth: false
    - id: summary_pickups
      label: Pickups Summary Page
      url_pattern: /wiki/Pickups
      url_example: https://neonabyss.fandom.com/wiki/Pickups
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to: []
      requires_auth: false
    - id: summary_upgrades
      label: Upgrades Summary Page
      url_pattern: /wiki/Upgrades
      url_example: https://neonabyss.fandom.com/wiki/Upgrades
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to: []
      requires_auth: false
    - id: entity_item
      label: Individual Item Page
      url_pattern: /wiki/ITEM_NAME
      url_example: https://neonabyss.fandom.com/wiki/Acorn
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_item
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_items
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: entity_weapon
      label: Individual Weapon Page
      url_pattern: /wiki/WEAPON_NAME
      url_example: https://neonabyss.fandom.com/wiki/Airgun
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_weapon
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_weapons
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: entity_character
      label: Individual Character Page
      url_pattern: /wiki/CHARACTER_NAME
      url_example: https://neonabyss.fandom.com/wiki/Amir
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_character
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_characters
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
    - id: entity_monster
      label: Individual Monster Page
      url_pattern: /wiki/MONSTER_NAME
      url_example: https://neonabyss.fandom.com/wiki/Bear_Fly
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - target: entity_monster
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
        - target: summary_monsters
          selector: ".mw-parser-output a[href^=\"/wiki/\"]"
      requires_auth: false
  entry_points:
    - wiki_main_page
    - summary_items
    - summary_weapons
    - summary_characters
    - summary_monsters
    - summary_pets
    - summary_pickups
    - summary_upgrades
api:
  platform: mediawiki
  base_url: "https://neonabyss.fandom.com/api.php"
  capabilities:
    - page_list
    - category_lookup
    - html_parse
    - wikitext_parse
    - imageinfo_query
  namespaces: [0]
  content_profile:
    discovery_strategy: "category_members"
    content_acquisition: "html_rendered"
    link_resolver: "short_name_with_cross_namespace"
    template_processor: "fandom_infobox"
    list_page_assembler: "hybrid_frontmatter_and_rendered"
  platform_variant: fandom
  page_type_map:
    summary_pages:
      - Items
      - Weapons
      - Characters
      - Monsters
      - Pets
      - Pickups
      - Upgrades
      - Patchnotes
    entity_pages:
      items_category: "Category:Items"
      weapons_category: "Category:Weapons"
      characters_category: "Category:Characters"
      monsters_category: "Category:Monsters"
  taxonomy:
    page_categories:
      Items: "Items"
      Weapons: "Weapons"
      Characters: "Characters"
      Monsters: "Monsters"
      Pets: "Pets"
      Pickups: "Pickups"
      Upgrades: "Upgrades"
      Patchnotes: "Patchnotes"
    category_filters:
      - "Neon Abyss Wiki"
      - "Neon Abyss"
      - "Neon Abyss images"
      - "Disambiguations"
      - "Stubs"
      - "Candidates for deletion"
      - "Candidates for speedy deletion"
      - "Pages to be merged"
      - "Pages to be moved"
      - "Pages with broken file links"
      - "Hidden categories"
      - "Articles with empty sections"
      - "Cleanup"
      - "Citation needed"
      - "TR translation"
      - "FR translation"
  filename:
    replacements:
      "/": "_"
      ":": "_"
      " ": "_"
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
      "Infobox item": ""
      "Infobox monster": ""
      "Infobox weapon": ""
      "Infobox character": ""
extraction:
  pipeline: BeautifulSoup preprocessing + markdownify conversion
  selectors:
    title: "#firstHeading"
    body: ".mw-parser-output"
  image_handling:
    attribute: src
    lazyload_fallback: data-src
    output_format: markdown_inline
    keep_inline_in: [td, th, span, a, div, p, li]
    base_url: https://neonabyss.fandom.com
  cleanup:
    - fix_lazyload_images: replace base64 src with data-src
    - strip_edit_sections: remove .mw-editsection elements
    - strip_toc: remove #toc and Contents headers
    - strip_fandom_infobox_tables: remove item-table-* and infobox-table classes
    - convert_ambox_to_text: replace ambox tables with ⚠️ paragraph
    - unwrap_image_wrappers: unwrap <a> tags that only contain <img>
    - unwrap_image_file_links: unwrap <a> tags whose href is an image URL
    - convert_wiki_links: replace /wiki/ links with markdown relative links
    - strip_translation_links: remove /tr interlanguage links
    - strip_empty_elements: remove empty p/div without images
  text_normalization:
    space_fix:
      enabled: true
      patterns:
        - regex: '([a-zA-Z])(\d+(?:\.\d+)*)([a-zA-Z])'
          replacement: '\1 \2 \3'
          description: 'Fix missing spaces around version numbers (supports multi-dot like 1.4.6)'
        - regex: '([a-z])\.([A-Z])'
          replacement: '\1. \2'
          description: 'Fix missing space after period'
    consecutive_image_spacing:
      enabled: true
      description: 'Add spaces between consecutive inline images ![A](x)![B](y)'
    link_resolution:
      enabled: true
      resolve_to: "markdown_relative"
      fallback: "external_wiki_url"
---

## Overview

neonabyss.fandom.com is a Fandom-hosted MediaWiki 1.43.8 game wiki for *Neon Abyss*, a roguelike action-platformer developed by Veewo Games and published by Team17.

The site operates under a **dual-content model**:
- **Summary pages** (`Items`, `Weapons`, `Characters`, `Monsters`, `Pets`, `Pickups`, `Upgrades`): comprehensive list pages with large data tables covering all entities in a category.
- **Individual entity pages** (`Airgun`, `Acorn`, `Amir`, `Bear Fly`): short articles describing a single game entity, some with infoboxes.

Critical infrastructure note: **HTML pages are protected by Cloudflare Managed Challenge**, returning a `"Just a moment..."` interstitial to non-browser clients. However, **MediaWiki API endpoints (`/api.php`) are completely unaffected** and return valid JSON without any challenge. The recommended acquisition path is therefore **MediaWiki API-first**.

## Site Scale

| Metric | Value |
|--------|-------|
| Total pages | 2,875 |
| Articles (ns=0) | 699 |
| Images | 1,828 |
| Edits | 8,151 |
| Active users | 1 |
| Admins | 3 |

## Content Model

### Summary Pages (Single-page category coverage)

These pages contain complete tabular data for an entire category. They are the **only** source for `Pets`, `Pickups`, and `Upgrades`, which have no individual article pages.

| Page | Entities | Structure |
|------|----------|-----------|
| `Items` | 100+ items | Multi-section with category tables; links to individual item pages |
| `Weapons` | 60 weapons | Two tables: Regular Weapons + Starter Weapons |
| `Characters` | 9 playable characters | Overview + links to individual character pages |
| `Monsters` | 50+ monsters | Overview + links to individual monster pages |
| `Pets` | 48 pets | Single large table (Icon/Name/Description/HP/Evolves from/Evolves?) |
| `Pickups` | 30+ pickups | Sectioned by type: Hearts, Shields, Crystals, Coins, Keys, Bombs, Misc |
| `Upgrades` | 50+ upgrades | 6 Upgrade Trees with individual unlock entries |

### Individual Entity Pages

Pages exist for entities in `Items`, `Weapons`, `Characters`, and `Monsters` categories.

**Items** (e.g., `Acorn`):
- Uses `{{Infobox item|name=...|image=...|description=...|appearance=...}}` template
- Sections: General Information, Effect, Trivia
- May include `ambox` notice: "The information in this article is from game version X on Steam"

**Weapons** (e.g., `Airgun`):
- No infobox template; uses Fandom table markup for attributes
- Typical attributes: Description, Ability, Type, Output, Rate of Fire
- May include animated GIFs (e.g., `Airgun_2.gif`)
- Sections: (often none — single-section articles)

**Characters** (e.g., `Amir`):
- No infobox; uses simple attribute table (HP, Keys, Bombs)
- Sections: Description, Ability

**Monsters** (e.g., `Bear Fly`):
- Uses `{{Infobox monster|name=...|image=...}}`
- Sections: General Information
- Typically very short (1-2 paragraphs)

## Protection & Engine Selection

| Layer | Status | Recommended Engine |
|-------|--------|-------------------|
| HTML (`/wiki/*`) | Cloudflare Managed Challenge (403) | `cloakbrowser-fetch` (playwright_stealth) |
| API (`/api.php`) | Unrestricted | Direct HTTP / `scrapling-get` |

**Engine priority**:
1. `scrapling-get` — for API calls (action=query, action=parse)
2. `cloakbrowser-fetch` — for HTML fallback if API is insufficient
3. `chrome-devtools-mcp` — diagnostic fallback

## Discovery Flow

1. **Site initialization**: `action=query&meta=siteinfo&siprop=general|statistics`
   - Confirm MediaWiki version, article count, namespace configuration.

2. **Seed pages** (explicit entry points):
   - `Neon_Abyss_Wiki` (main page)
   - `Items`, `Weapons`, `Characters`, `Monsters`, `Pets`, `Pickups`, `Upgrades`

3. **Category-based discovery** for individual pages:
   - `action=query&list=categorymembers&cmtitle=Category:Items`
   - `action=query&list=categorymembers&cmtitle=Category:Weapons`
   - `action=query&list=categorymembers&cmtitle=Category:Characters`
   - `action=query&list=categorymembers&cmtitle=Category:Monsters`
   - Filter by `ns=0` to exclude translation pages (`/tr` suffix).

4. **Gap analysis**: Compare category member list against discovered individual pages. Summary pages may link to pages not yet in category lists.

5. **Normalization**: `action=query&titles=...&redirects=1` to resolve redirects.

## Content Acquisition Flow

### Primary: `action=parse` (HTML-rendered)

Request:
```
action=parse&page=TITLE&prop=text|categories|links|sections|displaytitle|wikitext
```

Extract:
- `displaytitle`: Human-readable title
- `text`: Parsed HTML body (`mw-parser-output` wrapper)
- `wikitext`: Raw wikitext for infobox extraction
- `categories`: Page categories for classification
- `links`: Outgoing wiki links for graph expansion
- `sections`: Section structure

### HTML Fallback

If API parse output is incomplete or specific rendering is required:
- Use `cloakbrowser-fetch` with `--wait-until domcontentloaded --wait 8`
- Cloudflare challenge typically resolves within 3-5 seconds with stealth browser

## Extraction & Conversion Rules

### Infobox Handling

Fandom renders infoboxes as a sequence of HTML tables with classes:
- `item-table-header` — entity name
- `item-table-body` — main image
- `item-table-description` — description text
- `item-table-appearance` — appearance/secondary image

**Rule**: Remove these visual tables from HTML before Markdown conversion. Extract structured data from wikitext `{{Infobox ...}}` template and emit as a Markdown table in frontmatter or article header.

### Article Message Boxes (ambox)

Pages often contain `plainlinks ambox ambox-green` tables with notices like:
> "The information in this article is from game version 1.4.6 on Steam."

**Rule**: Convert to a blockquote or plain paragraph prefixed with `⚠️`. Do not leave as HTML table.

### Table of Contents Removal

MediaWiki auto-generates a `Contents` block with numbered section links.

**Rule**: Strip the entire TOC block from Markdown output.

### Internal Link Resolution

Wiki internal links (`/wiki/Page_Name`) should be converted to relative Markdown links (`[Page Name](Page_Name.md)`) when the target page is also in the crawl set. Links to un-crawled pages should fall back to plain text or external wiki URL.

### Space Normalization

Link stripping may produce text like `game version1.4.6on Steam`.

**Rule**: Apply regex-based space normalization:
- `([a-zA-Z])(\d)([a-zA-Z])` → `$1 $2 $3`
- Missing space after period: `([a-z])\.([A-Z])` → `$1. $2`

### Image Handling

- Preserve all Wikia image URLs (`static.wikia.nocookie.net/...`) as Markdown inline images
- Animated GIFs (e.g., weapon previews) must retain their `.gif` extension
- Image dimensions from API `scale-to-width-down/` paths are acceptable; full-resolution URLs can be reconstructed by removing the scale parameter

### Translation Page Filtering

The wiki contains Turkish translation pages with `/tr` suffix (e.g., `Amir/tr`, `Items/tr`).

**Rule**: Exclude pages matching `title.endswith('/tr')` or `ns != 0` from the crawl set.

## Output Structure

```
outputs/neonabyss-fandom/
├── summary/
│   ├── Items.md
│   ├── Weapons.md
│   ├── Characters.md
│   ├── Monsters.md
│   ├── Pets.md
│   ├── Pickups.md
│   └── Upgrades.md
├── items/
│   ├── Acorn.md
│   ├── Air_Force_Medal.md
│   └── ...
├── weapons/
│   ├── Airgun.md
│   ├── Black_Raven.md
│   └── ...
├── characters/
│   ├── Amir.md
│   ├── Anna.md
│   └── ...
└── monsters/
    ├── Bear_Fly.md
    ├── Bear_Jumper.md
    └── ...
```

Each Markdown file includes YAML frontmatter:
```yaml
---
title: Page Title
categories: [Category1, Category2]
sections: [General Information, Effect]
has_infobox: true
---
```

## Known Issues

- **Cloudflare on HTML pages**: Direct HTTP to `/wiki/*` returns 403. API endpoints bypass this entirely.
- **No individual pages for Pets/Pickups/Upgrades**: These categories only exist as summary list pages.
- **Fandom infobox rendering**: Infobox HTML uses non-standard table classes (item-table-*) that fragment into multiple small tables during Markdown conversion. Resolved by `fandom_html_to_markdown.py`: remove visual tables, extract structured data from wikitext.
- **Fandom lazy-loaded images**: Images use `src="data:image/gif;base64,..."` placeholder with real URL in `data-src`. Resolved by `fandom_html_to_markdown.py`: replace src with data-src before conversion.
- **Fandom ambox table structure**: ambox notices are HTML tables, not text. Resolved by `fandom_html_to_markdown.py`: convert to ⚠️ paragraph.
- **Empty Trivia sections**: Some item pages have `Trivia` sections with only a dash (`-`) or completely empty. These should be dropped or marked as empty.
- **Unresolved: summary tables with extra blank columns**: Wikis often render HTML tables with extra empty first column (for image icons). May produce leading `| |` in Markdown tables; acceptable cosmetic issue.

## Implementation

The strategy-driven conversion logic is implemented in:
-  — reusable Python module
  -  — main entry point, returns Markdown string with frontmatter
  - Fandom-specific: lazy-load fix, item-table cleanup, ambox handling
  - Link resolution: known pages → relative .md links, unknown → external wiki
  - Text normalization: space fixes, consecutive image spacing
  - Dependencies:  + 

## Evidence

- Siteinfo: `api.php?action=query&meta=siteinfo&siprop=general|statistics` — validated 2026-05-12. Returns `generator: MediaWiki 1.43.8`, `pages: 2875`, `articles: 699`.
- API availability: Direct curl to `/api.php?action=query&list=allpages&aplimit=1` returns 200 JSON without challenge — validated 2026-05-12.
- HTML challenge: `scrapling-get` to `/wiki/Neon_Abyss_Wiki` returns HTTP 403 — validated 2026-05-12.
- Cloudflare interstitial: `obscura fetch` returns `"Just a moment..."` challenge page — validated 2026-05-12.
- Stealth success: `cloakbrowser` with `headless=True` successfully resolves challenge and returns 226KB valid HTML — validated 2026-05-12.
- Parse (Weapons): `api.php?action=parse&page=Weapons&prop=text|wikitext` returns full article with 113 images — validated 2026-05-12.
- Parse (Acorn): `api.php?action=parse&page=Acorn&prop=text|wikitext` returns infobox template and 3 sections — validated 2026-05-12.
- Category (Items): `api.php?action=query&list=categorymembers&cmtitle=Category:Items` returns 50+ items with `continue` token — validated 2026-05-12.
- Pets category empty: `Category:Pets` has no article members (only `Pets` page + `Category:Items` reference) — validated 2026-05-12.
- Translation pages: `Amir/tr`, `Items/tr` exist in ns=0 and must be filtered — validated 2026-05-12.
- Reports: `reports/2026-05-12-explore-neonabyss-fandom-com-wiki-neon-abyss-wiki.md`