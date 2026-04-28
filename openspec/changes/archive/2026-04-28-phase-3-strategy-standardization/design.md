# Design

## Context

Phase 1 and Phase 2 have established the governance foundation (AGENTS.md, metadata contract model) and frozen engine contracts (5 engines with input/output/error dimensions). The existing `sites/` directory contains 5 files with 5 different ad-hoc structures, mixing site description, anti-crawl knowledge, and operational scripts. Phase 3 standardizes all of this into two queryable schemas.

The key insight from exploration is that site strategy and anti-crawl strategy are two distinct concerns:
- **Site strategy**: describes a site's page structure, extraction patterns, and which protections apply
- **Anti-crawl strategy**: describes a protection mechanism and an engine sequence to defeat it, reusable across multiple sites

This mirrors Phase 2's separation of concern between engine contracts (per-engine behavior) and the aggregation index (cross-engine mapping).

## Goals / Non-Goals

**Goals:**
1. Define structured YAML frontmatter schemas for both site and anti-crawl strategies
2. Establish a two-directory layout: `sites/anti-crawl/` (flat, by mechanism) + `sites/strategies/<domain>/` (folder per site)
3. Provide `registry.json` indexes for fast machine querying without reading full strategy files
4. Define controlled vocabularies for `protection_type`, `page_type`, and `protection_level`
5. Create `default.md` as the explicit Scrapling-first fallback for unmatched sites
6. Migrate 5 existing site files to the new structure, separating operational content into `_attachments/`
7. Encode governance constraints in AGENTS.md for registry.json maintenance

**Non-Goals:**
- No engine implementation changes
- No automatic strategy matching or scheduling (Phase 4 scope)
- No new engine additions
- No output lifecycle management (Phase 5 scope)

## Decisions

### Decision 1: Two-directory layout with shared anti-crawl

```
sites/
├── anti-crawl/
│   ├── cloudflare-turnstile.md
│   ├── login-wall-redirect.md
│   ├── cookie-auth-session.md
│   ├── rate-limit-api.md
│   ├── default.md
│   └── registry.json
│
├── strategies/
│   ├── fanbox.cc/
│   │   ├── strategy.md
│   │   └── _attachments/
│   ├── mp.weixin.qq.com/
│   │   └── strategy.md
│   ├── wiki.supercombo.gg/
│   │   └── strategy.md
│   ├── x.com/
│   │   ├── strategy.md
│   │   └── _attachments/
│   └── registry.json
```

**Rationale**: Anti-crawl strategies are named by mechanism (e.g., `cloudflare-turnstile.md`) not by origin site. Site strategies reference them via `anti_crawl_refs` in their frontmatter. This enables cross-site reuse: a new Cloudflare-protected site just adds `cloudflare-turnstile` to its refs.

Site strategies use folder-per-domain because a single site may have operational artifacts (`_attachments/`) that need to be co-located.

### Decision 2: Per-page anti_crawl_refs

The `anti_crawl_refs` field exists at two levels:
- **File level**: default for all pages in the site
- **Per-page override** (`structure.pages[].anti_crawl_refs`): for pages within a domain that differ

Example: x.com has `public_tweet` (no auth needed) and `hashtag_search` (login-wall required). The per-page override allows both to coexist in one strategy file.

**Rationale**: The site is the domain unit, but different pages within a domain can face different protections. This was the deciding factor for x.com being one file with multiple entry points.

### Decision 3: Dual index (registry.json + frontmatter)

Both `registry.json` and individual file frontmatter contain structured fields. The registry summarizes; the frontmatter is authoritative.

When inconsistency is detected, frontmatter wins. The registry is a convenience index for fast scanning — matching on `protection_type`, `page_types`, `pagination` etc. without opening every file.

**Rationale**: `registry.json` as a JSON file is more scriptable for automated tooling. But keeping frontmatter as the authoritative source follows the principle that data should live closest to its usage context. The registry is a generated summary, not a primary data store.

### Decision 4: Controlled vocabularies (closed for v1)

