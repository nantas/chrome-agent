---
domain: boardgamegeek.com
description: BoardGameGeek browse listing and detail pages for board game mechanics
protection_level: high
anti_crawl_refs: []
engine_preference:
  preferred: scrapling-stealthy-fetch
  reason: "BGG returns HTTP 403 on scrapling-get; scrapling-stealthy-fetch with stealth features is needed to bypass bot detection"
structure:
  pages:
    - id: mechanic_browse
      label: Board Game Mechanic Browse
      url_pattern: /browse/boardgamemechanic
      url_example: https://boardgamegeek.com/browse/boardgamemechanic
      type: dynamic_list
      anti_crawl_refs: []
      engine_preference:
        preferred: scrapling-stealthy-fetch
        reason: "BGG browse page blocks simple HTTP fetches with 403"
      content_type: list
      pagination:
        mechanism: url_parameter
        parameter: page
        start: 1
      links_to:
        - target: mechanic_detail
          selector: "a[href*='/boardgamemechanic/']"
      requires_auth: false
    - id: mechanic_detail
      label: Board Game Mechanic Detail
      url_pattern: /boardgamemechanic/:id/:slug
      url_example: https://boardgamegeek.com/boardgamemechanic/2073/acting
      type: dynamic_content
      anti_crawl_refs: []
      engine_preference:
        preferred: scrapling-stealthy-fetch
        reason: "BGG detail pages also blocked by bot detection"
      content_type: article_with_attachments
      pagination: none
      links_to: []
      requires_auth: false
  entry_points:
    - mechanic_browse
extraction:
  image_handling:
    attribute: src
    output_format: markdown_inline
---

## Overview

BoardGameGeek's browse/boardgamemechanic page lists all board game mechanics with their names, descriptions, and related game counts. Each mechanic links to a detail page with full description, official links, and top games list. Both page types are protected by bot detection returning HTTP 403 for non-stealth requests.

## Page Structure

### Mechanic Browse (`/browse/boardgamemechanic`)

- List-style page with all mechanics in a two-column table.
- Each row links to a mechanic detail page (`/boardgamemechanic/:id/:slug`).
- BGG returns HTTP 403 for `scrapling-get` — requires stealthy browser engine.
- Pagination parameter (?page=N) returns duplicate content; all mechanics on page 1.

### Mechanic Detail (`/boardgamemechanic/:id/:slug`)

- Detail page for a single mechanic.
- Contains: mechanic name, fan count, description paragraph, official links, top games list (rank, fans).
- Tab navigation: Overview (default), Linked Games, Forums, Images, Videos, GeekLists, Other Links.

## Extraction Flow

1. Use `scrapling-stealthy-fetch` with the `/browse/boardgamemechanic` URL.
2. Extract all mechanic links from the table.
3. For each mechanic link, fetch detail page with `scrapling-stealthy-fetch`.
4. Extract: mechanic name, description, top games list.
5. Save each detail as a separate output.

## Known Issues

- First tried `scrapling-get` (2026-05-02): HTTP 403, empty content.
- `scrapling-stealthy-fetch` is the recommended first engine.
- Pagination parameter returns duplicate content; no need to paginate.
- 192 detail pages may take significant time to crawl.

## Evidence

- 2026-05-02: `fetch` via `scrapling-get` returned 403 with 0-byte `content.md`.
- 2026-05-02: `fetch` via `scrapling-stealthy-fetch` returned full browse list and acting detail page.
- 2026-05-02: `explore` confirmed no site strategy existed before this creation.
