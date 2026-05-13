# Explore Workflow Conduct

## Purpose

This playbook documents the `explore` deep discovery workflow for strategy gap scenarios — when `chrome-agent explore <url>` does not match an existing site strategy.

## Trigger

- User runs `chrome-agent explore <url>` against an uncovered domain
- Skill layer routes to `explore` with no matching strategy in `sites/strategies/registry.json`

## Workflow Overview

```
explore <url>
  ├─ strategy registry lookup
  │   ├─ MATCH → existing behavior (structured report, recommended fetcher)
  │   └─ GAP  → deep discovery pipeline
  │       ├─ Phase A: Engine Probe Chain
  │       ├─ Phase B: API Discovery
  │       ├─ Phase C: Structure Mapping
  │       ├─ Phase D: Protection Identification
  │       ├─ Phase E: Template Selection → Scaffold Generation
  │       ├─ Phase F: Sample Conversion + Self-Check (S1-S7)
  │       ├─ Phase G: User Interactive Confirmation (skill layer)
  │       └─ Phase H: Freeze or Iterate
```

## Phase Details

### Phase A: Engine Probe Chain

**Module**: `scripts/explore/probe_chain.py`

Attempts in order:
1. `scrapling-get` — static fetch
2. `obscura-fetch` — lightweight CDP (SPA/dynamic)
3. `cloakbrowser-fetch` — stealth browser (high protection)
4. `chrome-devtools-mcp` — diagnostic fallback (handled by CLI layer)

**Output per engine**:
```json
{
  "engine": "scrapling-get",
  "status": "success|failure|partial",
  "http_status": 200,
  "error_type": "cloudflare-managed|rate-limit|timeout|unknown",
  "page_title": "...",
  "content_length": 12345
}
```

### Phase B: API Discovery

**Module**: `scripts/explore/api_discovery.py`

Probes endpoints:
- `/api.php` → MediaWiki `siteinfo`
- `/wp-json` → WordPress REST
- `/graphql` → GraphQL introspection
- `/sitemap.xml` → URL count
- `/robots.txt` → crawl rules

**Output**:
```json
{
  "type": "mediawiki",
  "base_url": "https://example.com/api.php",
  "version": "MediaWiki 1.43.8",
  "capabilities": ["read", "parse", "query"],
  "pages": 1234,
  "articles": 567
}
```

### Phase C: Structure Mapping

**Module**: `scripts/explore/structure_mapper.py`

Extracts:
- **Page type**: home / list / article / gallery (DOM heuristic)
- **Nav sections**: ≤10 top-level labels
- **Content structure**: tables, infoboxes, lists, card patterns
- **Category counts**: via `categorymembers` API (if MediaWiki)

### Phase D: Protection Identification

**Module**: `scripts/explore/protection_identifier.py`

Rules:
- 403 + "Just a moment..." → `cloudflare-managed`
- 403 + `cf-turnstile` → `cloudflare-turnstile`
- 429 → `rate-limit`
- redirect to `/login` → `login-wall`

**Output**:
```json
{
  "type": "cloudflare-managed",
  "detection_basis": "403 + 'Just a moment...' from scrapling-get",
  "engine_override": "cloakbrowser-fetch"
}
```

### Phase E: Template Selection + Scaffold Generation

**Module**: `scripts/explore/strategy_scaffold_generator.py`

1. Select template from `sites/templates/` based on platform + protection level
2. Fill frontmatter: domain, description, protection_level, anti_crawl_refs, structure.pages[], api, extraction rules
3. Write to `sites/strategies/<domain>/strategy.md` with header `# Auto-generated scaffold — review recommended`

**Templates available**:
- `mediawiki.yaml` — generic MediaWiki
- `mediawiki-fandom.yaml` — Fandom (Cloudflare, lazyload images)
- `mediawiki-wiki-gg.yaml` — wiki.gg
- `wordpress.yaml` — WordPress REST API (skeleton)
- `static-site.yaml` — plain HTML
- `custom.yaml` — fallback

### Phase F: Sample Conversion + Self-Check

**Modules**: `scripts/explore/sample_converter.py`, `scripts/explore/self_check.py`

