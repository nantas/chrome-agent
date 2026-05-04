# Verification Checkpoints

## Spec-to-Implementation Coverage Matrix

### mediawiki-api-extraction spec

| Requirement | Implementation Location | Status |
|-------------|------------------------|--------|
| 管线触发条件 | `scripts/chrome-agent-cli.mjs` `runCrawl()` — API config check before Scrapling preflight | ✓ Implemented |
| API 端点探测 | `scripts/mediawiki-api-extract` `probe_api_endpoint()` | ✓ Implemented |
| Phase A — 页面发现 | `scripts/mediawiki-api-extract` `run_phase_a()`, `discover_all_pages()`, `discover_categories()` | ✓ Implemented |
| Phase B — 内容提取 | `scripts/mediawiki-api-extract` `run_phase_b()`, `convert_wikitext_to_markdown()` | ✓ Implemented |
| Phase C — 输出组装 | `scripts/mediawiki-api-extract` `run_phase_c()` | ✓ Implemented |
| Fallback 到 Scrapling | `scripts/mediawiki-api-extract` exit codes + `chrome-agent-cli.mjs` fallback logic | ✓ Implemented |
| 输出格式契约 | `convert_wikitext_to_markdown()` — YAML frontmatter, wiki link conversion, template expansion | ✓ Implemented |

### site-strategy-schema spec (modified)

| Requirement | Implementation Location | Status |
|-------------|------------------------|--------|
| API 提取配置 (optional `api` field) | `balatrowiki.org/strategy.md`, `vampire.survivors.wiki/strategy.md` | ✓ Added |
| API Capabilities 受控词汇表 | Strategy files use `page_list`, `category_lookup`, `wikitext_parse` | ✓ Valid |
| API Taxonomy 配置 | `taxonomy.list_pages`, `taxonomy.category_filters` in strategy files | ✓ Added |
| API Filename 配置 | `filename.replacements` in strategy files | ✓ Added |
| API Output 配置 | `output.frontmatter_fields`, `output.template_map` in strategy files | ✓ Added |

## Validation Evidence

### balatrowiki.org full crawl (2026-05-04)

- **Phase A**: 468 pages discovered, categories resolved for all pages, 16 list pages fetched
- **Phase B**: 468/468 pages extracted (100% success at concurrency=3; 453/468 at concurrency=5 due to rate limiting)
- **Phase C**: 453-468 pages written across 17 directories, `_index.md` and per-directory `index.md` generated
- **Frontmatter quality**: `Joker.md` correctly extracts `effect: +4 Mult`, `rarity: Common`, `type: Additive Mult`, `buyprice: 2`
- **No wikitext artifacts**: Individual pages have no `{{...}}` residue, no `[[Category:...]]` lines
- **Directory classification**: Misc ratio 10.5% (target was <5%; acceptable for v1 given category mapping complexity)

### vampire.survivors.wiki (validation pending)

- Strategy file updated with `api` field
- Full crawl not executed in this session

### Fallback validation

- Exit code 10 (API_UNREACHABLE) → caller falls back to Scrapling ✓
- Exit code 11 (PHASE_A_FAILURE) → caller falls back to Scrapling ✓
- Exit code 12 (PHASE_B_FAILURE, >50%) → caller falls back to Scrapling ✓
- Exit code 1 (PARTIAL_SUCCESS) → caller accepts partial result ✓
- Simulated via code review; live test would require blocking the API endpoint

## Strategy File Validation

| File | api.platform | api.base_url | api.capabilities | Registry Entry | backend field |
|------|-------------|-------------|-----------------|---------------|--------------|
| `balatrowiki.org/strategy.md` | mediawiki | https://balatrowiki.org/api.php | page_list, category_lookup, wikitext_parse | ✓ Present | weird-gloop-mediawiki-1.45 |
| `vampire.survivors.wiki/strategy.md` | mediawiki | https://vampire.survivors.wiki/api.php | page_list, category_lookup, wikitext_parse | ✓ Present | weird-gloop-mediawiki-1.45 |

## Crawl Command Integration Validation

| Scenario | Expected Behavior | Verified |
|----------|-------------------|----------|
| Strategy has `api.platform: mediawiki` | Route to API pipeline | ✓ Code review |
| Strategy has no `api` field | Route to Scrapling | ✓ Backward compatible |
| API pipeline fails (exit >= 10) | Fall through to Scrapling | ✓ Code review |
| API pipeline succeeds | Return with `extraction_method: mediawiki_api` | ✓ Code review |
| API script missing | Fall through to Scrapling | ✓ Code review |

## DPL Table Restoration & Noise Cleanup (Tasks 5.1-5.5)

| Check | Result | Verified |
|-------|--------|----------|
| HTML comments (`<!-- ... -->`) stripped | 0 comments in output | ✓ |
| `<dpl>...</dpl>` replaced with data-driven table | Jokers/index.md contains Markdown table | ✓ |
| DPL table columns from frontmatter_fields | Page + 9 data columns (image merged into Page) | ✓ |
| Page column: image + link (matching original DPL) | `![name](url)<br>[name](file)` | ✓ |
| Image URLs: spaces encoded as %20 | `file/Abstract%20Joker.png` | ✓ |
| File paths: spaces replaced with underscores | 0 files with spaces in names | ✓ |
| H1 title added to all sub-pages | `# Joker` after frontmatter | ✓ |
| Redundant list page files removed | Jokers.md deleted, index.md only | ✓ |
| frontmatter_fields extended (number, image, unlock, activation) | All fields extracted where present | ✓ |
