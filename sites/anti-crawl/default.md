---
id: default
protection_type: none
sites: []
detection:
  http:
    status_codes: []
  page_content:
    has_content: true
engine_sequence:
  - engine: scrapling-get
    purpose: primary
  - engine: scrapling-fetch
    purpose: primary
    config:
      network_idle: true
  - engine: scrapling-stealthy-fetch
    purpose: fallback
  - engine: chrome-devtools-mcp
    purpose: diagnostic
success_signals:
  page_content:
    has_content: true
failure_signals:
  page_content:
    dom_markers: []
  http:
    status_codes: [403, 429]
---

## Overview

The default strategy is used when no known protection signals are detected and no site strategy matches. It encodes the canonical Scrapling-first escalation chain for simple, unprotected pages.

## Engine Sequence Rationale

- `scrapling-get` is tried first since there are no known protection signals and the page is expected to be simple static HTML.
- `scrapling-fetch` is the first fallback when JS rendering is needed.
- `scrapling-stealthy-fetch` handles cases where unexpected anti-bot protection is encountered.
- `chrome-devtools-mcp` is the diagnostic fallback when all Scrapling engines fail.

## Known Quirks

- This strategy is intentionally generic. If a site consistently requires escalation beyond `scrapling-get`, consider creating a dedicated site strategy.
- The `sites` field is empty because this strategy is not bound to any domain — it applies to all unmatched URLs.

## Evidence

- Defined as part of Phase 3 (2026-04-28) strategy standardization.
- Engine identifiers and escalation order follow the `engine-contracts` spec canonical chain.
