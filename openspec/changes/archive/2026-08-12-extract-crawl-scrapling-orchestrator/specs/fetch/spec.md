# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch`
- 来源: `proposal.md` / 已确认 capabilities（用户确认方案）
- 变更类型: `modified`
- 用户确认摘要: 仅 fetch（Modified）；纯结构重构，crawl 外部行为零变更；C4 候选方案用户已确认（提取边界、参数对象化、deps seam 粒度）

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: crawl-scrapling-orchestrator-is-a-seam-module

The scrapling crawl orchestrator (`runCrawlScrapling`) SHALL live in `scripts/lib/crawl_scrapling.mjs`, not inline in `scripts/chrome-agent-cli.mjs`. It SHALL accept its operating context as a `ctx` object (repo_root, repo_ref, resolution_mode, run_dir, report_path, manifest_path, emit_report, target_url, strategy, doc, start_page, matching_page, entry_points) plus an `opts` object (max_pages, concurrency, from_manifest, ...), replacing the prior 12 positional parameters. Because the function depends on ~26 internal cli.mjs helpers (filesystem, result-builders, scrapling/obscura fetch, conversion), it SHALL receive them via an injected `api` bundle (flat object: `api.fs` + the named helper functions) rather than via circular imports. Only `runCrawlScrapling` itself moves; all helpers stay in cli.mjs. This makes the traversal/manifest/handoff logic unit-testable with a stub `api` (real pure helpers, stubbed side-effecting helpers), without spawning Chrome or touching a real filesystem.

#### Scenario: orchestrator-extractable-and-importable
- **WHEN** the orchestrator module is imported in a test
- **THEN** `runCrawlScrapling` SHALL be callable with a `ctx` object + an `api` bundle whose side-effecting members (fs, fetch/preflight helpers, port/server helpers) are stubbed, exercising traversal/manifest/handoff without spawning Chrome

#### Scenario: crawl-output-byte-identical
- **WHEN** the same crawl command runs before and after extraction (same target, strategy, opts)
- **THEN** the manifest, report, and merged output SHALL be byte-identical (pure structural refactor, no behavioral change)

#### Scenario: api-bundle-built-once-in-cli
- **WHEN** cli.mjs delegates to `runCrawlScrapling` at its 3 call sites (line 2202/2365/2369)
- **THEN** it SHALL build the `api` bundle once (real `fs` + real helpers + `buildScraplingExtractionArgs` already imported) and pass it, alongside `ctx` + `opts`; no circular import exists between crawl_scrapling.mjs and cli.mjs
