# x.com Public Tweet Note

## Scope

- Domain: `x.com`
- Path validated: `/<user>/status/<id>` (public tweet detail page)
- Date: `2026-04-28`
- Method: Scrapling `fetch` (Playwright, SPA rendering)

## Validated Behavior

- Scrapling `fetch` with `network_idle=true` successfully rendered the tweet detail page
- The following content was extracted:
  - **Author**: display name + @handle
  - **Tweet text**: full text content including line breaks
  - **Media links**: video thumbnail / image URLs preserved in output
  - **Engagement data**: reply count, repost count, like count visible
  - **Timestamp**: post date and time
- Login gate was detected at the bottom of the page (registration prompt) but did not prevent tweet content loading
- The page URL remained the target tweet URL (no redirect to `/i/flow/login`)

## Extraction Pattern

For public tweet pages, Scrapling `fetch` with `network_idle=true` or `wait_selector` can extract tweet content:

```
fetch(url, { network_idle: true })
```

## Known Limitations

- The page renders a registration/login prompt at the bottom, but tweet content is loaded above it
- If x.com changes their frontend, the extraction behavior may change
- For authenticated tweet content (e.g., followed users only), `chrome-cdp` with an approved session would be needed
- The tweet ID `2048939923580043450` was successfully fetched on 2026-04-28

## Content Retrieval Path

1. Use Scrapling `fetch` with `network_idle=true` for tweet detail page
2. Extract: author name and handle, tweet text, media links, engagement metrics
3. Return content directly

## Page Analysis Path

1. Use Scrapling `fetch` first
2. If content is incomplete or blocked by login wall, escalate to `chrome-devtools-mcp` for diagnostic evidence
3. If an approved authenticated Chrome tab exists, escalate to `chrome-cdp`
