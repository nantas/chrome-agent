---
domain: x.com
description: Public tweet detail and hashtag/search pages
protection_level: variable
anti_crawl_refs:
  - login-wall-redirect
structure:
  pages:
    - id: public_tweet
      label: Public Tweet Detail
      url_pattern: /:user/status/:id
      url_example: https://x.com/username/status/123456789
      type: dynamic_content
      engine_preference:
        preferred: scrapling-fetch
        reason: Public tweet detail pages are already validated on the lighter Scrapling fetch path
      content_type: article_with_attachments
      pagination: none
      links_to: []
      requires_auth: false
    - id: hashtag_search
      label: Hashtag/Search Page
      url_pattern: /hashtag/:tag
      url_example: https://x.com/hashtag/StreetFighter6
      type: search_results
      engine_preference:
        preferred: chrome-cdp
        reason: Hashtag and search pages often require authenticated live-session continuity after login-wall detection
      content_type: search_results
      pagination:
        mechanism: scroll_infinite
        trigger: Scroll down to load more results
      links_to: []
      requires_auth: true
      anti_crawl_refs:
        - login-wall-redirect
  entry_points:
    - public_tweet
    - hashtag_search
extraction:
  image_handling:
    attribute: src
    output_format: markdown_inline
---

## Overview

x.com has two structurally different page types under the same domain. Public tweet detail pages load content without authentication, while hashtag/search pages redirect to a login wall.

## Page Structure

### Public Tweet (`/:user/status/:id`)

- SPA-rendered tweet detail page.
- Content loads without authentication — no redirect to login.
- Login/registration prompt appears at the bottom but does not prevent content extraction.
- Extracted fields: author display name + @handle, tweet text (full), media links (video thumbnails/image URLs), engagement data (reply/repost/like counts), timestamp.

### Hashtag/Search (`/hashtag/:tag`, `/search?q=...`)

- Login wall: redirects to `/i/flow/login?redirect_after_login=...`
- HTTP status is 200 but DOM contains login form only.
- `window.__INITIAL_STATE__` contains empty tweet entities: `"tweets":{"entities":{},"errors":{}}`
- Scrapling session reuse does not maintain authentication across different URLs.
- An authenticated `chrome-cdp` session (user-approved) can access content.

## Extraction Flow

1. For public tweet URLs: use Scrapling `fetch` with `network_idle=true`.
2. For hashtag/search URLs: try Scrapling first; if redirected to login, switch to `chrome-cdp` with user-approved authenticated session.
3. For tweet content: extract author, text, media links, engagement metrics, timestamp.
4. Return content directly for Content Retrieval path; save report for Analysis path.

## Known Issues

- Tweet ID `2048939923580043450` was successfully fetched on 2026-04-28 via Scrapling `fetch`.
- If x.com frontend changes, extraction behavior may change.
- Authenticated-only content (e.g., followed users only) requires `chrome-cdp` with approved session.
- The `login-wall-redirect` anti-crawl strategy handles login gate detection signals.
- `engine_preference` is intentionally split per page type: public tweet detail keeps the lighter Scrapling path, while authenticated search prefers `chrome-cdp`.

## Evidence

- Public tweet: validated on x.com public tweet (2026-04-28).
- Hashtag login gate: validated on `/hashtag/StreetFighter6` (2026-03-21).
- Authenticated search: validated on `#sf6_ingrid` search with `chrome-cdp` (2026-04-23).
- Reports: `reports/2026-03-21-sf6-x-shell-signals.txt`, `reports/2026-04-23-x-sf6-ingrid-authenticated-evaluation.md`.