1. Fetch sample pages using determined engine
2. Apply extraction rules (selectors, cleanup, text normalization)
3. Convert to Markdown with YAML frontmatter
4. Run S1-S7 checks:
   - **S1**: Image retention count
   - **S2**: Internal wiki link resolution
   - **S3**: Infobox extraction
   - **S4**: Empty content
   - **S5**: Text integrity (spaces, base64 residue, escapes)
   - **S6**: Table integrity
   - **S7**: Image wrapper detection

5. **Auto-remediation**: if fixable failures detected, `main.py` amends extraction rules via `auto_remediate()` and re-converts (max 2 iterations)

### Phase G: User Interactive Confirmation

**Module**: `scripts/explore/scope_confirmer.py`
**Consumption Layer**: `chrome-agent` workflow skill (ask_user)

`scope_confirmer.py` consumes the `discovery` JSON and generates structured question payloads for the skill layer to present via `ask_user`. It drives a 4-round confirmation:

1. **Content scope**: all / specific sections / to be specified
   - Dynamically lists detected nav sections (≤10) from `structure_mapping.nav_sections`
2. **Page granularity**: summary+individual / individual only / summary only
   - Warns if the page looks like a list-only page with no individual entries
3. **Sample selection**: agent recommends 4-8 covering each content type, user confirms or adjusts
4. **Output format**: Markdown+frontmatter / pure Markdown / JSON

The skill layer passes the user's answers back to the CLI or stores them for the freeze/iterate phases.

### Phase H: Freeze or Iterate

**Freeze** (`scripts/explore/freeze.py`):
```bash
python3 scripts/explore/freeze.py <repo_root> <scaffold_path>
```
- Removes scaffold marker
- Appends entry to `sites/strategies/registry.json`
- Generates `freeze-report.json`

**Iterate** (`scripts/explore/iterate.py`):
```bash
python3 scripts/explore/iterate.py <repo_root> <scaffold_path> \
  --feedback "images not loading, missing spaces" \
  --samples '[{"url": "...", "title": "..."}]' \
  --engine cloakbrowser-fetch \
  --run-dir <dir>
```
- Parses feedback to update extraction rules
- Re-runs conversion and self-check
- Returns updated results

## CLI Integration

The `explore` command in `chrome-agent-cli.mjs` invokes the deep discovery pipeline automatically when no strategy exists:

```javascript
// In runExplore()
if (!strategy) {
  const ddResult = spawnSync("python3", [
    path.join(repoRoot, "scripts", "explore", "main.py"),
    repoRoot,
    targetUrl,
    "--run-dir", runDir,
  ]);
  // Parse JSON output, build extended result with discovery/scaffold/samples/self_check
}
```

If the Python pipeline fails, the CLI falls back to legacy behavior (`scrapling-get` + `detectBackend`).

## Directory Structure

```
scripts/explore/
├── __init__.py
├── main.py                    # CLI entry for deep discovery
├── probe_chain.py             # Phase A: engine chain
├── api_discovery.py           # Phase B: API probes
├── structure_mapper.py        # Phase C: structure extraction
├── protection_identifier.py   # Phase D: protection detection
├── strategy_scaffold_generator.py  # Phase E: scaffold generation
├── sample_converter.py        # Phase F: conversion
├── self_check.py              # Phase F: S1-S7 + auto-remediation helpers
├── scope_confirmer.py         # Phase G: confirmation question generation
├── freeze.py                  # Phase H: finalize strategy
└── iterate.py                 # Phase H: refine extraction rules
```

## Backward Compatibility

- **Strategy-matched URLs**: unchanged behavior (load strategy, return structured report)
- **Strategy-gap URLs with backend detection**: legacy `detectBackend` still runs if deep discovery fails
- **Existing strategies**: no format changes; new strategies follow same YAML frontmatter schema

## References

- Spec: `openspec/changes/explore-workflow-templates/specs/explore-workflow/spec.md`
- Design: `openspec/changes/explore-workflow-templates/design.md`
- Tasks: `openspec/changes/explore-workflow-templates/tasks.md`
- Verification: `openspec/changes/explore-workflow-templates/verification.md`
