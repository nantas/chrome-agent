# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-contracts`
- 来源: `integrate-cloakbrowser-engine` proposal + user confirmation
- 变更类型: modified
- 用户确认摘要: 新增 cloakbrowser-fetch 到 escalation chain（rank 4，替换 scrapling-stealthy-fetch），更新错误矩阵

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 注意：各引擎的行为规范真源是各自的 `<engine-id>-contract/spec.md`；本文件是聚合索引，不做行为定义的替代

## MODIFIED Requirements

### Requirement: Cross-engine error contract consistency

The system SHALL ensure consistent error categories and recommendations across all engine contracts, including the new cloakbrowser-fetch engine.

#### Scenario: Shared error categories (updated)

- **WHEN** error contracts are compared across engines
- **THEN** the following error categories SHALL be used consistently (each engine adds engine-specific categories as needed):

| Category | scrapling-get | obscura-fetch | scrapling-fetch | cloakbrowser-fetch | scrapling-bulk-fetch | chrome-devtools-mcp | chrome-cdp |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| network | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| timeout | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| block | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| parse | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| browser | — | ✓ | ✓ | ✓ | ✓ | — | — |
| challenge | — | — | — | ✓ | — | — | — |
| binary | — | — | — | ✓ | — | — | — |
| license | — | — | — | ✓ | — | — | — |
| connection | — | — | — | — | — | ✓ | ✓ |
| navigation | — | — | — | — | — | ✓ | — |
| selector | — | — | — | — | — | ✓ | — |
| evaluation | — | — | — | — | — | ✓ | — |
| auth_redirect | — | — | — | — | — | — | ✓ |
| session_loss | — | — | — | — | — | — | ✓ |
| rate_limit | — | — | — | — | — | — | ✓ |
| permissions | — | — | — | — | — | — | ✓ |

Note: `scrapling-stealthy-fetch` (superseded) retains its error categories for historical reference but is removed from the primary comparison table.

#### Scenario: Escalation chain (updated)

- **WHEN** an engine fails and escalation is recommended
- **THEN** the standard escalation chain SHALL follow: `scrapling-get → obscura-fetch → scrapling-fetch → cloakbrowser-fetch → chrome-devtools-mcp` for protection-level escalation
- **AND** `obscura-fetch` SHALL be tried after `scrapling-get` fails (e.g., JS rendering required) and before `scrapling-fetch` (e.g., full browser needed)
- **AND** `cloakbrowser-fetch` SHALL be tried after `scrapling-fetch` and before `chrome-devtools-mcp` for high-protection pages requiring stealth (TLS fingerprint evasion, Turnstile, reCAPTCHA)
- **AND** the bulk escalation chain SHALL follow: `scrapling-bulk-fetch → scrapling-bulk-stealthy-fetch` for batch operations
- **AND** the live-session path SHALL follow: `scrapling-fetch/cloakbrowser-fetch (session reuse fail) → chrome-cdp`

### Requirement: Smoke-check aggregate (updated)

The system SHALL provide a consolidated view of smoke-check scenarios across all engine contracts, including the new cloakbrowser-fetch engine.

#### Scenario: Smoke-check inventory (updated)

- **WHEN** the smoke-check inventory is consulted
- **THEN** it SHALL reference each engine's smoke-check scenario from its individual contract spec
- **AND** the inventory SHALL list each engine's smoke-check target and expected outcome:

| Engine | Smoke-check Target | Expected Outcome |
|--------|-------------------|-----------------|
| scrapling-get | mp.weixin.qq.com/s/... | 文章标题 + DOM 顺序正文 + 内联图片 URL 保留 |
| obscura-fetch | news.ycombinator.com | 页面标题 "Hacker News" + ≥20 story entries + HTTP 200 + timing ≤ 5000ms |
| scrapling-fetch | x.com/<user>/status/<id> | SPA 渲染推文内容 + 作者 + 媒体链接 |
| cloakbrowser-fetch | wiki.supercombo.gg/w/... | CF Turnstile 自动解析 + 文章内容（20,000+ chars），非挑战壳 |
| | scrapingbee.com/blog/ | TLS 指纹绕过 + 全量内容（140+ links），非空 body |
| scrapling-bulk-fetch | [example.com, httpbin.org/get] | 双 URL 成功，status 200 × 2，正确内容 |
| chrome-devtools-mcp | x.com/hashtag/... | 诊断证据：title/URL + snapshot + network（登录门检测） |
| chrome-cdp | fanbox.cc/@.../posts | 认证页面 visit + 帖子列表内容 + 无 auth redirect |
