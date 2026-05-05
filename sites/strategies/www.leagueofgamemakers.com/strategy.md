---
domain: www.leagueofgamemakers.com
description: Self-hosted WordPress blog for board game design articles
protection_level: low
anti_crawl_refs: []
engine_preference:
  preferred: scrapling-get
  reason: "WordPress renders full article HTML server-side; no JavaScript or stealth required"
structure:
  pages:
    - id: single_post
      label: WordPress Single Post
      url_pattern: /:year/:month/:slug/
      url_example: https://www.leagueofgamemakers.com/2014/09/using-game-theory-to-design-games/
      type: static_article
      content_type: article_body
      pagination: none
      links_to:
        - target: single_post
          selector: "a[href*='/20']"
        - target: category_archive
          selector: "a[href^='https://www.leagueofgamemakers.com/category/']"
        - target: tag_archive
          selector: "a[href^='https://www.leagueofgamemakers.com/tag/']"
        - target: author_archive
          selector: "a[href^='https://www.leagueofgamemakers.com/author/']"
      requires_auth: false
    - id: category_archive
      label: WordPress Category Archive
      url_pattern: /category/:slug/
      url_example: https://www.leagueofgamemakers.com/category/technical/
      type: static_list
      content_type: post_list
      pagination:
        mechanism: url_path
        pattern: /page/:n/
      links_to:
        - target: single_post
          selector: "article a[rel='bookmark']"
      requires_auth: false
    - id: tag_archive
      label: WordPress Tag Archive
      url_pattern: /tag/:slug/
      url_example: https://www.leagueofgamemakers.com/tag/game-theory/
      type: static_list
      content_type: post_list
      pagination:
        mechanism: url_path
        pattern: /page/:n/
      links_to:
        - target: single_post
          selector: "article a[rel='bookmark']"
      requires_auth: false
    - id: author_archive
      label: WordPress Author Archive
      url_pattern: /author/:slug/
      url_example: https://www.leagueofgamemakers.com/author/thomas-jolly/
      type: static_list
      content_type: post_list
      pagination:
        mechanism: url_path
        pattern: /page/:n/
      links_to:
        - target: single_post
          selector: "article a[rel='bookmark']"
      requires_auth: false
    - id: blog_index
      label: Blog Index
      url_pattern: /blog/
      url_example: https://www.leagueofgamemakers.com/blog/
      type: static_list
      content_type: post_list
      pagination:
        mechanism: url_path
        pattern: /page/:n/
      links_to:
        - target: single_post
          selector: "article a[rel='bookmark']"
      requires_auth: false
  entry_points:
    - single_post
    - category_archive
    - tag_archive
    - author_archive
    - blog_index
extraction:
  image_handling:
    attribute: src
    fallback: href
    output_format: markdown_inline
  cleanup:
    - strip_navigation_duplicates
    - strip_comment_form
    - strip_related_posts_if_partial
---

## Overview

`www.leagueofgamemakers.com` is a self-hosted WordPress blog covering board game design topics. The site serves fully rendered HTML for all article and archive pages. No client-side JavaScript rendering or anti-crawl protections are present.

## CMS Identification

- **Media path**: `/wp-content/uploads/2014/09/` (classic WordPress upload directory structure)
- **Author archives**: `/author/thomas-jolly/`
- **Category archives**: `/category/technical/`
- **Tag archives**: `/tag/boardgames/`
- **Permalink format**: `/:year/:month/:slug/` (WordPress default pretty permalinks)
- **Comment system**: Standard WordPress comment form (`Leave a Reply`)

## Page Structure

### Single Post (`/:year/:month/:slug/`)

- Full article rendered server-side in static HTML.
- Metadata: title, author with avatar, publish date, categories, tags.
- Body: mixed text, inline images, heading hierarchy.
- Images: often served via lazy-load SVG data-URI placeholders; original image URL may be in parent anchor `href` pointing to `/wp-content/uploads/`.
- Navigation: previous/next post links at bottom.
- Related Posts section with thumbnail, author, date, excerpt.
- Comment form present but not required for content extraction.

### Category Archive (`/category/:slug/`)

- Lists posts belonging to a category.
- Pagination via `/page/N/` appended to category URL.
- Each entry links to single post.

### Tag Archive (`/tag/:slug/`)

- Same structure as category archive, grouped by tag.
- Pagination via `/page/N/`.

### Author Archive (`/author/:slug/`)

- Lists posts by author.
- Pagination via `/page/N/`.

### Blog Index (`/blog/`)

- Chronological post listing.
- Pagination via `/blog/page/N/`.

## Extraction Flow

1. Fetch target URL with `scrapling-get`.
2. For single post:
   - Extract title from first `h1`.
   - Extract author from `.author a` or `a[href^='/author/']`.
   - Extract publish date from time element or post meta.
   - Extract body content in DOM order, preserving heading hierarchy.
   - For images: prefer `href` on enclosing anchor if `src` is a data-URI placeholder; otherwise use `src`.
   - Strip navigation duplicates, comment forms, and related posts if they fragment the article.
3. For archive/list pages:
   - Extract all post links (`article a[rel='bookmark']`).
   - Follow pagination links (`/page/N/`) until empty or bounded.
   - Recursively fetch each linked single post.

## Known Issues

- Image `src` attributes frequently use base64-encoded SVG placeholders (lazy loading). The actual image URL is often on the parent anchor `href` pointing to `/wp-content/uploads/`.
- Navigation menu appears twice in DOM (desktop + mobile), causing duplicate links in raw extraction.
- Comment form and related posts appear after article body; they should be excluded from article extraction.
- No RSS/JSON API endpoints observed; crawling must follow HTML links.

## Evidence

- 2026-05-05: `fetch` via `scrapling-get` returned full article HTML with title, author, date, categories, tags, and body.
- 2026-05-05: Content markdown confirmed WordPress permalink, `/wp-content/uploads/`, `/author/`, `/category/`, `/tag/` URL patterns.
- 2026-05-05: `explore` flagged `strategy_gap`; this strategy was authored from the fetch evidence.
