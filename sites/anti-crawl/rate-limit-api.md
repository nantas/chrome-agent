---
id: rate-limit-api
protection_type: rate_limit
sites:
  - fanbox.cc
detection:
  http:
    status_codes: []
  page_content:
    titles: []
    dom_markers: []
    has_content: false
  network:
    empty_api_entities: ""
engine_sequence:
  - engine: scrapling-fetch
    config:
      network_idle: true
    purpose: primary
  - engine: chrome-devtools-mcp
    purpose: diagnostic
success_signals:
  page_content:
    has_content: true
failure_signals:
  page_content:
    dom_markers: []
  http:
    status_codes: []
---

## Overview

API rate limiting limits the number of requests within a time window. When triggered, browser `fetch()` API calls return `TypeError: Failed to fetch` with no HTTP response. Retries will not help until the cooldown period expires.

## Engine Sequence Rationale

- `scrapling-fetch` is the primary engine since rate-limited content requires browser rendering.
- `chrome-devtools-mcp` is the diagnostic fallback to confirm rate limiting via network panel evidence.

## Known Quirks

- FANBOX `api.fanbox.cc` rate limit characteristics (observed 2026-04-04):
  - Burst threshold: ~80-100 calls within 10 minutes.
  - Recovery time: ~2.5-3 hours.
  - Safe sustained rate: ~8-10 calls per minute.
  - Error symptom: `TypeError: Failed to fetch` — no HTTP status code returned.
  - Rate limit is per-session; cooldown affects all subsequent requests.
- API calls must go through the browser (Cloudflare blocks direct HTTP requests).
- The `page` and `offset` parameters for FANBOX post list API do not work — DOM scraping is the reliable pagination method.

## Mitigation

- Minimum 3s delay between API calls; 5s for long batch operations.
- Checkpoint progress after each successful call for resumable runs.
- Stop immediately on `Failed to fetch` — continue only after cooldown.
- Monitor for email verification redirects which may appear as unrelated failures.

## Evidence

- Validated on fanbox.cc (2026-04-04 batch download run).
- Two rate limit events recorded: ~03:42 and ~06:38.
- See `sites/strategies/fanbox.cc/strategy.md` for full rate limit mitigation details.
