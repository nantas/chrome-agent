# Specification Delta

## Capability 对齐（已确认）

- Capability: `chrome-cdp-contract`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——chrome-cdp 作为实时会话延续引擎，需要用户已打开的 Chrome 标签页，且已认证状态只读。evidence: fanbox.cc content download (336 行文档) + x.com auth session

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract — live session prerequisites

The system SHALL define the prerequisites and parameters for chrome-cdp, a live-session continuity engine that operates on an already-open Chrome browser tab.

#### Scenario: Live session requirement

- **WHEN** chrome-cdp is used
- **THEN** a Chrome browser with remote debugging enabled SHALL already be running
- **AND** an explicit user-approved target page or tab SHALL be identified before any operation

#### Scenario: User approval prerequisite

- **WHEN** the target involves an authenticated or logged-in state
- **THEN** explicit user approval of the target page SHALL be obtained before chrome-cdp is invoked
- **AND** the run SHALL remain read-only by default unless the user explicitly broadens scope

#### Scenario: Navigation action

- **WHEN** chrome-cdp navigates within an approved live tab
- **THEN** navigation SHALL NOT cause session loss, logout, or page reset
- **AND** if navigation results in redirect to login, the operation SHALL stop and record failure

#### Scenario: DOM interaction

- **WHEN** chrome-cdp extracts page information
- **THEN** it SHALL support DOM queries via JavaScript evaluation (querySelector, innerText, attribute extraction)
- **AND** it SHALL support accessibility snapshots of the current page state

#### Scenario: Cookie extraction

- **WHEN** chrome-cdp extracts session cookies for downstream operations (e.g., authenticated file download)
- **THEN** it SHALL support CDP `Network.getCookies` with domain/URL filtering
- **AND** extracted cookies SHALL only be used for read-only operations within the approved scope

#### Scenario: Session limitations

- **WHEN** chrome-cdp is used
- **THEN** the CDP daemon SHALL be subject to a 20-minute inactivity auto-exit
- **AND** after navigation, target discovery SHALL be re-performed (daemon may disconnect on nav)
- **AND** the "Allow debugging" prompt SHALL be accepted by the user before connection

#### Scenario: Fallback relationship

- **WHEN** chrome-cdp is selected
- **THEN** it SHALL only be used as the live-session continuity fallback after Scrapling-first has been attempted (or when live-session continuity is known up front as essential)
- **AND** it SHALL NOT be used as the default browser automation path for tasks that can be handled by Scrapling or chrome-devtools-mcp

### Requirement: Output contract — live-session extraction

The system SHALL define the output structure for chrome-cdp, which produces page content from an approved live Chrome session.

#### Scenario: Content extraction output

- **WHEN** chrome-cdp extracts page content
- **THEN** the output SHALL include: page title, current URL, extracted text content (from DOM), and downloadable media URLs when present
- **AND** the output SHALL indicate `engine: chrome-cdp` and whether the session was authenticated

#### Scenario: Cookie extraction output

- **WHEN** chrome-cdp extracts cookies via CDP
- **THEN** the output SHALL include: cookie name, domain, and flags (httpOnly, secure) for each relevant cookie
- **AND** cookie values SHALL NOT be logged or persisted to artifacts without explicit user approval

#### Scenario: Session-state metadata

- **WHEN** chrome-cdp completes an operation
- **THEN** the output SHALL include session-state context: whether the target is authenticated, account identifier (if visible), and confirmation that no unexpected reset, logout, redirect, or write-action risk occurred

#### Scenario: Download operation output

- **WHEN** chrome-cdp supports authenticated file downloads (e.g., fanbox.cc files)
- **THEN** the output SHALL include: download URL, filename, file size (when available), download status (success/failure), and saved file path

### Requirement: Error contract — failure classification

The system SHALL define error categories for chrome-cdp failures, with emphasis on session and authentication state errors.

#### Scenario: Error categories

- **WHEN** chrome-cdp encounters a failure
- **THEN** the error SHALL be classified into one of: connection, auth_redirect, session_loss, rate_limit, extraction, permissions

| Error Category | Description |
|---------------|-------------|
| connection | CDP daemon not reachable, Chrome debugging port closed, browser crashed |
| auth_redirect | Navigation or extraction triggered redirect to login/email verification, losing authenticated context |
| session_loss | CDP disconnected during operation, daemon timeout, page close |
| rate_limit | API rate limiting triggered (e.g., fanbox.cc API 403/network error after burst) |
| extraction | DOM selector not found, content missing despite valid session |
| permissions | "Allow debugging" prompt declined, page requires login but no session available |

#### Scenario: Recommended next action per auth_redirect

- **WHEN** an auth_redirect error occurs (page redirected to login/email verification)
- **THEN** the operation SHALL stop immediately
- **AND** the recommended next action SHALL be: inform user the authenticated session was lost or requires re-verification; do not retry

#### Scenario: Recommended next action per rate_limit

- **WHEN** a rate_limit error occurs (API returns 403 or network error after burst)
- **THEN** the recommended next action SHALL be: stop all API calls immediately; wait at minimum 3 hours before retry; implement minimum 3-second delay between calls for safe sustained rate
- **AND** rate limit metadata SHALL be recorded: burst threshold (~80-100 calls in 10 min), recovery time (~2.5-3 hours), safe sustained rate (~8-10 calls/min)

#### Scenario: Recommended next action per connection error

- **WHEN** a connection error occurs (CDP daemon not reachable)
- **THEN** the recommended next action SHALL be: verify Chrome is running with remote debugging enabled; inform user to click "Allow debugging"; retry connection

### Requirement: Smoke-check scenario — authenticated content retrieval

The system SHALL validate the chrome-cdp contract against known authenticated targets.

#### Scenario: fanbox.cc authenticated content view

- **WHEN** chrome-cdp is tested against a fanbox.cc creator post list at `https://www.fanbox.cc/@<creatorId>/posts` with an approved authenticated Chrome tab
- **THEN** the page title SHALL contain the creator name and "pixivFANBOX"
- **AND** post cards with dates, titles, and access levels SHALL be visible in the accessibility snapshot
- **AND** the output SHALL include `engine: chrome-cdp` and the authenticated session status
- **AND** if `isMailAddressOutdated` is set, the test SHALL detect and report the email verification redirect (`/email/reactivate`)

#### Scenario: x.com authenticated session continuity

- **WHEN** chrome-cdp is tested against an x.com search page (e.g., `https://x.com/search?q=%23sf6_ingrid&src=typed_query&f=live`) with an approved authenticated Chrome tab
- **THEN** the page title SHALL confirm the search context (e.g., "#sf6_ingrid - Search / X")
- **AND** search results SHALL be visible (not the login page)
- **AND** the account marker (e.g., `@username`) SHALL be visible confirming authenticated state
- **AND** the output SHALL record that no redirect to `/i/flow/login` occurred during the session
