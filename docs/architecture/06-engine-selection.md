# 06 — Engine Selection Architecture

> **Spec reference**: `openspec/specs/engine-registry/`, `openspec/specs/engine-contracts/`
>
> **Config files**: `configs/engine-registry.json`, `configs/engine-versions.json`
>
> **Source**: AGENTS.md §3, §9

## 1. Overview

chrome-agent routes each web request through one of 10 registered engines, selected by a cascading decision tree that considers platform detection, protection level, and page type. The system includes preflight validation for each engine, a fallback escalation path, and version governance through a centralized manifest.

## 2. Engine Registry

All engines are registered in `configs/engine-registry.json` with their type, capabilities, status, and default rank.

| ID | Type | Status | Rank | Efficiency | Best For |
|----|------|--------|------|-----------|----------|
| `mediawiki-api` | `api` | frozen | 0 | 0.90 | MediaWiki articles, direct API fetch |
| `scrapling-get` | `http` | frozen | 1 | 0.95 | Static pages, low protection |
| `obscura-fetch` | `cdp_lightweight` | draft | 2 | 0.85 | Dynamic content, SPA, dynamic lists |
| `obscura-serve-pool` | `cdp_lightweight_pool` | draft | 3 | 0.85 | Bulk dynamic, concurrent fetch |
| `scrapling-fetch` | `playwright` | frozen | 4 | 0.60 | SPA rendering, dynamic interaction |
| `scrapling-bulk-fetch` | `playwright_bulk` | frozen | 4 | 0.55 | Bulk operations with Playwright |
| `cloakbrowser-fetch` | `playwright_stealth` | draft | 4 | 0.25 | High protection, Turnstile, reCAPTCHA, TLS fingerprint |
| `scrapling-stealthy-fetch` | `playwright_stealth` | **superseded** | 4 | 0.40 | ~~High protection~~ (replaced by cloakbrowser-fetch) |
| `chrome-devtools-mcp` | `cdp_managed` | frozen | 5 | 0.30 | Diagnostics, evidence collection |
| `chrome-cdp` | `cdp_live` | frozen | 6 | 0.20 | Authenticated sessions, live tab |

### Lifecycle States

| Status | Meaning |
|--------|---------|
| `frozen` | Stable, no breaking changes expected |
| `draft` | Active development, API may evolve |
| `superseded` | Replaced by a newer engine; retained for historical reference only |

### Type Taxonomy

