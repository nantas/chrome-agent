# x.com Public Hashtag/Search Login-Gate Note

## Scope

- Domain: `x.com`
- Paths validated:
  - `/hashtag/StreetFighter6?src=hashtag_click`
  - `/search?q=%23StreetFighter6&src=typed_query&f=live`
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

- Keep default path as `chrome-devtools-mcp` for first-pass diagnostics.
- For content extraction beyond shell/login flow, switch to specialist path only when user approves live-session continuation:
  - repo-local `chrome-cdp` on an already-open authenticated Chrome tab.
- Default boundary remains read-only unless user broadens scope.

## Artifacts (2026-03-21 run)

- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-hashtag-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-hashtag-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-search-live-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-search-live-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-shell-signals.txt`
