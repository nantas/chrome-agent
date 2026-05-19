# CLI Domain: Workflows — Merged Spec

> **Merged from**: `scrapling-first-browser-workflow`, `strategy-guided-crawl`, `scrape-command`, `full-url-parameterization`
> **Purpose**: Defines the core CLI workflows: Scrapling-first routing, strategy-guided crawl (with Markdown output, phases, concurrency), strategy-free scrape, and full URL parameterization for links and images.

---

## Part 1 — Source: `scrapling-first-browser-workflow`

### Requirement: Scrapling-first routing

Scrapling is the first tool path for all webpage grabbing tasks: public content, dynamic pages, protected pages, batch, and read-only logged-in sessions.

#### Scenario: Public content request
- **WHEN** user asks to get content from a public URL
- **THEN** workflow starts with Scrapling before `chrome-devtools-mcp` or `chrome-cdp`

#### Scenario: Dynamic or protected page request
- **WHEN** page needs JS rendering, stealth, session continuity, or bot-blocking mitigation
- **THEN** workflow selects matching Scrapling fetcher/session before escalating

### Requirement: Default workflow ordering

Route (Content Retrieval vs Platform/Page Analysis) → Scrapling CLI preflight → Scrapling fetcher selection → fallback only on verified triggers.

### Requirement: Fallback boundaries

- `chrome-devtools-mcp` for diagnostic evidence (DOM, accessibility, network, screenshots)
- `chrome-cdp` for live-session continuity
- Choose by diagnostic vs session continuity needs, NOT by tool duplication

### Requirement: Authenticated read-only boundary

Explicit user approval required. Read-only by default. Session reuse failure → record and stop. Redirect to login → stop and record failure.

### Requirement: Environment contract

`SCRAPLING_CLI_PATH` as canonical reference. No host-specific absolute paths in git-tracked files.

### Requirement: Verification baseline

Covers: static public page, dynamic page, article with images, protected page attempt. Logged-in experiments deferred without explicit approval.

---

## Part 2 — Source: `strategy-guided-crawl`

### Requirement: Default Markdown output

`crawl` defaults to Markdown output. Each page produces `.md` file via `scrapling extract`. Intermediate `.html` cleaned up after conversion.

### Requirement: Optional merged output

`--merge` → concatenate all `.md` files into `crawl-output.md` with table of contents.

### Requirement: Concurrent Markdown conversion

Default concurrency: 5. Custom: `--concurrency N`.

### Requirement: Phase 2 partial failure semantics

Phase 1 success + Phase 2 failures → `partial_success`. Failed URLs in `phase2.failed_urls`. Successful `.md` files remain.

### Requirement: Phase-based execution

| `--phase` | MediaWiki API | Scrapling |
|-----------|--------------|-----------|
| `discover` | allpages/homepage discovery | Link discovery |
| `fetch` | API parse + cache write | Download + cache write |
| `convert` | Cache read + HTML→MD | Cache read + HTML→MD |
| `assemble` | Index + link fix | Link fix + merge |
| `all` | discover → fetch → convert | discover → fetch → convert |

### Requirement: unified-cli-phase-semantics

`--phase convert` = read cache → convert → output Markdown (consistent across both paths).

### Requirement: keep-html-semantics (deprecated)

`--keep-html` deprecated. HTML persisted via `--phase fetch` cache. Warning emitted but not blocking.

### Requirement: no-markdown-alignment

`--no-markdown` skips conversion. Suggests `--phase fetch` as recommended HTML-only workflow.

---

## Part 3 — Source: `scrape-command`

### Requirement: Scrape command surface

`chrome-agent scrape <url>` — strategy-free recursive crawling.

### Requirement: No strategy dependency

`scrape` proceeds without site-strategy. If strategy exists, it is ignored.

### Requirement: Self-discovered link traversal

- Same-domain filtering (default `--same-domain`)
- `--match <glob>` for URL pattern filtering
- Dedup and cycle prevention

### Requirement: Bounded traversal

`--max-pages` (default 10).

### Requirement: Default Markdown output

Each page produces `.md` file. `--no-markdown` retains `.html`.

### Requirement: Structured directory output

Output reflects URL pathname hierarchy. Internal links rewritten as relative paths.

### Requirement: Optional merged output

`--merge` → `scrape-output.md` with table of contents.

### Requirement: Concurrent Markdown conversion

Default: 5. Custom: `--concurrency N`.

### Requirement: Fetcher override

`--fetcher <name>` (default: `scrapling-get`).

### Requirement: Partial failure semantics

Phase 1 or Phase 2 partial failure → `partial_success`. Failed URLs recorded in manifest.

### Requirement: HTML intermediate cleanup

`.html` files cleaned after Phase 2. `--keep-html` retains them as `disposable` artifacts.

---

## Part 4 — Source: `full-url-parameterization`

### Requirement: convert-internal-links-to-full-urls

`convert_links_to_md(html: str, wiki_domain: str) -> str` converts:
- `/wiki/*` → `https://{wiki_domain}/wiki/*`
- `/images/*` → `https://{wiki_domain}/images/*`
- Any `/...` → `https://{wiki_domain}/...`
- Preserves external URLs and anchor-only links
- Strips `javascript:` links to text only
- `wiki_domain` is REQUIRED (no default — raises TypeError if missing)

### Requirement: convert-internal-images-to-full-urls

`convert_images_to_md(html: str, wiki_domain: str, skip_patterns: list[str] = []) -> str` converts:
- `/images/*` src → `https://{wiki_domain}/images/*`
- `skip_patterns` — regex patterns; matching images excluded
- External images preserved unchanged

### Requirement: base-url-from-strategy

`wiki_domain` extracted from strategy `domain` field or `api.base_url`. Passed to converter functions.
