# Specification Delta

## Capability 对齐（已确认）

- Capability: `chrome-devtools-mcp-contract`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——chrome-devtools-mcp 作为诊断引擎，其契约与 Scrapling content-fetch 引擎有本质区别：输入侧重页面导航与诊断配置，输出侧重结构化证据（snapshot/网络/截图/性能），不产出正文提取

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — navigation and diagnostic parameters

The system SHALL define the input parameters for chrome-devtools-mcp, a diagnostic engine using Chrome DevTools Protocol for structured page evidence collection.

#### Scenario: Navigation parameter — url

- **WHEN** chrome-devtools-mcp navigates to a page
- **THEN** it SHALL accept a `url` parameter for `navigate_page` with `type: url`
- **AND** it SHALL support navigation types `back`, `forward`, and `reload`

#### Scenario: Navigation parameter — timeout

- **WHEN** chrome-devtools-mcp navigates to a page
- **THEN** it SHALL accept a `timeout` in milliseconds for page load wait

#### Scenario: Navigation parameter — init script

- **WHEN** chrome-devtools-mcp navigates to a page
- **THEN** it SHALL accept an optional `initScript` JavaScript string to execute on each new document before other scripts

#### Scenario: Page management — new page

- **WHEN** creating a new browsing context
- **THEN** the `new_page` action SHALL accept `url`, optional `background` boolean (default `false`), optional `isolatedContext` string for cookie/storage isolation
- **AND** the `select_page` action SHALL accept `pageId` and optional `bringToFront`

#### Scenario: Diagnostic action — take_snapshot

- **WHEN** collecting page structure evidence
- **THEN** the `take_snapshot` action SHALL accept optional `verbose` boolean (default `false`) for full a11y tree detail
- **AND** it SHALL accept optional `filePath` for saving to disk

#### Scenario: Diagnostic action — take_screenshot

- **WHEN** capturing visual evidence
- **THEN** the `take_screenshot` action SHALL accept `format` (png/jpeg/webp, default png), optional `uid` for element targeting, optional `fullPage` boolean, optional `filePath`
- **AND** for jpeg/webp formats, `quality` parameter SHALL be supported (0-100)

#### Scenario: Diagnostic action — list_network_requests

- **WHEN** collecting network evidence
- **THEN** the `list_network_requests` action SHALL accept optional `pageSize`, `resourceTypes` filter, and `includePreservedRequests` boolean

#### Scenario: Diagnostic action — list_console_messages

- **WHEN** collecting console evidence
- **THEN** the `list_console_messages` action SHALL accept optional `pageSize`, `types` filter, and `includePreservedMessages` boolean

#### Scenario: Diagnostic action — performance trace

- **WHEN** collecting performance evidence
- **THEN** the `performance_start_trace` action SHALL accept optional `reload` boolean (default `true`) and `autoStop` boolean (default `true`)

#### Scenario: Diagnostic action — evaluate_script

- **WHEN** executing JavaScript in the page context
- **THEN** the `evaluate_script` action SHALL accept a JavaScript `function` declaration and optional `args` array of element UIDs

#### Scenario: Interaction actions

- **WHEN** performing page interaction for diagnosis
- **THEN** the engine SHALL support `click`, `fill`, `fill_form`, `hover`, `press_key`, `type_text`, `drag`, `upload_file` actions
- **AND** each interaction SHALL accept `includeSnapshot` boolean (default `false`) for post-action state capture

#### Scenario: Wait strategy

- **WHEN** waiting for page state
- **THEN** the `wait_for` action SHALL accept a non-empty `text` array and optional `timeout` in milliseconds

#### Scenario: Session mode — managed browser context

- **WHEN** chrome-devtools-mcp is used
- **THEN** it SHALL operate in a managed browser context by default (no user-side Chrome session)
- **AND** it SHALL support `--autoConnect` and `--wsEndpoint` modes for live-attach to existing Chrome instances

#### Scenario: Authentication boundary

