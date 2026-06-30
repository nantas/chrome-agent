# 07 — Explore Workflow Architecture

> **Spec reference**: Architecture Gate spec, KI Lifecycle spec
>
> **Source modules**: `scripts/explore/`
>
> **Source**: AGENTS.md §3 Deep Discovery content

## 1. Overview

The Explore workflow implements a **deep discovery pipeline** that analyzes an unknown website, generates a strategy scaffold, validates conversion quality, and produces a frozen strategy file. It operates as an 8-step sequential pipeline with two critical validation gates.

```
URL input
  │
  ├── Step 1: ProbeChain         ──→ Engine chain results + raw HTML
  ├── Step 2: ApiDiscovery       ──→ Platform API endpoints
  ├── Step 3: StructureMapper    ──→ Nav sections, page type, content structure
  ├── Step 4: ProtectionIdentifier ──→ Protection level + engine override
  ├── Step 5: Template Selection ──→ Best-matching scaffold template
  ├── Step 6: Scaffold Generation ──→ strategy.md with YAML frontmatter
  ├── Step 7: Sample Conversion & Self-Check ──→ Markdown outputs + quality checks
  │     ├── Architecture Gate (strategy↔pipeline alignment)
  │     └── Auto-remediation loop (max 2 iterations)
  └── Step 8: Freeze            ──→ Remove scaffold markers, register strategy
```

## 2. CLI Entry Point

```bash
python3 scripts/explore/main.py <repo_root> <url> [--run-dir <dir>] [--samples <json>] [--quick]
```

**Output**: JSON to stdout with all pipeline phase results:

```json
{
  "target_url": "...",
  "probe_chain": { "results": [...], "success_engine": "..." },
  "api_discovery": [...],
  "structure_mapping": {...},
  "protection": {...},
  "scaffold": { "path": "...", "template_id": "..." },
  "samples": [...],
  "self_check": {...},
  "architecture_gate": {...},
  "run_dir": "..."
}
```

**Exit codes**:
- `0` — Success (all gates passed)
- `2` — Partial success (architecture gate violations)

## 3. 8-Step Pipeline

### Step 1: ProbeChain (`probe_chain.py`)

Sequentially attempts engines until one succeeds:

```
scrapling-get → obscura-fetch → cloakbrowser-fetch → chrome-devtools-mcp
```

Per-engine results include: `engine`, `status`, `http_status`, `error_type`, `page_title`, `content_length`.

**Key function**: `probe(repo_root, url, run_dir) → dict`

### Step 2: ApiDiscovery (`api_discovery.py`)

Probes common API endpoints for the target domain:

| Endpoint | Detection |
|----------|-----------|
| `/api.php` | MediaWiki API (`?action=query&meta=siteinfo`) |
| `/wp-json` | WordPress REST API |
| `/graphql` | GraphQL endpoint (introspection query) |
| `/sitemap.xml` | XML sitemap |
| `/robots.txt` | Robots file |

**Key function**: `discover(url) → list[dict]`

### Step 3: StructureMapper (`structure_mapper.py`)

Analyzes HTML structure to extract:

- **Navigation sections**: Top nav items (max 10) from primary navigation
- **Page type**: `home` / `list` / `article` / `gallery` / `other`
- **Content structure**: Tables, infoboxes, lists, sections present

**Key function**: `map_structure(html, api_config) → dict`

### Step 4: ProtectionIdentifier (`protection_identifier.py`)

Determines protection level based on:

- Engine chain error patterns (which engines failed and how)
- HTML content features (challenge pages, CAPTCHA elements)

Output includes `protection_level` and optional `engine_override`.

**Key function**: `identify(engine_results, html_content) → dict`

### Step 5: Template Selection (`strategy_scaffold_generator.py`)

Selects the best-matching template from `sites/templates/`:

| Template | Platform Match |
|----------|---------------|
| `mediawiki` | Standard MediaWiki |
| `mediawiki-fandom` | Fandom-hosted MediaWiki |
| `static-site` | Static HTML sites |
| `custom` | Fallback for unknown platforms |

**Key function**: `_select_template(repo_root, platform, protection) → dict`

### Step 6: Scaffold Generation (`strategy_scaffold_generator.py`)

Generates a `strategy.md` file with YAML frontmatter populated from discovery results:

- `domain`, `platform`, `protection_level`, `protection_type`
- `page_type` array mapped from nav sections
- `api` config (if MediaWiki detected)
- `extraction` rules (selectors, cleanup, infobox, image filtering)
- `anti_crawl` references

The scaffold file is written to `sites/strategies/<domain>/strategy.md` with a first line `# Auto-generated scaffold — review recommended`.

