# Handoff: rep.taptap.cn SPA rendering pipeline gaps

## Context

| Field | Value |
|---|---|
| Command | `chrome-agent explore https://rep.taptap.cn/docs/taprep-about` |
| Target | https://rep.taptap.cn/docs/ (Vue SPA, 26 页帮助文档) |
| Timestamp | 2026-06-26T07:30:00Z |
| Repo ref | env:CHROME_AGENT_REPO |
| Strategy path | `sites/strategies/rep.taptap.cn/strategy.md` (已提交 ca60abf) |
| Workflow artifact | `outputs/20260626T072200-explore-rep-taptap-cn-samples/` (5 sample pages + S1-S12 self-check) |

## What Worked

- ✅ `scrapling extract fetch` (Playwright 渲染) 可以正确渲染 SPA，提取 `.rep-docs-content` 正文
- ✅ `--network-idle --wait 3000` 参数确保 Vue app 完全挂载
- ✅ 侧边栏渲染后提取到完整 27 条链接（26 个文档 + 1 入口）
- ✅ 5 页采样 S1-S12 检查：33/60 pass, 6 fixable fail, 21 skip
- ✅ 全量 crawl 26/26 成功，归档到 my-wiki `30-raw/local/operation/taptap-official-guidelines/` 下

## What Went Wrong — Pipeline Gaps

### GAP-S1: `extraction.fetch_options` not consumed by `buildScraplingExtractionArgs`

| Attribute | Value |
|---|---|
| **Classification** | **S-line** (Strategy configuration expresses intent) → **P-line** (Pipeline lacks consumer) |
| **Severity** | P1 — blocks automatic crawl for all SPA sites |
| **Location** | `scripts/lib/scrapling-extraction-args.mjs` (line 30-63) |

**Problem**: The strategy file declares `extraction.fetch_options` (network-idle, wait, headless), but `buildScraplingExtractionArgs` only handles `selectors.content` → `-s` or `--ai-targeted`. The `fetch_options` block is silently ignored.

**Expected behavior**: When strategy declares `extraction.fetch_options`, the pipeline should translate them into scrapling CLI arguments:

```yaml
# Strategy declaration (what we want to work)
extraction:
  fetch_options:
    network_idle: true    # → --network-idle
    wait_ms: 3000         # → --wait 3000
    headless: true         # → --headless
```

**Current workaround**: Manual invocation of `scrapling extract fetch` with flags hardcoded.

### GAP-S2: SPA empty-shell detection missing in Protection Identifier

| Attribute | Value |
|---|---|
| **Classification** | **S-line** (explore Protection Identifier heuristic gap) |
| **Severity** | P1 — causes explore to produce incorrect auto-generated scaffolds |
| **Location** | `scripts/explore/protection_identifier.py` (or equivalent in `main.py`) |

**Problem**: Explore's Phase D (Protection Identification) detects Cloudflare (403 + "Just a moment..."), Turnstile (403 + cf-turnstile), rate-limit (429), and login-wall (redirect to /login). However, it has **no detection for SPA empty shells** — when scrapling-get returns HTTP 200 with a 2267-byte `<div id="sub-app"></div>` shell, it is classified as "success" and "protection: none".

**Consequence**: The auto-generated scaffold is completely wrong:
- `page_type: static_article` (should be `dynamic_content`)
- `engine: scrapling-get` (should be `scrapling-fetch`)
- No content structure detected (nav_sections: [], tables: 0)

**Proposed detection heuristics** (any one triggers SPA classification):
1. Content length < 3000 bytes (SPA shells tend to be tiny)
2. Single empty mount point (e.g., `<div id="app"></div>`, `<div id="root"></div>`, `<div id="sub-app"></div>`)
3. `<body>` text length < 20 characters
4. Multiple `<script type="module">` + `<link rel="modulepreload">` tags (Vue/React SPA pattern)

## Remaining Pipeline Quality Issues (P-line, non-blocking)

| ID | Issue | Impact | Pages Affected |
|---|---|---|---|
| KI-1 | S5 Escape artifacts (`\*` residues) — scrapling MD converter leaves backslashes | Cosmetic | 3/5 samples |
| KI-2 | S1 Image retention skewed for table-heavy pages (22→7 in game-jump) | Moderate: decorative images filtered | 1/5 samples |
| KI-3 | S6 Table row deviation (rowspan/colspan merge→MD cell split) | Minor: table readability | 2/5 samples |

These are tracked in `sites/strategies/rep.taptap.cn/strategy.md` Known Issues table.

## Run Artifacts

- **Strategy**: `/Users/nantasmac/projects/agentic/chrome-agent/sites/strategies/rep.taptap.cn/strategy.md`
- **Samples + self-check**: `/Users/nantasmac/projects/agentic/chrome-agent/outputs/20260626T072200-explore-rep-taptap-cn-samples/`
- **Explore output**: `/Users/nantasmac/projects/agentic/chrome-agent/outputs/20260626T071416-explore-rep-taptap-cn-docs-taprep-about/`
- **S1-S12 raw results**: 5 documents, 33/60 pass, 6 fixable fail, 21 skip

## Next Steps

This issue must be resolved in the chrome-agent repository.

1. **Fix GAP-S2 first** (unblocks all downstream): Add SPA empty-shell detection to Protection Identifier → enables correct auto-scaffold generation
   - File: `scripts/explore/protection_identifier.py` (or inline in `main.py`)
   - Heuristic: content length < threshold OR empty mount point OR body text < threshold
2. **Fix GAP-S1** (enables automatic crawl): Extend `buildScraplingExtractionArgs` in `scripts/lib/scrapling-extraction-args.mjs` to consume `extraction.fetch_options`
   - Map `network_idle: true` → `--network-idle`
   - Map `wait_ms: N` → `--wait N`
   - Map `headless: false` → `--no-headless`
3. **Create openspec change proposal** for each gap
4. **Implement fixes**
5. **Re-run to verify**: `chrome-agent explore https://rep.taptap.cn/docs/taprep-about` should auto-detect SPA and produce correct `extraction.engine: scrapling-fetch` scaffold
6. **Post-fix**: Can run `chrome-agent crawl` with `--from-domain rep.taptap.cn` for automatic re-crawl