| Type | Description | Browser Required |
|------|-------------|-----------------|
| `api` | Direct HTTP API calls (no rendering) | No |
| `http` | HTTP-only fetch (no JS rendering) | No |
| `cdp_lightweight` | Rust+V8 headless, minimal footprint | Lightweight |
| `cdp_lightweight_pool` | Worker pool of lightweight browsers | Lightweight × N |
| `playwright` | Full Playwright browser automation | Yes |
| `playwright_bulk` | Batch Playwright with amortized setup | Yes |
| `playwright_stealth` | Patched Chromium with stealth patches | Yes (patched) |
| `cdp_managed` | Managed browser via Chrome DevTools MCP | Yes (managed) |
| `cdp_live` | Live browser tab connection | Yes (user's) |

## 3. Engine Selection Decision Tree

```
REQUEST (URL + intent)
  │
  ├── Platform Detection
  │     ├── MediaWiki (api.platform: mediawiki in strategy)
  │     │     └── mediawiki-api (rank 0)
  │     ├── Sitemap-driven site (discovery.method: sitemap in strategy)
  │     │     └── sitemap.xml → scrapling-get (rank 1, linear extraction)
  │     └── Other → continue
  │
  ├── Protection Level Assessment
  │     ├── High protection (Turnstile / reCAPTCHA / TLS fingerprint)
  │     │     └── cloakbrowser-fetch (rank 4, stealth)
  │     ├── Moderate protection
  │     │     └── obscura-fetch (rank 2, cdp_lightweight)
  │     └── No/minimal protection → continue
  │
  ├── Page Type Analysis
  │     ├── Static page / article
  │     │     └── scrapling-get (rank 1, HTTP-only)
  │     ├── Dynamic content / SPA / dynamic list
  │     │     └── obscura-fetch (rank 2) → fallback: scrapling-fetch (rank 4)
  │     └── Batch / bulk URLs
  │           ├── obscura-serve-pool (rank 3, concurrent)
  │           └── scrapling-bulk-fetch (rank 4, sequential)
  │
  └── Special Cases
        ├── Diagnostic evidence needed
        │     └── chrome-devtools-mcp (rank 5)
        └── Authenticated session / live tab
              └── chrome-cdp (rank 6)
```

### Selection Rules

1. **API-first for MediaWiki**: When strategy declares `api.platform: mediawiki`, the `mediawiki-api` engine takes priority (rank 0) for crawl operations. `fetch` and `scrape` commands do not trigger the API path.
2. **Sitemap discovery for static doc sites**: When strategy declares `discovery.method: sitemap` (and no `api:` block), discovery parses `sitemap.xml` and page extraction uses `scrapling-get` (rank 1) linearly. This path is mutually exclusive with the MediaWiki API path.
3. **Scrapling-first default**: For non-API scenarios, start with `scrapling-get` (lightest engine). Escalate only when output is incomplete.
4. **Obscura for dynamic content**: When JS rendering is needed but full browser overhead is unwarranted, `obscura-fetch` provides 2-3.5× the speed of Playwright.
5. **CloakBrowser for high protection**: `cloakbrowser-fetch` handles Cloudflare Turnstile (6-8s auto-resolve), reCAPTCHA v3 (score 0.9), and TLS fingerprint detection via 57 C++ Chromium patches.
6. **DevTools for diagnostics only**: `chrome-devtools-mcp` is never a primary extraction engine; it provides DOM, network, console, and screenshot evidence.

## 4. Preflight Mechanism

Before any engine runs, a preflight check ensures the engine is installed and functional.

### Scrapling Preflight

- **CLI discovery**: Checks `SCRAPLING_CLI_PATH` env var, then managed installation at `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`
- **Managed venv**: Scrapling runs in a dedicated Python venv managed by `scripts/scrapling-cli.sh`
- **Auto-install**: If missing, preflight provisions the venv automatically
- **Reference**: `docs/playbooks/scrapling-cli-preflight.md`

### Obscura Preflight

- **Binary discovery**: Checks `OBSCURA_CLI_PATH` env var, then managed path `$HOME/.cache/chrome-agent-obscura/bin/obscura`
- **Hash verification**: Validates binary MD5 and file size against `configs/engine-versions.json`
- **Download**: Fetches from GitHub Releases (`h4ckf0r0day/obscura`) with platform-specific archives
- **Reference**: `docs/playbooks/obscura-cli-preflight.md`

### CloakBrowser Preflight

- **Module check**: Verifies `cloakbrowser` Python module is importable
- **Binary cache**: Chromium binary auto-downloads to `~/.cloakbrowser/chromium-{version}/` on first use
- **Reference**: `scripts/cloakbrowser-preflight.sh`

### Doctor Integration

`chrome-agent doctor --format json` runs all preflight checks and reports version status via `scripts/engine-version-check.sh --json`.

## 5. Fallback Escalation Path

When the primary engine fails or produces incomplete output, the system escalates:

```
scrapling-get (static)
  ↓ incomplete / blocked
obscura-fetch (dynamic, cdp_lightweight)
  ↓ incomplete / blocked
cloakbrowser-fetch (stealth, patched Chromium)
  ↓ needs diagnostics
chrome-devtools-mcp (evidence collection)
  ↓ needs live session
chrome-cdp (authenticated continuity)
```

### Escalation Triggers

| Signal | Action |
|--------|--------|
| Scrapling output incomplete or blocked | Escalate to obscura-fetch |
| Obscura CDP subset insufficient | Escalate to cloakbrowser-fetch or scrapling-fetch |
| Visual output suspicious / needs evidence | Switch to chrome-devtools-mcp |
| Authenticated state required | Switch to chrome-cdp |

### Fallback Selection Criteria

- **Diagnostic need** → chrome-devtools-mcp (DOM/network/console/screenshots)
- **Session continuity** → chrome-cdp (live tab, authenticated state)
- **Not both** — choose based on the specific need, don't switch tools arbitrarily

**Reference**: `docs/playbooks/fallback-escalation.md`

## 6. Engine Version Governance

### Version Manifest — `configs/engine-versions.json`

The single source of truth for all engine versions:

| Engine | Version Type | Detection Method | Managed Path |
|--------|-------------|-----------------|--------------|
| Scrapling | `pip` | `python_importlib` in managed venv | `$HOME/.cache/chrome-agent-scrapling/` |
| Obscura | `precompiled_binary` | `file_hash` (MD5 + size) | `$HOME/.cache/chrome-agent-obscura/bin/` |
| CloakBrowser | `pip_module` | `python_attribute` (`__version__`) | System Python (pip-managed) |

### Upgrade Workflow

Engine runtime upgrades must follow this order:

1. **Confirm availability**: Check PyPI / GitHub Release for target version
2. **Update manifest**: Modify `configs/engine-versions.json`:
   - `expected_version`
   - For Obscura: `expected_size` and `expected_md5` for each binary
3. **Execute install**: `./scripts/engine-version-check.sh --update --engine <name>`
4. **Verify**: `./scripts/engine-version-check.sh --json` → `all_ok: true`
5. **Doctor check**: `chrome-agent doctor --format json` → version check passes
6. **Commit**: Include `configs/engine-versions.json` update in the upgrade commit

### Obscura Hash Acquisition

After upgrading Obscura, obtain new hashes immediately:

```bash
BIN="$HOME/.cache/chrome-agent-obscura/bin"
md5 -q "$BIN/obscura" "$BIN/obscura-worker"
stat -f '%z' "$BIN/obscura" "$BIN/obscura-worker"
```

### Governance Constraints

- **`engine-registry.json` is NOT a version source**: Its prose version strings are human-readable only
- **`engine-version-check.sh` is the single detection entry point**: All preflight and doctor checks route through it
- **No manual binary swaps**: Never bypass the manifest by manually replacing binaries or pip-installing without updating `engine-versions.json`

## 7. Superseded Engine: `scrapling-stealthy-fetch`

| Property | Value |
|----------|-------|
| Status | `superseded` |
| Replacement | `cloakbrowser-fetch` |
| Reason | CloakBrowser provides 57 C++ source-level Chromium patches for superior stealth capabilities |
| Retention | Kept in registry for historical reference; not selected by any routing rule |

## 8. Version Check Script

`scripts/engine-version-check.sh` provides unified version detection:

```bash
# Check all engines
./scripts/engine-version-check.sh

# JSON output (consumed by doctor)
./scripts/engine-version-check.sh --json

# Auto-update specific engine
./scripts/engine-version-check.sh --update --engine obscura
```

Output includes per-engine `status` (`ok` / `version_mismatch` / `hash_mismatch` / `not_found`) and an aggregate `all_ok` flag.

## 关联文档

- [01 — 系统总览](01-overview.md) — 多后端架构中的引擎定位
- [04 — CLI 参考](04-cli-reference.md) — 命令路由如何触发引擎选择
- [08 — 技术栈](08-tech-stack.md) — 引擎版本治理与依赖管理
