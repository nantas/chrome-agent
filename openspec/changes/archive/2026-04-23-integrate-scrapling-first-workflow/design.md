# Design

## Context

The normative behavior for this change is `specs/scrapling-first-browser-workflow/spec.md`.

The repository currently documents `chrome-devtools-mcp` as the default browser path and `chrome-cdp` as the specialist live-session path. This change replaces that default routing with a Scrapling-first model while preserving the existing tools as fallback and evidence paths.

Local discovery found that the current system Python is `3.9.6` and Scrapling is not installed. Scrapling currently requires Python `>=3.10`, so implementation must introduce an isolated Python runtime path instead of relying on `/usr/bin/python3`.

## Goals / Non-Goals

**Goals:**

- Make Scrapling the first path in the documented workflow for public, dynamic, protected, batch, and approved read-only session grabbing tasks.
- Add setup documentation for a Python `>=3.10` Scrapling environment, browser dependencies, CLI checks, and MCP server configuration.
- Reframe `chrome-devtools-mcp` as the structured diagnostic and evidence fallback.
- Preserve `chrome-cdp` as the already-open live Chrome fallback when session preservation or immediate tab continuation matters.
- Extend the evaluation playbook with Scrapling-first success criteria and fallback evidence requirements.
- Record the explicit approval precondition for any logged-in read-only Scrapling validation.

**Non-Goals:**

- Do not build a new large automation framework.
- Do not default to Scrapling Spider/checkpoint/proxy-pool crawling until real site-level tasks justify it.
- Do not introduce credential storage or automated login management.
- Do not move site-specific extraction logic into the global `chrome-agent` dispatcher skill.

## Decisions

- **Workflow decision:** `AGENTS.md` becomes the primary operator contract for Scrapling-first routing. It should keep the existing Content Retrieval vs Platform/Page Analysis split, but replace the tool priority inside both routes.
- **Setup decision:** Add a dedicated Scrapling setup doc under `docs/setup/`. The recommended local path uses `uv` to provision Python `>=3.10`, then installs Scrapling and runs `scrapling install`.
- **MCP decision:** Add documented MCP configuration for Scrapling as an optional project-scoped server after the CLI smoke check succeeds. The implementation should avoid deleting the existing `chrome-devtools` MCP config.
- **Fallback decision:** Do not remove `chrome-devtools-mcp` or `chrome-cdp`. Reword them as fallback paths with explicit triggers matching the spec.
- **Evaluation decision:** Add Scrapling to the existing browser tooling evaluation playbook rather than creating a separate one-off benchmark.
- **Decision-record decision:** Add a new decision file under `docs/decisions/` stating that the March DevTools-first decision is superseded for grabbing priority, but still valid for diagnostics and live-session fallback evidence.

## Risks / Migration

- Scrapling may not preserve authenticated state as well as a direct live Chrome continuation. The first logged-in scenario must be read-only, explicitly approved, and must stop on logout, redirect, reset, or write-action risk. This change only documents that precondition; it does not claim a logged-in validation without an approved target.
- Protected-page claims must be verified against real targets. If Scrapling fails a Cloudflare or Turnstile page, the report should record the exact fetcher/session path and fallback trigger instead of treating the failure as a workflow failure.
- Adding Scrapling MCP before the runtime is verified could leave a broken project config. Implementation should verify the executable path first, then document or add config.
- Existing reports and site notes were produced under DevTools/CDP assumptions. Update stable docs and add new evidence instead of rewriting historical reports.
