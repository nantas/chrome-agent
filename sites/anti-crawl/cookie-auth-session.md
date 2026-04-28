---
id: cookie-auth-session
protection_type: cookie_auth
sites:
  - fanbox.cc
detection:
  http:
    status_codes: [200]
  page_content:
    titles:
      - "!@投稿列表"
    dom_markers:
      - 'a[href*="/email/reactivate"]'
    url_patterns:
      - "/email/reactivate"
    has_content: false
engine_priority:
  - engine: chrome-cdp
    rank: 1
success_signals:
  page_content:
    has_content: true
    titles:
      - "投稿列表"
      - "pixivFANBOX"
failure_signals:
  page_content:
    url_patterns:
      - "/email/reactivate"
    dom_markers:
      - 'a[href*="/email/reactivate"]'
  network:
    empty_api_entities: "isMailAddressOutdated"
---

## Overview

Cookie-based authentication requires a valid session cookie (e.g., `FANBOXSESSID`) to access protected content. Without the cookie, requests may redirect to login or show a shell page.

## Engine Priority Rationale

- `chrome-cdp` is the primary path for authenticated sessions — it reuses the user's live browser session with valid cookies.

## Known Quirks

- FANBOX also enforces email re-verification — if `isMailAddressOutdated` is true, accessing post details redirects to `/email/reactivate`.
- The `FANBOXSESSID` cookie is httpOnly and secure, making it inaccessible to JavaScript.
- Cookie extraction for download auth uses CDP `Network.getCookies` with `{"urls":["https://downloads.fanbox.cc"]}`.
- Required headers for programmatic download: `Cookie`, `Referer: https://www.fanbox.cc/`, standard Chrome UA.

## Evidence

- Validated on fanbox.cc (2026-04-04 batch download run).
- Single file download test confirmed `FANBOXSESSID` cookie enables curl-based file download.
- See `sites/strategies/fanbox.cc/strategy.md` for full site strategy details.
