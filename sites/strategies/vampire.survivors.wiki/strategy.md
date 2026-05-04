---
domain: vampire.survivors.wiki
description: Weird Gloop hosted MediaWiki for Vampire Survivors
protection_level: low
anti_crawl_refs: []
engine_preference:
  preferred: scrapling-get
  fallback: obscura-fetch
structure:
  pages:
    - id: wiki_category
      label: MediaWiki Category Page
      url_pattern: /wiki/Category:*
      url_example: https://vampire.survivors.wiki/wiki/Category:Weapons
      type: static_page
      content_type: link_list
      pagination: none
      links_to:
        - target: wiki_article
          selector: "#mw-content-text a[href*=\"/w/\"]"
      requires_auth: false
    - id: wiki_article
      label: MediaWiki Article Page
      url_pattern: /w/:title
      url_example: https://vampire.survivors.wiki/w/Whip
      type: static_article
      content_type: article_body
      pagination: none
      links_to: []
      requires_auth: false
  entry_points:
    - wiki_category
api:
  platform: mediawiki
  base_url: "https://vampire.survivors.wiki/api.php"
  capabilities:
    - page_list
    - category_lookup
    - wikitext_parse
  taxonomy:
    list_pages:
      Weapons: "Weapons"
      Passive_Items: "Passive_Items"
      Arcanas: "Arcanas"
      Characters: "Characters"
      Stages: "Stages"
      PowerUps: "PowerUps"
      Pickups: "Pickups"
    category_filters:
      - "Disambiguations"
  filename:
    replacements:
      "/": "_"
      ":": "_"
  output:
    frontmatter_fields: []
extraction:
  selectors:
    title: "#firstHeading"
    body: "#mw-content-text"
  image_handling:
    attribute: src
    output_format: markdown_inline
  cleanup:
    - strip_footer
    - strip_skip_links
    - strip_json_data
    - strip_empty_parens
    - convert_nested_images
    - normalize_internal
    - strip_category_links
    - normalize_infobox
    - fix_separators
---

## Overview

`vampire.survivors.wiki` is a Weird Gloop-hosted MediaWiki instance for the game Vampire Survivors. Pages are server-side rendered static HTML with no dynamic loading requirements for article content. The site uses MediaWiki 1.45.x with the Vector skin (or similar Weird Gloop customisation).

## Page Structure

- **Category pages** (`/wiki/Category:<name>`): List articles belonging to a category. These are the primary entry points for crawl traversal. Internal wiki links to articles appear in `#mw-content-text`.
- **Article pages** (`/wiki/<title>`): Standard MediaWiki articles with an infobox, body content, and footer navigation. Content is rendered server-side.

## Extraction Flow

1. Open a category or article URL.
2. Verify page identity with `#firstHeading` title and URL pattern.
3. Extract body from `#mw-content-text`.
4. Walk DOM in reading order — emit non-empty text blocks.
5. For images: extract `src` attribute, emit as inline Markdown (`![](url)`).
6. Apply MediaWiki cleanup rules in order: navigation → template → link → table.

## Known Issues

- **Crawl engine selector limitation:** The chrome-agent crawl engine parses `links_to` selectors using only simple `href*="..."` or `href="..."` extraction. Complex CSS selectors (e.g. `:not()`, `^=`) are not supported. The current selector `href*="/w/"` matches all `/w/` links, including project pages (`Vampire_Survivors_Wiki:*`) and special pages (`Special:*`). Bounded traversal (`max_pages`) prevents runaway crawling, but some non-article pages may be visited.
- Scrapling output may expose hidden template artifacts (JSON data rows from Scribunto modules, empty parentheses from empty template parameters).
- Infobox tables often have many empty columns; normalize to `| key | value |` format for readability.
- Nested image links (`[![](thumb)](page)`) should be flattened to direct image references.
- Category links (`[[Category:...]]`) and internal link title residues (`"title")`) appear in Scrapling text output and must be cleaned.
- DPL wikitext artifacts are not common on this site but may appear on pages using DynamicPageList.

## Evidence

- Validated on 416-page bulk scrape (2026-04).
- Scrapling `get` successfully retrieved article body and inline images without JavaScript rendering.
- balatrowiki.org (also Weird Gloop MediaWiki 1.45.3) confirmed 79% rule reuse rate; 2 site-specific differences noted in `docs/patterns/mediawiki-extraction.md`.
