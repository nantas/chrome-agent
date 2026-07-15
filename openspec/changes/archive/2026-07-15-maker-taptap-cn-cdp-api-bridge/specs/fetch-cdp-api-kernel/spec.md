# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch-cdp-api-kernel`
- 来源: `proposal.md` / grill-with-docs session
- 变更类型: new
- 用户确认摘要: 经 grill 确认，新增 CDP→REST API bridge 作为 fetch 能力的新执行路径。接收外部 `CdpApiEvalFn` callback（由外层 `.mjs` 管理 CDP WebSocket），Python 侧只做编排和缓存。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: CDP API Bridge Fetch

The system SHALL provide a fetch phase implementation at `scripts/pipeline/pipeline/phases/fetch_cdp_api.py` that retrieves content from RESTful JSON APIs by executing JavaScript `fetch()` calls within a live browser page context via CDP `Runtime.evaluate`.

The module SHALL NOT manage CDP WebSocket connections directly. It SHALL receive an `eval_fn` callback of signature `Callable[[str], Optional[str]]` that accepts a JavaScript expression string and returns the `result.value` of a `Runtime.evaluate` call, or `None` on failure.

#### Scenario: Successful list and content retrieval

- **WHEN** `run_fetch_cdp_api()` is called with a valid strategy containing `api.auth` and `api.endpoints`, a project ID, and a working `eval_fn` callback
- **THEN** the system SHALL:
  1. Read the Bearer token from `localStorage` via `eval_fn`
  2. Call the list API endpoint to obtain the file manifest
  3. Filter files by the optional `path_prefix` parameter
  4. For each matching file, call the content API endpoint
  5. Write content (Markdown text) to `.cache/chrome-cdp/<domain>/<safe_path>.json`
  6. Produce and return `extraction_results.json`-compatible results dict

#### Scenario: Token extraction failure

- **WHEN** `eval_fn` returns `None` or throws when reading the token from localStorage
- **THEN** the system SHALL log the error and return an empty results dict with a failure status

#### Scenario: List API failure

- **WHEN** the list API call via `eval_fn` fails or returns unexpected data
- **THEN** the system SHALL log the error and return an empty results dict with a failure status

#### Scenario: Content API failure for individual file

- **WHEN** a single content API call fails (not the whole batch)
- **THEN** the system SHALL log a warning for that file, skip it, and continue processing remaining files

### Requirement: Rate Limiting Between API Calls

The system SHALL enforce a configurable delay between successive content API calls to avoid triggering server-side rate limits.

#### Scenario: Batch content retrieval with rate limiting

- **WHEN** `run_fetch_cdp_api()` processes multiple files
- **THEN** it SHALL sleep for `batch_delay_sec` (default 0.3s) between each `eval_fn` invocation

### Requirement: Cache Reuse

The system SHALL check the `.cache/` directory before fetching content, and skip already-cached files unless `re_fetch` is True.

#### Scenario: Cache hit

- **WHEN** a file exists in `.cache/chrome-cdp/<domain>/<safe_path>.json` and `re_fetch` is False
- **THEN** the system SHALL skip the API call and mark the file as "skipped" in stats

#### Scenario: Re-fetch override

- **WHEN** `re_fetch` is True
- **THEN** the system SHALL re-fetch all files regardless of cache state

### Requirement: Extraction Results Output

The system SHALL produce output compatible with the downstream pipeline's `extraction_results.json` format, enabling direct consumption by the assemble phase.

#### Scenario: Results dict format

- **WHEN** fetch completes
- **THEN** the returned results dict SHALL contain entries keyed by safe file path, each with:
  - `title`: safe file path
  - `status`: `"ok"` or `"error"`
  - `content`: the Markdown text (on success)
  - `rendered_html`: `None` (no HTML intermediate)
