# Street Fighter 6 Hard-Page Extraction Analysis (2026-03-21)

## Task

- Goal: continue prior `Street Fighter 6` knowledge collection and validate whether hard pages can be stably extracted in the `chrome-agent` workflow.
- Targets:
  - `https://x.com/hashtag/StreetFighter6?src=hashtag_click`
  - `https://x.com/search?q=%23StreetFighter6&src=typed_query&f=live`
  - `https://wiki.supercombo.gg/w/Street_Fighter_6`
- Workflow route: `Platform/Page Analysis` (deep evidence + reusable artifacts).
- Tool path: `chrome-devtools-mcp` (managed browser context), no live-session attach.

## Target Results

### 1) `x.com` hashtag page

- Result: `partial_success`
- Observed URL after load: `https://x.com/i/flow/login?redirect_after_login=%2Fhashtag%2FStreetFighter6%3Fsrc%3Dhashtag_click`
- Title: `登录 X / X`
- Extracted content level: login-flow text only (no hashtag timeline body).

Evidence highlights:

- Accessibility snapshot confirms login modal and account input flow.
- Document response body contains app shell and empty initial tweet entities:
  - `"tweets":{"entities":{},"errors":{},"fetchStatus":{}}`
- Runtime page text sample only includes login/register copy.

### 2) `x.com` live search page

- Result: `partial_success`
- Observed URL after load: `https://x.com/i/flow/login?redirect_after_login=%2Fsearch%3Fq%3D%2523StreetFighter6%26src%3Dtyped_query%26f%3Dlive`
- Title: `登录 X / X`
- Extracted content level: login-flow text only (no live search timeline body).

Evidence highlights:

- Accessibility snapshot shows same login modal structure as hashtag page.
- Document response body is again shell-level with empty initial tweet entities.
- Runtime page text sample only includes login/register copy.

### 3) `wiki.supercombo.gg` Street Fighter 6 page

- Result: `failure`
- Observed URL: `https://wiki.supercombo.gg/w/Street_Fighter_6`
- Title: `请稍候…` / challenge page (`Just a moment...` in response HTML).
- Extracted content level: Cloudflare challenge only, no Street Fighter 6 article body.

Evidence highlights:

- First document request status `403`, response header indicated challenge mode (`cf-mitigated: challenge` in network metadata).
- Accessibility snapshot shows Cloudflare Turnstile verification flow.
- Interaction attempt (clicking verification checkbox) still remained in challenge loop; no transition to article page content.

## Stability Verdict

- `x.com` hashtag/search URLs are not stably extractable for timeline body in this managed unauthenticated workflow; extraction currently stalls at login gate.
- `wiki.supercombo.gg/w/Street_Fighter_6` is not stably extractable in this run due to anti-bot challenge loop.
- Reusable value from this run is diagnostic-only: login-gate/challenge artifacts and structure clues were preserved for future live-session continuation.

## Artifact Index

- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-hashtag-latest.png`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-hashtag-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-hashtag-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-search-live-latest.png`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-search-live-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-search-live-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-x-shell-signals.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-latest.png`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-challenge-signals.txt`

## Recommended Next Action

- For `x.com`: continue via the specialist live-session path (`chrome-cdp`), attached to a user-approved already-authenticated tab, and keep the run read-only unless scope is expanded.
- For `wiki.supercombo.gg`: use a human-completed challenge session first, then continue extraction in the same live session; otherwise treat as blocked by anti-bot.
