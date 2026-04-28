---
id: cloudflare-turnstile
protection_type: cloudflare_turnstile
sites:
  - wiki.supercombo.gg
detection:
  http:
    status_codes: [403]
  page_content:
    titles:
      - "Just a moment..."
      - "请稍候…"
    dom_markers:
      - cf-turnstile
      - "#challenge-form"
    has_content: false
engine_priority:
  - engine: scrapling-stealthy-fetch
    rank: 1
    config:
      solve_cloudflare: true
      network_idle: true
  - engine: chrome-devtools-mcp
    rank: 2
success_signals:
  page_content:
    has_content: true
    titles:
      - "!@Just a moment"
      - "!@请稍候"
failure_signals:
  page_content:
    dom_markers:
      - cf-turnstile
  http:
    status_codes: [403]
---

## Overview

Cloudflare Turnstile is an anti-bot challenge that presents a checkbox or invisible verification widget. When triggered, the page returns HTTP 403 with a minimal challenge shell — the real content is only accessible after passing the challenge.

## Engine Priority Rationale

- Starts with `scrapling-stealthy-fetch` because `scrapling-get` and `scrapling-fetch` cannot solve Turnstile challenges. The stealthy fetcher's browser fingerprint spoofing and `solve_cloudflare` option are required.
- `chrome-devtools-mcp` is the diagnostic fallback when stealthy-fetch cannot complete the challenge, providing screenshot and DOM evidence for manual analysis.

## Known Quirks

- The Turnstile widget may be a checkbox challenge (user clicks "I am human") or an invisible challenge (solved automatically by the browser environment).
- Invisible challenges are more likely to succeed with `scrapling-stealthy-fetch` because the browser environment is fully emulated.
- Some sites may present a JS challenge interstitial (non-Turnstile) — those are covered by `cloudflare_challenge` protection type.

## Evidence

- Validated on `wiki.supercombo.gg/w/Street_Fighter_6` (2026-03-21).
- Scrapling `stealthy-fetch` with `--solve-cloudflare` successfully reached article content.
- See `reports/2026-03-21-sf6-supercombo-challenge-signals.txt` for challenge detection signals.
