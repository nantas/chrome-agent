---
domain: balatrowiki.org
description: Weird Gloop hosted MediaWiki for Balatro game wiki
protection_level: low
anti_crawl_refs: []
engine_preference:
  preferred: scrapling-get
  fallback: obscura-fetch
structure:
  pages:
    - id: wiki_article
      label: MediaWiki Article Page
      url_pattern: /w/:title
      url_example: https://balatrowiki.org/w/Joker
      type: static_article
      content_type: article_body
      pagination: none
      links_to:
        - target: wiki_article
          selector: "#mw-content-text a[href*=\"/w/\"]"
      requires_auth: false
  entry_points:
    - wiki_article
extraction:
  selectors:
    title: "#firstHeading"
    body: "#mw-content-text"
  image_handling:
    attribute: src
    output_format: markdown_inline
  cleanup:
    - strip_footer
    - strip_edit_links
    - strip_skip_links
    - strip_dpl_wikitext
    - strip_empty_parens
    - convert_nested_images
    - normalize_internal
    - strip_category_links
    - normalize_infobox
    - fix_separators
---

## Overview

`balatrowiki.org` is a Weird Gloop-hosted MediaWiki instance for the game **Balatro**, a poker-inspired roguelike deck builder. Pages are server-side rendered static HTML with no dynamic loading requirements for article content. The site uses MediaWiki 1.45.3 with the Vector skin.

## Page Structure

- **Article pages** (`/w/<title>`): All content pages share the same URL structure. This includes both list/overview pages (e.g., `/w/Jokers`) and individual item pages (e.g., `/w/Joker`). Content is rendered server-side in `#mw-content-text`.
- **Category pages** (`/w/Category:<name>`): Standard MediaWiki category listings, usually linked from article pages. These are excluded from primary content extraction.
- **Special pages** (`/w/Special:*`): System pages (Recent Changes, WhatLinksHere, etc.) — non-content, excluded from extraction targets.
- **File pages** (`/w/File:*`): Image file description pages — non-content.

## Extraction Flow

1. Open a starting article URL (typically a list/overview page like `/w/Jokers`).
2. Verify page identity with `#firstHeading` title and URL `/w/` pattern.
3. Extract body from `#mw-content-text`.
4. Walk DOM in reading order — emit non-empty text blocks.
5. For images: extract `src` attribute, emit as inline Markdown (`![](url)`).
6. Apply the `balatro` cleanup profile in order:
   - **Navigation cluster**: strip_footer, strip_edit_links, strip_skip_links
   - **Template cluster**: strip_dpl_wikitext, strip_empty_parens
   - **Link cluster**: convert_nested_images, normalize_internal, strip_category_links
   - **Table cluster**: normalize_infobox, fix_separators

## Crawl Strategy

Entry points are major list/overview pages that contain dense internal links:

- `https://balatrowiki.org/w/Jokers`
- `https://balatrowiki.org/w/Decks`
- `https://balatrowiki.org/w/Poker_Hands`
- `https://balatrowiki.org/w/Card_Modifiers`
- `https://balatrowiki.org/w/Consumables`
- `https://balatrowiki.org/w/Tarot_Cards`
- `https://balatrowiki.org/w/Planet_Cards`
- `https://balatrowiki.org/w/Spectral_Cards`
- `https://balatrowiki.org/w/Vouchers`
- `https://balatrowiki.org/w/Booster_Packs`
- `https://balatrowiki.org/w/Blinds`
- `https://balatrowiki.org/w/Tags`
- `https://balatrowiki.org/w/Stakes`
- `https://balatrowiki.org/w/Achievements`
- `https://balatrowiki.org/w/Updates`
- `https://balatrowiki.org/w/Game_Mechanics`

The crawl engine follows `links_to` selectors on each visited page, traversing from list pages to individual articles. Bounded traversal (`max_pages`) prevents runaway crawling.

## Known Issues

- **Crawl engine selector limitation:** The `links_to` selector `href*="/w/"` matches all `/w/` links, including category pages (`Category:*`), special pages (`Special:*`), file pages (`File:*`), template pages (`Template:*`), and project pages (`Balatro_Wiki:*`). Bounded traversal limits total pages, but some non-article pages may be visited. Post-crawl cleanup is recommended.
- **DPL wikitext artifacts:** Pages with DynamicPageList templates (especially Jokers list page) may expose `{{hl|...}}`, `{{Chips|...}}`, `{{Mult|...}}` syntax in Scrapling output. The `balatro` profile strips these.
- **Section edit links:** Unlike vampire.survivors.wiki, balatrowiki.org shows `[edit]` and `[edit source]` links next to section headings. The `balatro` cleanup profile includes `strip_edit_links`.
- **Infobox tables:** Individual item pages (e.g., `/w/Joker`) use sparse infobox tables with many empty columns. `normalize_infobox` compresses these to `| key | value |` format.
- **Nested image links:** `[![](thumb-url)](article-url)` pattern appears frequently and is flattened by `convert_nested_images`.

## Evidence

- Validated on homepage, `/w/Jokers`, and `/w/Joker` samples (2026-05-04).
- Scrapling `get` successfully retrieved article body and inline images without JavaScript rendering.
- Content licensed under CC BY-NC-SA 3.0.
