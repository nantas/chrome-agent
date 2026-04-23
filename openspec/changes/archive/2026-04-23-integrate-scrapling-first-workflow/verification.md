# Verification

## Scope

This verification covers the Scrapling-first workflow change and the in-repo writeback targets updated to support it.

## Spec-to-Implementation Coverage

- `scrapling-first-browser-workflow`: implemented as the first webpage grabbing path in `AGENTS.md`, `README.md`, and the setup docs.
- `fallback boundaries`: implemented by keeping `chrome-devtools-mcp` as the diagnostics fallback and `chrome-cdp` as the live-session fallback.
- `environment contract`: implemented with a dedicated Scrapling setup doc, isolated Python `3.11.14` environment, and project MCP config entries.
- `verification baseline`: implemented by extending the playbook and validating the Scrapling path on public, dynamic, article, protected, and approved read-only authenticated pages.
- `documentation and site knowledge`: implemented by updating workflow docs, decision docs, playbooks, and the existing WeChat, SuperCombo, and X site notes.

## Task-to-Evidence

### Completed evidence

- Python `3.11.14` virtual environment created at `/Users/nantasmac/.cache/chrome-agent-scrapling`
- `scrapling[ai]` installed successfully with `uv`
- `scrapling install` completed and installed browser dependencies
- `codex -C /Users/nantasmac/projects/agentic/chrome-agent mcp get scrapling` confirmed the Scrapling MCP server registration
- `opencode mcp list` showed both `chrome-devtools` and `scrapling` as connected servers
- `scrapling extract get https://example.com ... --ai-targeted` succeeded
- `scrapling extract fetch https://todomvc.com/examples/react/dist/ ... --ai-targeted --network-idle` succeeded
- `scrapling extract get https://mp.weixin.qq.com/s/kPEyL3NDPAQYp7sFl5eE4w?scene=1 ... --ai-targeted` succeeded and preserved inline image URLs in Markdown output
- `scrapling extract stealthy-fetch https://wiki.supercombo.gg/w/Street_Fighter_6 ... --ai-targeted --solve-cloudflare` succeeded and solved the Cloudflare challenge
- Scrapling CDP-attached session attempt on `https://x.com/search?q=%23sf6_ingrid&src=typed_query` redirected to `/i/flow/login?...` instead of preserving the authenticated search page
- `chrome-cdp` read-only fallback on the approved live tab confirmed title `(4) #sf6_ingrid - Search / X`, stable URL, visible results, and account marker `Wang Nan @nantas`
- authenticated evaluation report added at `/Users/nantasmac/projects/agentic/chrome-agent/reports/2026-04-23-x-sf6-ingrid-authenticated-evaluation.md`

## Result

- Scrapling-first workflow: verified
- Chrome diagnostics fallback: verified
- Live-session fallback boundary: preserved
- Logged-in session experiment: executed, with Scrapling session reuse failing and approved live-tab fallback succeeding

## Notes

- The old Chrome-only decision record is now historical and retained as fallback evidence.
- The Scrapling executable path currently used by the repo is `/Users/nantasmac/.cache/chrome-agent-scrapling/bin/scrapling`.
