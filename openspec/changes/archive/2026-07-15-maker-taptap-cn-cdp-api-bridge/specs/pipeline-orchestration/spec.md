# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-orchestration`
- 来源: `proposal.md` / grill-with-docs session
- 变更类型: modified
- 用户确认摘要: 经 grill 确认，orchestrator 需新增 `api.platform: rest` + `backend: cdp-api-bridge` 的验证、convert passthrough 和 backend 守卫。fetch 阶段不通过 orchestrator 路由——`eval_fn` 无法序列化为 CLI args，由外层 `.mjs` 直接 import `run_fetch_cdp_api()`。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: REST Platform Recognition

The `run_pipeline()` function SHALL recognize `api.platform: rest` in strategy frontmatter and skip MediaWiki-specific initialization (API endpoint probe, `ApiClient` construction).

#### Scenario: Rest platform skips API probe

- **WHEN** `run_pipeline()` is called with a strategy containing `api.platform: rest`
- **THEN** it SHALL skip `probe_api_endpoint()` and set `base_url` to `None`

### Requirement: Backend Validation

The `run_pipeline()` function SHALL validate the strategy's `backend` field against a set of known backends during pipeline initialization. Unknown backends SHALL cause early exit with `EXIT_STRATEGY_ERROR`.

#### Scenario: Known backend passes validation

- **WHEN** `run_pipeline()` is called with `backend: cdp-api-bridge`
- **THEN** validation SHALL pass silently

#### Scenario: Unknown backend causes graceful failure

- **WHEN** `run_pipeline()` is called with a strategy that declares an unknown `backend` value
- **THEN** it SHALL log an error and return `EXIT_STRATEGY_ERROR`

### Requirement: Passthrough Convert for REST Platforms

When `api.platform` is `rest`, the convert phase SHALL be skipped — content returned by the CDP API bridge is already Markdown and does not require HTML-to-Markdown conversion.

#### Scenario: Rest platform skips convert

- **WHEN** `run_pipeline()` is called with `--phase convert` (or `--phase all`) and the strategy declares `api.platform: rest`
- **THEN** the convert phase SHALL read cached content directly and populate `extraction_results.json` without invoking `HtmlToMarkdownConverter` or any HTML parsing

#### Scenario: Results are directly passed through

- **WHEN** the passthrough convert processes cached REST API content
- **THEN** each entry in `extraction_results.json` SHALL have:
  - `content`: the raw Markdown from the API (unmodified)
  - `rendered_html`: `None`
  - `status`: `"ok"`

### Requirement: CDP API Bridge Fetch (External Orchestration)

The CDP API bridge fetch SHALL NOT be invoked from within `run_pipeline()`. Because `eval_fn` requires a live CDP WebSocket connection that cannot be serialized into CLI arguments, the fetch phase for `backend: cdp-api-bridge` sites SHALL be called externally — by the `.mjs` layer importing `run_fetch_cdp_api()` directly and passing an `eval_fn` callback that wraps `cdp.mjs evalraw`.

The orchestrator's responsibility is limited to validating the strategy's `backend` field (see Backend Validation) and executing the passthrough convert and assemble phases for `rest` platform strategies.

#### Scenario: Fetch phase for cdp-api-bridge is handled externally

- **WHEN** `run_pipeline()` is called with `--phase fetch` and a strategy declaring `backend: cdp-api-bridge`
- **THEN** it SHALL log a message indicating that fetch should be performed externally via `fetch_cdp_api.run_fetch_cdp_api()` and return `EXIT_SUCCESS`

## MODIFIED Requirements

### Requirement: Phase Execution with Backend-Specific Routing

The `run_pipeline()` function SHALL use the strategy's `backend` field for validation and convert routing. The existing behavior for `backend: <not set>` (implicitly MediaWiki) SHALL remain unchanged. Unknown backends SHALL cause `EXIT_STRATEGY_ERROR`.

#### Scenario: Default backend uses mediawiki fetch

- **WHEN** `run_pipeline()` is called with a strategy that has `api.platform: mediawiki` (explicit or implicit)
- **THEN** it SHALL route to `run_fetch()` as before

#### Scenario: Unknown backend causes graceful failure

- **WHEN** `run_pipeline()` is called with a strategy that declares an unknown `backend` value
- **THEN** it SHALL log an error and return `EXIT_STRATEGY_ERROR`
