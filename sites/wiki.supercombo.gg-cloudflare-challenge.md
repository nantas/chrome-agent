# wiki.supercombo.gg Cloudflare Challenge Note

## Scope

- Domain: `wiki.supercombo.gg`
- Path validated: `/w/Street_Fighter_6`
- Date: `2026-03-21`

## Observed Behavior

- Historical managed-browser run on `2026-03-21` returned `403`.
- Challenge response HTML title was `Just a moment...`.
- Runtime page title showed `请稍候…`, with Cloudflare Turnstile verification flow.
- That earlier run stayed inside the anti-bot challenge loop and never reached the article body.

## Extraction Impact

- Direct managed extraction in the earlier run was blocked.
- The later Scrapling `stealthy-fetch` smoke check reached the article content successfully.

## Interaction Outcome

- Checkbox interaction on the Turnstile widget was attempted in the earlier managed-browser run.
- That run remained in verification flow with no transition to article content.

## Recommended Routing

- Try Scrapling `stealthy-fetch` first for grab-first tasks on this domain.
- Escalate to `chrome-devtools-mcp` when challenge diagnostics or browser evidence are needed.
- If user approves and a real logged-in or solved tab must be continued immediately, use specialist live-session continuation (`chrome-cdp`), read-only by default.

## Notes From The Scrapling Run

Observed on the Scrapling smoke check:

- `scrapling extract stealthy-fetch ... --solve-cloudflare` solved the Turnstile challenge and reached the Street Fighter 6 page
- the resulting Markdown preserved the page title and article content rather than only the challenge shell
- for this domain, Scrapling should now be tried before falling back to live-tab continuation when the user wants a grab-first path

## Artifacts (2026-03-21 run)

- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-challenge-signals.txt`
