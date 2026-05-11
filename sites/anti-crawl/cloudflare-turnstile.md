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
  - engine: cloakbrowser-fetch
    rank: 1
    config:
      headless: true
      wait_until: domcontentloaded
      timeout: 30
      # CloakBrowser auto-resolves Turnstile in 6–15s via source-level fingerprint patches
      # No manual solve step needed — wait for title to change away from challenge indicators
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

- Starts with `cloakbrowser-fetch` because its 57 C++ source-level Chromium fingerprint patches bypass Cloudflare Turnstile automatically in headless mode (no manual solve step needed).
- `chrome-devtools-mcp` is the diagnostic fallback when `cloakbrowser-fetch` cannot resolve the challenge within the timeout, providing screenshot and DOM evidence for manual analysis.

## Known Quirks

- The Turnstile widget may be a checkbox challenge (user clicks "I am human") or an invisible challenge (solved automatically by the browser environment).
- Invisible challenges are more likely to succeed with `cloakbrowser-fetch` because the patched Chromium binary provides native-level fingerprint stealth undetectable by JavaScript fingerprinting.
- Some sites may present a JS challenge interstitial (non-Turnstile) — those are covered by `cloudflare_challenge` protection type.

## Evidence

- Validated on `wiki.supercombo.gg/w/Street_Fighter_6` (2026-03-21).
- CloakBrowser `cloakbrowser-fetch` with `wait_until=domcontentloaded` auto-resolves Turnstile and returns full article content (~23,000 chars in ~14s).
- See `reports/2026-03-21-sf6-supercombo-challenge-signals.txt` for challenge detection signals.