**Overwrite Guard**：如果 `strategy.md` 已存在且首行不是 `# Auto-generated scaffold`，scaffold 生成器将跳过写入并返回 `{"skipped": true, "reason": "Manually-edited strategy exists — delete it first to regenerate."}`。这保护了手动编辑的策略文件不被 explore 流程重置。自动生成的 scaffold（首行以 `# Auto-generated scaffold` 开头）则允许正常覆盖，支持重新生成。

**Key function**: `generate(repo_root, domain, description, platform, protection, structure, api_config) → dict`

### Step 7: Sample Conversion & Self-Check

This is the most complex step, involving multiple sub-phases:

#### 7a: Sample Conversion (`sample_converter.py`)

Fetches sample pages and converts them using the scaffold extraction rules:

```python
def _apply_extraction(html, extraction_rules, known_pages):
    infobox_md = extract_infobox(html, extraction_rules, wiki_domain)    # Step 1
    cleaned_html = preprocess_html(html, extraction_rules, "explore")    # Step 2
    md = convert_html_to_markdown(cleaned_html, wiki_domain, rules)      # Step 3
    md = infobox_md + "\n\n" + md                                        # Step 4
    # Post-conversion normalization...
```

**Key function**: `convert(repo_root, samples, extraction_rules, engine, run_dir) → list[dict]`

#### 7b: Self-Check (`self_check.py`)

Runs S1–S12 quality checks against each converted sample:

| Check | What it validates |
|-------|------------------|
| S1 | Image retention (count + full URL verification) |
| S2 | Link resolution (no unresolved references) |
| S3 | Infobox extraction completeness |
| S4 | Non-empty content |
| S5 | Text integrity (version regex check) |
| S6 | Table structure preservation |
| S7 | Image wrapper cleanup |
| S8 | Section extraction completeness |
| S9 | Navigation removal from content |
| S10 | YouTube title extraction |
| S11 | Relative link conversion |
| S12 | Infobox semantic quality |

Each check returns: `{check, status: pass|fail|skip, detail, fixable_type?}`

**Key function**: `run_checks(html, markdown, wikitext, known_pages, type, ...) → list[dict]`

#### 7c: Auto-Remediation Loop

If self-check finds fixable failures, the system automatically adjusts extraction rules and re-converts:

```
Iteration 0: Initial conversion + self-check
  ↓ fixable_failures found?
Iteration 1: auto_remediate(extraction, failures) → re-convert → re-check
  ↓ fixable_failures found?
Iteration 2: auto_remediate → re-convert → re-check
  ↓ max 2 iterations reached
Done
```

**Key function**: `auto_remediate(extraction, fixable_failures) → dict`

#### 7d: Architecture Gate (`architecture_gate.py`)

**Runs after self-check passes, before final output.** Validates bidirectional alignment between strategy config and pipeline converters.

See §4 below for details.

### Step 8: Freeze (`freeze.py`)

After user confirmation:

1. Removes scaffold `<!-- Bootstrapped -->` marker
2. Writes final strategy to `sites/strategies/<domain>/strategy.md`
3. Appends entry to `sites/strategies/registry.json`

**Key function**: `freeze(repo_root, scaffold_path) → dict`

## 4. Architecture Gate

The Architecture Gate (`scripts/explore/architecture_gate.py`) validates **strategy↔pipeline bidirectional alignment** — ensuring no dead config and no hardcoded site-specific values.

### Two-Part Validation

#### Check 1: Strategy → Pipeline (Dead Config Detection)

Scans all extraction config keys to ensure each is consumed by `html_to_markdown.py`:

- Checks `.get("key")`, `["key"]`, `"key" in variable`, and `if "key"` patterns in pipeline source
- Validates each `cleanup` operation name appears in pipeline source
- Also checks cleanup operation names via `detect_dead_cleanup_operations()`

**Result**: `dead_config: list[str]` — config keys with no pipeline consumer

#### Check 2: Pipeline → Strategy (Hardcoded Value Audit)

Audits `html_to_markdown.py` for site-specific values not sourced from strategy config:

| Check Type | What it detects |
|------------|----------------|
| `hardcoded_selector` | CSS selectors not from `cleanup_selectors` or `infobox.selector` config |
| `hardcoded_css_class` | CSS class names not in strategy's known class set |
| `hardcoded_list_value` | CSS class names in list literals not from config |
| `hardcoded_domain` | Domain names not derived from `image_handling.base_url` |
| `hardcoded_filename_pattern` | File patterns not from `image_filtering.skip_patterns` |
| `unconditional_operation` | Site-specific operations not guarded by config `enabled` checks |

