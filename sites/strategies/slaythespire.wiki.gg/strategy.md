---
domain: slaythespire.wiki.gg
description: Slay the Spire 2 wiki on wiki.gg, a MediaWiki 1.43.6 site with custom namespace (ns=3000) for sequel content
protection_level: low
anti_crawl_refs:
  - default
structure:
  pages:
    - id: sts2_main_page
      label: Slay the Spire 2 Main Page
      url_pattern: /wiki/Slay_the_Spire_2:Main
      url_example: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Main
      type: static_article
      content_type: wiki_main_page
      pagination: none
      links_to:
        - sts2_list_page
        - sts2_mechanic_page
        - sts2_character_page
        - sts2_act_page
        - sts2_ancient_page
      requires_auth: false
    - id: sts2_list_page
      label: StS2 List Page
      url_pattern: /wiki/Slay_the_Spire_2:*_List
      url_example: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Cards_List
      type: static_article
      content_type: wiki_list_page
      pagination: none
      links_to:
        - sts2_entity_page
      requires_auth: false
    - id: sts2_entity_page
      label: StS2 Entity Page
      url_pattern: /wiki/Slay_the_Spire_2:*
      url_example: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Bash
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - sts2_entity_page
        - sts2_list_page
        - sts2_mechanic_page
      requires_auth: false
    - id: sts2_mechanic_page
      label: StS2 Mechanic Page
      url_pattern: /wiki/Slay_the_Spire_2:Mechanics
      url_example: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Mechanics
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - sts2_entity_page
        - sts2_list_page
      requires_auth: false
    - id: sts2_character_page
      label: StS2 Character Page
      url_pattern: /wiki/Slay_the_Spire_2:Ironclad|Silent|Regent|Necrobinder|Defect
      url_example: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Ironclad
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - sts2_entity_page
        - sts2_list_page
      requires_auth: false
    - id: sts2_act_page
      label: StS2 Act Page
      url_pattern: /wiki/Slay_the_Spire_2:Overgrowth|Underdocks|Hive|Glory
      url_example: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Overgrowth
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - sts2_entity_page
      requires_auth: false
    - id: sts2_ancient_page
      label: StS2 Ancient Page
      url_pattern: /wiki/Slay_the_Spire_2:Neow|Orobas|Pael|Tezcatara|Darv|Nonupeipe|Tanx|Vakuu
      url_example: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Neow
      type: static_article
      content_type: wiki_article
      pagination: none
      links_to:
        - sts2_entity_page
      requires_auth: false
  entry_points:
    - sts2_main_page
extraction:
  image_handling:
    attribute: src
    output_format: markdown_inline
    base_url: https://slaythespire.wiki.gg
---

## Overview

slaythespire.wiki.gg is a MediaWiki 1.43.6 site hosted on wiki.gg. It contains content for both Slay the Spire 1 (ns=0) and Slay the Spire 2 (ns=3000). The site shares a single domain and homepage, with StS2 content isolated in the custom namespace "Slay the Spire 2" (canonical) / "StS2" (alias).

The recommended acquisition path is **MediaWiki API-first**:
- HTML article pages trigger Cloudflare challenge (`cf-mitigated` on `/wiki/Slay_the_Spire_2:*`).
- `action=parse` and `action=query` endpoints are accessible without challenge.
- All StS2 discovery and content extraction should target `ns=3000` to avoid StS1 contamination.

## Namespace Configuration

| ID | Canonical | Alias | Content |
|----|-----------|-------|---------|
| 0 | (main) | — | Slay the Spire 1 |
| 3000 | Slay the Spire 2 | StS2 | Slay the Spire 2 |
| 3010 | Board Game | TTG | Board game content |
| 14 | Category | — | Shared categories (StS1 + StS2) |

**Rule**: Always filter by `ns=3000` during discovery and metadata queries.

## Page Structure

### Main Page (`/wiki/Slay_the_Spire_2:Main`)

- CSS Grid layout (`#mp-container`) with 8 named areas.
- **Games**: Two banner images linking to StS1 wiki root (`/`) and StS2 main page (self).
- **Welcome**: Article count (1,360 articles / 9,877 pages), link to `Special:AllPages`.
- **About**: One-paragraph game description.
- **Gameplay**: 9 navigation items (Acts, Timeline, Buffs, Debuffs, Mechanics, Keywords, Achievements, Map Locations, Custom Mode).
- **Characters**: 5 playable characters (Ironclad, Silent, Regent, Necrobinder, Defect).
- **Compendium**: 4 list pages (Cards, Relics, Potions, Events).
- **Ancients**: 8 ancient deities.
- **Acts**: 4 game acts.

Only 2 ns=0 links appear on the main page (`Slay the Spire Wiki`, `Editor Portal`), both navigational.

### List Pages (e.g., `Cards_List`)

- Top ambox notices distinguishing StS2 from StS1.
- JS-driven card grid (`#cardsContainer`) with data attributes:
  - `data-rarity`, `data-type`, `data-color`, `data-canupgrade`, `data-multiplayer`
