# wiki.supercombo.gg Cloudflare Challenge Note

## Scope

- Domain: `wiki.supercombo.gg`
- Path validated: `/w/Street_Fighter_6`
- Date: `2026-03-21`

## Observed Behavior

- Initial document request returned `403`.
- Challenge response HTML title: `Just a moment...`.
- Runtime page title shown as `请稍候…`, with Cloudflare Turnstile verification flow.
- Snapshot and network evidence indicate anti-bot challenge loop; article body never became available.

## Extraction Impact

- Direct managed extraction is blocked in this run.
- Output can preserve only challenge diagnostics, not Street Fighter 6 article content.

## Interaction Outcome

- Checkbox interaction on Turnstile widget was attempted.
- Session remained in verification flow, with no transition to article content.

## Recommended Routing

- Treat as blocked unless a real browser session completes challenge first.
- If user approves, continue from already-open solved tab using specialist live-session continuation (`chrome-cdp`), read-only by default.

## Artifacts (2026-03-21 run)

- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-snapshot.txt`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-document.html`
- `/Users/nantas-agent/projects/chrome-agent/reports/2026-03-21-sf6-supercombo-challenge-signals.txt`
