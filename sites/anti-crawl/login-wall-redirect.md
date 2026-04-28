---
id: login-wall-redirect
protection_type: login_wall
sites:
  - x.com
detection:
  http:
    status_codes: [200]
  page_content:
    titles:
      - "登录 X"
      - "Login"
    url_patterns:
      - "/i/flow/login"
    has_content: false
    dom_markers:
      - 'a[href="/login"]'
  network:
    empty_api_entities: "window.__INITIAL_STATE__.tweets.entities"
engine_priority:
  - engine: scrapling-fetch
    rank: 1
    config:
      network_idle: true
  - engine: chrome-devtools-mcp
    rank: 2
success_signals:
  page_content:
    has_content: true
    titles:
      - "!@登录"
      - "!@Login"
failure_signals:
  page_content:
    url_patterns:
      - "/i/flow/login"
    has_content: false
---

## Overview

Login wall redirect is a protection mechanism where unauthenticated users are redirected to a login page. The HTTP response returns 200 but the DOM is replaced with a login form or signup prompt.

## Engine Priority Rationale

- Starts with `scrapling-fetch` (or session reuse) since some pages may load content without redirect if the session is recognized.
- Falls back to `chrome-devtools-mcp` for diagnostic evidence (screenshot, network redirect, DOM snapshot).

## Known Quirks

- x.com public tweet detail pages (`/<user>/status/<id>`) load content fine without authentication, but hashtag/search pages (`/hashtag/...`, `/search?q=...`) redirect to login.
- Scrapling session reuse does not seem to maintain authentication for x.com across different URLs.
- Detection signal: response page contains `window.__INITIAL_STATE__` with empty `tweets.entities` object.
- Even when Chrome DevTools MCP confirms a 200 HTTP response, the page can still be the login shell.

## Evidence

- Validated on x.com hashtag search (`/hashtag/StreetFighter6`, 2026-03-21).
- See `reports/2026-03-21-sf6-x-shell-signals.txt` for shell detection evidence.
- Authenticated run (2026-04-23) confirmed that live-session continuation remains possible, but that path is governed outside this anti-crawl priority file.