- **WHEN** chrome-devtools-mcp is used for diagnostic evidence on authenticated pages
- **THEN** the target page SHALL require explicit user approval
- **AND** diagnostic collection SHALL remain read-only

### Requirement: Output contract — diagnostic evidence structure

The system SHALL define the output structure for chrome-devtools-mcp, which produces diagnostic evidence rather than extracted content.

#### Scenario: Snapshot output

- **WHEN** `take_snapshot` completes
- **THEN** the output SHALL be an accessibility-tree-based text representation of the page, listing elements with unique identifiers (uid)
- **AND** the snapshot SHALL indicate the currently selected element in DevTools (if any)

#### Scenario: Screenshot output

- **WHEN** `take_screenshot` completes
- **THEN** the output SHALL be an image in the requested format (png/jpeg/webp)
- **AND** when `filePath` is provided, the image SHALL be saved to that path

#### Scenario: Network evidence output

- **WHEN** `list_network_requests` completes
- **THEN** the output SHALL list requests with reqid, URL, method, status, resource type, timing, and response size metadata

#### Scenario: Console evidence output

- **WHEN** `list_console_messages` completes
- **THEN** the output SHALL list messages with msgid, type (log/warn/error/info), text content, and source information

#### Scenario: Performance evidence output

- **WHEN** `performance_start_trace` + `performance_stop_trace` complete
- **THEN** the output SHALL include Core Web Vitals (LCP, INP, CLS) insight sets and performance trace data
- **AND** `performance_analyze_insight` SHALL provide detailed insight breakdown per insight name

#### Scenario: Script evaluation output

- **WHEN** `evaluate_script` completes
- **THEN** the return value SHALL be JSON-serializable and contain the function's return value

#### Scenario: Metadata for diagnostic outputs

- **WHEN** any diagnostic action completes
- **THEN** the output SHALL make it explicit it was produced by `engine: chrome-devtools-mcp`
- **AND** the output SHALL NOT attempt to produce a "content extraction" equivalent—this is diagnostic evidence, not content retrieval

### Requirement: Error contract — failure classification

The system SHALL define error categories for chrome-devtools-mcp failures.

#### Scenario: Error categories

- **WHEN** chrome-devtools-mcp encounters a failure
- **THEN** the error SHALL be classified into one of: connection, navigation, selector, evaluation, page_limit

| Error Category | Description |
|---------------|-------------|
| connection | MCP server not running, CDP WebSocket failure, browser crash |
| navigation | Navigation timeout, target URL unreachable, page load failure |
| selector | wait_for timeout, element uid not found in snapshot, click/fill target missing |
| evaluation | JavaScript execution error in page context |
| page_limit | Cannot close last open page |

#### Scenario: Recommended next action per connection error

- **WHEN** a connection error occurs (MCP server unavailable)
- **THEN** the recommended next action SHALL be: restart MCP server; verify launch configuration; if persistent, fall back to `chrome-cdp` if an approved live Chrome session exists

#### Scenario: Recommended next action per navigation error

- **WHEN** a navigation error occurs (timeout, unreachable)
- **THEN** the recommended next action SHALL be: retry with increased timeout; check if blocking requires `scrapling-stealthy-fetch` first; if persistent, report as unreachable

### Requirement: Smoke-check scenario — diagnostic evidence on a protected page

The system SHALL validate the chrome-devtools-mcp contract against a known diagnostic target.

#### Scenario: x.com page diagnostics

- **WHEN** chrome-devtools-mcp is tested against `https://x.com/hashtag/StreetFighter6?src=hashtag_click`
- **THEN** the diagnostic output SHALL capture: page title and final URL (even if redirected to login), accessibility snapshot exposing the page structure (login modal or logged-in content), and network requests showing document and fetch/XHR responses
- **AND** if the page redirects to `/i/flow/login`, the diagnostic evidence SHALL confirm the redirect target and that `window.__INITIAL_STATE__` contains empty tweet entities
- **AND** the output SHALL be usable as evidence for routing decisions (e.g., "this domain requires chrome-cdp for authenticated content")
