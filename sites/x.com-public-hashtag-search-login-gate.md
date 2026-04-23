# x.com Public Hashtag/Search Login-Gate Note

## Scope

- Domain: `x.com`
- Paths validated:
  - `/hashtag/StreetFighter6?src=hashtag_click`
  - `/search?q=%23StreetFighter6&src=typed_query&f=live`
  - `/search?q=%23sf6_ingrid&src=typed_query`
- Date: `2026-03-21`

## Observed Behavior

- Managed `chrome-devtools-mcp` browsing reaches `200` document responses, but runtime immediately lands on:
  - `/i/flow/login?redirect_after_login=...`
- Page title becomes `登录 X / X`.
- Accessibility snapshot exposes signup/login modal only.
- Response shell contains `window.__INITIAL_STATE__` with empty tweet entities:
  - `"tweets":{"entities":{},"errors":{},"fetchStatus":{}}`

## Extraction Impact

- No stable extraction of hashtag or live-search timeline body in this mode.
- Useful output is diagnostic-only (login gate signals, redirect target, shell metadata).

## Recommended Routing

- Try Scrapling first for grab-first attempts, including CDP-attached session reuse when a current browser session is available.
- If Scrapling is redirected to `/i/flow/login?...` and an already-open authenticated tab exists, switch to specialist path:
  - repo-local `chrome-cdp` on the approved authenticated Chrome tab.
- Default boundary remains read-only unless user broadens scope.

## Notes From The 2026-04-23 Authenticated Run

Observed on the approved `#sf6_ingrid` search page:

- Scrapling attached to the current Chrome debugging endpoint through CDP, but fetching the target URL still redirected to `x.com/i/flow/login?...`
- The already-open live tab itself remained authenticated and readable
- `chrome-cdp` confirmed page title `(4) #sf6_ingrid - Search / X`, URL stability, visible results, and account marker `Wang Nan @nantas`
- For this domain, Scrapling-first is still the right opening move, but current-session continuity can require immediate `chrome-cdp` fallback

## Artifacts (2026-03-21 run)

- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-hashtag-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-hashtag-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-search-live-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-search-live-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-shell-signals.txt`

## Artifacts (2026-04-23 run)

- `/Users/nantasmac/projects/agentic/chrome-agent/reports/2026-04-23-x-sf6-ingrid-authenticated-evaluation.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/reports/2026-04-23-x-sf6-ingrid-cdp.png`
