# Writeback

## Change: migrate-discovery-to-explore

### Writeback Targets

| # | Target | Status |
|---|--------|--------|
| 1 | `AGENTS.md` §2 Capability Framework | ✅ No change needed — already reflects target state (`scripts/explore/`, pipeline 不再自行发现页面) |
| 2 | `docs/architecture/01-overview.md` | ✅ Updated: diagram (五阶段→四阶段), directory structure (removed discovery from pipeline, added to explore) |
| 3 | `docs/architecture/07-explore-workflow.md` | ✅ No change needed — 8-step pipeline unchanged, discovery modules are utility modules used within it |

### Changes Applied

#### `docs/architecture/01-overview.md`
- Architecture diagram: "五阶段管线" → "四阶段管线", removed "discovery →", flow is now "fetch → convert → assemble → link-fix + validation"
- Directory structure:
  - Removed from pipeline section: `homepage_parser.py`, `page_assigner.py`, `discovery_homepage.py`, `discovery_allpages.py`, `discovery.py`
  - Added to explore section: all 5 discovery modules after `api_discovery.py`

#### `docs/architecture/02-pipeline-flow.md`
- Overview: "五种阶段" → "四种阶段", added note that page manifest comes from explore via `--from-manifest`
- Data flow diagram: removed "Homepage Discovery" and "Allpages Discovery" branches, kept only `--from-manifest` path; removed `discovery_summary.json` from output

### Unchanged

- `AGENTS.md` §2: Already correct
- `07-explore-workflow.md`: 8-step pipeline unchanged, discovery modules are utility modules