- Each card box contains 4 image variants (base / upgraded / beta / beta-upgraded).
- Card text with dual descriptions (`desc-base` / `desc-upg`).
- Interactive toggles for "Upgraded" and "Beta Art".
- Keyword links use `keyword-trigger inline-trigger` with `data-name` and `data-sequel="2"`.

### Entity Pages (e.g., `Bash`)

- Use `DRUID infobox` template (`Category:Pages with DRUID infoboxes`).
- Standard wiki article structure with infobox + body sections.

## Discovery Flow

1. **Site initialization**: `action=query&meta=siteinfo&siprop=general|namespaces|namespacealiases`
   - Cache namespace map, confirm `ns=3000` exists.

2. **Category-based discovery**: `action=query&list=categorymembers&cmtitle=Category:...&cmnamespace=3000`
   - `Category:Cards` → all StS2 cards
   - `Category:Relics` → all StS2 relics
   - `Category:Potions` → all StS2 potions
   - `Category:Events` → all StS2 events
   - `Category:Bosses` → all StS2 bosses
   - `Category:Game Mechanics` → mechanic pages
   - Shared categories (e.g. `Category:Cards`) contain both StS1 (ns=0) and StS2 (ns=3000); the `cmnamespace=3000` filter is mandatory.

3. **Seed pages** (optional, for coverage validation):
   - Main page links provide high-value navigation seeds.
   - `Special:AllPages` can be used for gap analysis.

4. **Normalization**: `action=query&titles=...&redirects=1`
   - Resolves `normalized` and `redirects` to canonical titles.
   - Deduplicate by `pageid`.

## Content Acquisition Flow

### Primary: `action=parse`

Request:
```
action=parse&page=Slay_the_Spire_2:TITLE&prop=text|categories|links|sections|displaytitle
```

Extract:
- `displaytitle`: Human-readable title.
- `text`: Parsed HTML body (`mw-parser-output` wrapper).
- `categories`: Page categories for classification.
- `links`: Outgoing wiki links for graph expansion.
- `sections`: Section structure for TOC and chunking.

### Fallback: `prop=revisions` (wikitext)

If parse HTML is insufficient:
```
action=query&prop=revisions&rvprop=content&rvslots=main&titles=...
```

### HTML Page Fallback (last resort)

If API is unavailable, Scrapling `fetch` with `network_idle=true` can attempt the HTML page, but expect Cloudflare challenge on article URLs. Escalate to `scrapling-stealthy-fetch` or `chrome-devtools-mcp` if needed.

## Extraction Flow

1. **Discovery**: Build candidate list from `categorymembers` + `cmnamespace=3000`.
2. **Metadata**: `prop=info|categories` to confirm `ns=3000`, page length, last revision.
3. **Content**: `action=parse` for each candidate.
4. **Cleaning**:
   - Remove `mw-editsection` links.
   - Handle or remove TOC.
   - Handle ambox / hatnote notices.
   - Preserve infobox structure.
   - Normalize image URLs (`/images/thumb/...` → full or keep thumb).
   - Convert keyword-trigger links to internal wiki links.
5. **Classification**:
   - Entity page: title in `Category:Cards|Relics|Potions|Events|Bosses`
   - List page: title ends in `*_List`
   - Mechanic page: title in `Category:Game Mechanics`
   - Character/Act/Ancient: title matches known set
6. **Output**: Markdown with frontmatter (title, categories, pageid, canonical_title, source_url).

## Known Issues

- **Cloudflare on HTML pages**: Direct requests to `/wiki/Slay_the_Spire_2:*` return 403 with `cf-mitigated: challenge`. API endpoints bypass this.
- **Cross-namespace categories**: `Category:Cards` contains both StS1 (ns=0) and StS2 (ns=3000) pages. The `cmnamespace` parameter is the only reliable filter.
- **Custom namespace in links**: `action=parse` links list `ns=3000` for StS2 targets and `ns=0` for StS1 targets. Use `ns` field to filter graph expansion.
- **Image variants**: Card list pages contain 4 image states per card (base, upgraded, beta, beta-upgraded). Extraction should pick the appropriate variant or preserve all.
- **No custom anti-crawl mechanism**: API calls do not require authentication or special headers beyond a reasonable `User-Agent`. Standard rate limiting applies.

## Evidence

- Siteinfo: `api.php?action=query&meta=siteinfo&siprop=general|namespaces|namespacealiases` — validated 2026-05-07.
- Parse (Main): `api.php?action=parse&page=Slay_the_Spire_2:Main` — validated 2026-05-07.
- Parse (Cards List): `api.php?action=parse&page=Slay_the_Spire_2:Cards_List` — validated 2026-05-07.
- Category (Cards, ns=3000): `api.php?action=query&list=categorymembers&cmtitle=Category:Cards&cmnamespace=3000` — validated 2026-05-07.
- Page categories (Bash): `api.php?action=query&prop=categories&titles=Slay_the_Spire_2:Bash` — validated 2026-05-07.
- HTML challenge: Direct curl to `/wiki/Slay_the_Spire_2:Bash` returned 403 with cf-mitigated header — validated 2026-05-07.
- Reports: `reports/2026-05-07-explore-slaythespire-wiki-gg-wiki-slay-the-spire-2-main.md`.