`protection_type` (anti-crawl): `none`, `cloudflare_turnstile`, `cloudflare_challenge`, `login_wall`, `cookie_auth`, `rate_limit`, `waf_generic`, `captcha`, `ip_block`

`page_type` (site-strategy): `static_page`, `static_article`, `dynamic_list`, `dynamic_content`, `search_results`, `binary_file`, `auth_gate`

`protection_level` (site-strategy): `low`, `medium`, `high`, `authenticated`, `variable`

New types require an openspec change to the respective spec.

**Rationale**: Closed vocabulary prevents drift and forces deliberate discussion about what makes a new type distinct. Open vocabulary risks accumulating near-synonyms and eroding queryability.

### Decision 5: Default strategy as a registry entry

`default.md` is a named entry in `sites/anti-crawl/` with `protection_type: none` and `sites: []`. It encodes the canonical Scrapling-first escalation chain:

```
scrapling-get → scrapling-fetch → scrapling-stealthy-fetch → chrome-devtools-mcp (diagnostic)
```

This is NOT implicitly defined in AGENTS.md. It's an explicit strategy file so the query logic is uniform: "nothing matched? → use `default`".

**Rationale**: An explicit file is testable, documentable, and extensible. Implicit behavior hidden in agent logic is not.

### Decision 6: Operational content separation

The `_attachments/` directory houses scripts, configs, and progress files. The `strategy.md` body provides narrative description of extraction flow but does not embed executable code blocks.

**Rationale**: The fanbox.cc file at 336 lines is evidence that strategy data and operational scripts should not co-reside. Strategy files are for understanding what to do; attachments are for doing it.

### Decision 7: Registry-driven strategy discovery

The agent's query flow for unknown sites:

```
Unknown URL → observe signals
  ├─ Domain partial match in strategies/registry.json?      → read strategy.md
  ├─ Protection signals match anti-crawl/registry.json?     → apply anti-crawl strategy
  ├─ Structural similarity (page_types + pagination)?        → review relevant strategy
  └─ None match                                               → use default strategy
     ├─ Default fails → analysis flow → possibly create new strategy
```

No query DSL or database. Both registry.json files are small enough (5-20 entries each) for the agent to fully read and reason about.

### Decision 8: Engine names and escalation chain

Anti-crawl `engine_sequence` MUST use canonical engine identifiers from `engine-contracts` spec. The sequence MUST be a subsequence of the canonical escalation chain (`get → fetch → stealthy-fetch → chrome-devtools-mcp → chrome-cdp`). Skipping entries is allowed; reordering is not.

**Rationale**: This is the strongest coupling point between Phase 2 and Phase 3 contracts. Engine names are few and stable — strict coupling is safe. Error categories (from Phase 2) are referenced loosely by name but not duplicated.

## Risks / Migration

- **风险 1: x.com 合并为一文件**: x.com 当前有 `x.com-public-tweet.md` 和 `x.com-public-hashtag-search-login-gate.md` 两个文件，合并为 `strategies/x.com/strategy.md` 会丢失分离的历史。缓解措施：合并后的 strategy.md 在 body 中保留两个入口点的 provenance 引用，新的 frontmatter 包含两者的 page types。

- **风险 2: fanbox.cc 操作内容拆分**: `fanbox.cc-content-download.md` 包含大量嵌入的 bash 脚本和 cookie 提取命令。拆分到 `_attachments/` 后，部分内容属于"说明性示例"保留在 body 中，部分属于"可执行脚本"移入附件。缓解措施：保留关键的命令片段作为 body 中的引用示例（不带完整语境），完整的可执行脚本移入 `_attachments/`。

- **风险 3: registry.json 与 frontmatter 漂移**: 手动维护两个数据源可能产生不一致。缓解措施：AGENTS.md 明确声明 frontmatter 为权威来源；registry.json 仅为索引摘要。未来可添加验证脚本，但 v1 不强制。

- **风险 4: 受控词汇表不够用**: v1 的 8 种 protection_type 和 6 种 page_type 可能不覆盖所有实际场景。缓解措施：词汇表通过 openspec change 扩展，扩展流程已定义在各自的 spec 中。遇到新类型时先记录为 unclassified，后续通过 change 添加。
