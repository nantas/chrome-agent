# Writeback

## Target Summary

This change writes back into the repository itself so the Scrapling-first workflow becomes the documented default.

## Writeback Targets

- `/Users/nantasmac/projects/agentic/chrome-agent/AGENTS.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/README.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/docs/setup/chrome-tooling.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/docs/setup/scrapling-first-workflow.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/docs/decisions/2026-03-17-browser-tooling-workflow.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/docs/decisions/2026-04-23-scrapling-first-workflow.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/docs/decisions/README.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/docs/playbooks/browser-tooling-evaluation.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/.codex/config.toml`
- `/Users/nantasmac/projects/agentic/chrome-agent/opencode.json`
- `/Users/nantasmac/projects/agentic/chrome-agent/sites/x.com-public-hashtag-search-login-gate.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/sites/README.md`
- `/Users/nantasmac/projects/agentic/chrome-agent/reports/2026-04-23-x-sf6-ingrid-authenticated-evaluation.md`

## Field Mapping

- workflow default and fallback ordering -> `AGENTS.md` and `README.md`
- installation and MCP launch path -> `docs/setup/scrapling-first-workflow.md`
- Chrome diagnostic fallback guidance -> `docs/setup/chrome-tooling.md`
- decision history -> `docs/decisions/`
- evaluation matrix and evidence requirements -> `docs/playbooks/browser-tooling-evaluation.md`
- project-scoped MCP server registration -> `.codex/config.toml` and `opencode.json`

## Preconditions

- Scrapling environment verified at `/Users/nantasmac/.cache/chrome-agent-scrapling/bin/scrapling`
- Scrapling MCP server confirmed by both `codex` and `opencode`
- browser smoke checks completed for representative static, dynamic, article, and protected pages

## Execution Evidence

- `codex -C /Users/nantasmac/projects/agentic/chrome-agent mcp get scrapling`
- `opencode mcp list`
- `scrapling --help`
- `scrapling extract get https://example.com ... --ai-targeted`
- `scrapling extract fetch https://todomvc.com/examples/react/dist/ ... --ai-targeted --network-idle`
- `scrapling extract get https://mp.weixin.qq.com/s/kPEyL3NDPAQYp7sFl5eE4w?scene=1 ... --ai-targeted`
- `scrapling extract stealthy-fetch https://wiki.supercombo.gg/w/Street_Fighter_6 ... --ai-targeted --solve-cloudflare`
- Scrapling CDP-attached fetch against `https://x.com/search?q=%23sf6_ingrid&src=typed_query`
- `node .agents/skills/chrome-cdp/scripts/cdp.mjs eval F133C35D ...`
- `node .agents/skills/chrome-cdp/scripts/cdp.mjs shot F133C35D reports/2026-04-23-x-sf6-ingrid-cdp.png`

## Conflict Handling

- If a user later wants to restore Chrome-first behavior, update `AGENTS.md`, `README.md`, `docs/decisions/2026-04-23-scrapling-first-workflow.md`, and the playbook together so the default ordering stays consistent.
- If the Scrapling executable path changes, update the two MCP config files and `docs/setup/scrapling-first-workflow.md` together.
