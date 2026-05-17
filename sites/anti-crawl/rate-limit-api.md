---
id: rate-limit-api
protection_type: rate_limit
sites:
  - fanbox.cc
  - slaythespire.wiki.gg
detection:
  http:
    status_codes:
      - 429
  page_content:
    titles: []
    dom_markers: []
    has_content: false
  network:
    empty_api_entities: ""
engine_priority:
  - engine: mediawiki-api
    rank: 0
    config:
      rate_limit_tier: strict
  - engine: scrapling-fetch
    rank: 1
    config:
      network_idle: true
  - engine: chrome-devtools-mcp
    rank: 2
success_signals:
  page_content:
    has_content: true
failure_signals:
  page_content:
    dom_markers: []
  http:
    status_codes:
      - 429
rate_limit_tiers:
  default:
    concurrency: 1
    batch_delay_ms: 500
    retry:
      max_retries: 3
      initial_delay_sec: 1.0
      backoff_multiplier: 2.0
      max_delay_sec: 60.0
      jitter: true
  strict:
    concurrency: 1
    batch_delay_ms: 800
    retry:
      max_retries: 5
      initial_delay_sec: 1.0
      backoff_multiplier: 2.5
      max_delay_sec: 60.0
      jitter: true
  very-strict:
    concurrency: 1
    batch_delay_ms: 3000
    retry:
      max_retries: 5
      initial_delay_sec: 2.0
      backoff_multiplier: 2.0
      max_delay_sec: 60.0
      jitter: true
---

## Overview

API rate limiting limits the number of requests within a time window. When triggered, browser `fetch()` API calls return `TypeError: Failed to fetch` with no HTTP response. Retries will not help until the cooldown period expires.

MediaWiki API rate limiting presents differently: the endpoint returns HTTP 429 with a `Retry-After` header (when available), and the response body contains a JSON error object. Unlike browser `fetch()` failures, MediaWiki 429s are recoverable with backoff and do not require a multi-hour cooldown.

## Engine Priority Rationale

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

## MediaWiki API Rate Limiting

- **Detection**: HTTP 429 status code on `action=query` or `action=parse` endpoints.
- **Symptom**: JSON response with `{"error":{"code":"ratelimited","info":"..."}}`.
- **Recovery**: Exponential backoff with jitter; no extended cooldown required.
- **Observed thresholds** (slaythespire.wiki.gg, 2026-05-07):
  - `concurrency=5` with `batch_delay_ms=40` → mass 429 failures within first 100 pages.
  - `concurrency=1` with `batch_delay_ms=800` → ~0.5% failure rate across 1298 pages.
- **Recommended tier**: `strict` for MediaWiki sites with unknown rate limit thresholds.

## Evidence

- Validated on fanbox.cc (2026-04-04 batch download run).
- Two rate limit events recorded: ~03:42 and ~06:38.
- See `sites/strategies/fanbox.cc/strategy.md` for full rate limit mitigation details.
- Validated on slaythespire.wiki.gg (2026-05-07): 1291/1298 pages succeeded with `strict` tier parameters.
- See `sites/strategies/slaythespire.wiki.gg/strategy.md` for MediaWiki API rate limit configuration.