**Result**: `violations: list[dict]` — each with `type`, `detail`, `location`, `remediation`

### Gate Result

```json
{
  "status": "pass" | "fail",
  "strategy_to_pipeline": {
    "status": "pass" | "fail",
    "dead_config": [...],
    "files_checked": ["converter.py", "preprocessor.py"]
  },
  "pipeline_to_strategy": {
    "status": "pass" | "fail",
    "violations": [...]
  }
}
```

The gate runs on the pipeline extraction files defined in `_PIPELINE_FILES` (currently `converter.py` + `preprocessor.py`): `converter.py` for conversion/hardcoded-value audit, `preprocessor.py` for cleanup-operation consumption.

## 5. KI Lifecycle Gate

The KI (Known Issue) Lifecycle module (`scripts/explore/ki_lifecycle.py`) runs **after the Architecture Gate passes** and provides structured management of self-check failures that could not be auto-remediated.

### KI Classification

Each self-check failure is classified with an **owner domain**:

| Owner | Meaning |
|-------|---------|
| `strategy` | Fix requires strategy config changes |
| `pipeline` | Fix requires converter/pipeline code changes |
| `self_check` | Check methodology issue (false positive, scope problem) |

Owner inference decision tree:
1. Explicit override provided → use it
2. `fixable_type` suggests pipeline fix → `pipeline`
3. Check ID has predefined mapping → use mapping
4. Heuristic keyword matching in detail text
5. Default → `self_check`

### Priority Assignment

| Priority | Criteria |
|----------|----------|
| P0 | Data corruption (wrong field values, broken links/images, navigation text in IDs) |
| P1 | Quality impact (readability reduction, false positives, minor pollution) |
| P2 | Check methodology (scope/precision issues, no output impact) |
| P3 | Skip/cosmetic (negligible visual impact) |

### Status State Machine

```
open ──→ in_progress ──→ resolved
  │           │
  │           └──→ wontfix (terminal)
  ├──→ open_systemic (terminal)
  └──→ wontfix (terminal)
```

### Fix Batch Planning

KIs are grouped into priority-based batches for sequential fix iterations:

- Batch 0: All P0 KIs
- Batch 1: All P1 KIs
- Batch 2: All P2 KIs (P3 are cosmetic, not batched)

Maximum 3 iterations (`MAX_ITERATIONS = 3`).

### KI Table Generation

Produces a Markdown table for inclusion in `strategy.md`:

```markdown
## Known Issues (Post-Validation)

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| KI-1 | ... | open | P1 | pipeline | ... | ... |
```

**Key function**: `run_ki_lifecycle(failures, owner_overrides) → list[dict]`

## 6. Confirmation Gates

### Explore → Crawl Confirmation Gate

When `explore` returns `partial_success` with a strategy gap, the agent **must not** proceed directly to crawl or fetch. The gate requires:

1. **Agent presents**: Structure analysis, sample conversions, self-check results, architecture gate result
2. **Agent self-audits**: Before user review, verify self-check report completeness
3. **User confirms**: Explicit approval to proceed
4. **3-iteration limit**: Maximum 3 remediation iterations before requiring user intervention

### Crawl Confirmation Gate (Discovery → Extraction)

When SKILL routes `crawl` intent without `--yes`:

1. **Discovery-only**: `chrome-agent crawl <url> --discovery-only --format json`
2. **Presentation**: Tree visualization of discovery results
3. **Confirmation**: User approves/adjusts/cancels
4. **Extraction**: `chrome-agent crawl <url> --from-manifest <path>`

`--yes` bypasses the gate entirely.

## 7. Module Dependency Map

```
main.py
  ├── probe_chain.py          (Phase 1)
  ├── api_discovery.py        (Phase 2)
  ├── structure_mapper.py     (Phase 3)
  ├── protection_identifier.py(Phase 4)
  ├── strategy_scaffold_generator.py (Phase 5+6)
  ├── sample_converter.py     (Phase 7a)
  │     ├── lib/extraction/infobox.py
  │     ├── lib/extraction/preprocessor.py
  │     └── pipeline/converters/html_to_markdown.py
  ├── self_check.py           (Phase 7b+7c)
  ├── architecture_gate.py    (Phase 7d)
  └── ki_lifecycle.py         (Post-gate)
```

External dependencies (from `scripts/explore/requirements.txt`):
- `beautifulsoup4>=4.12`
- `pyyaml>=6.0`
- `selectolax>=0.3`

## 关联文档

- [00 — 目标架构](00-target-architecture.md) — **架构真源**：explore 作为 B 轴执行路径的 4 维坐标
- [01 — 系统总览](01-overview.md) — 多后端架构全景

