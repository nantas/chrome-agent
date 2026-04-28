# Writeback

## Change Summary

- **Change**: phase-2-contract-freeze
- **Schema**: orbitos-change-v1
- **Status**: Complete
- **Date**: 2026-04-28

## Deliverables

### Created
- `openspec/specs/scrapling-get-contract/spec.md` — Scrapling get 引擎契约 v1.0.0
- `openspec/specs/scrapling-fetch-contract/spec.md` — Scrapling fetch 引擎契约 v1.0.0
- `openspec/specs/scrapling-stealthy-fetch-contract/spec.md` — Scrapling stealthy-fetch 引擎契约 v1.0.0
- `openspec/specs/chrome-devtools-mcp-contract/spec.md` — Chrome DevTools MCP 诊断引擎契约 v1.0.0
- `openspec/specs/chrome-cdp-contract/spec.md` — Chrome CDP 实时会话引擎契约 v1.0.0
- `openspec/specs/engine-contracts/spec.md` — 引擎契约聚合索引 v1.0.0
- `sites/x.com-public-tweet.md` — x.com 公开推文 SPA 渲染站点经验文档

### Updated
- `docs/governance-and-capability-plan.md` — Phase 2 描述修正（specs 列表、交付物、排他边界）

## Smoke Check Results

| Engine | Target | Result |
|--------|--------|--------|
| scrapling-get | mp.weixin.qq.com 公开文章 | ✅ 成功 — 标题提取、DOM 顺序正文、封面图 URL 保留 |
| scrapling-fetch | x.com 公开推文 | ✅ 成功 — SPA 渲染推文内容（作者、文本、媒体），底部登录门但内容已加载 |
| scrapling-stealthy-fetch | wiki.supercombo.gg | ✅ 成功 — CF Turnstile 突破，文章内容返回 |
| chrome-devtools-mcp | x.com/hashtag/... | ✅ 已有证据 — sites/x.com-public-hashtag-search-login-gate.md |
| chrome-cdp | fanbox.cc @.../posts | ✅ 已有证据 — sites/fanbox.cc-content-download.md |

## Verification Status

- 5 engine contracts: ✅ All pass compliance (input/output/error + smoke-check + SHALL/MUST + Scenario blocks)
- engine-contracts aggregation: ✅ Correctly references all 5 engines + error matrix + smoke-check inventory
- Governance plan Phase 2: ✅ Updated spec list, deliverables, exclusivity boundary
- Smoke check evidence: ✅ All recorded (new smoke checks + existing site docs)

## Key Decisions Confirmed

- Error handling merged into each engine contract (no standalone `error-handling` spec)
- chrome-devtools-mcp treated as diagnostic engine (not content extraction)
- Smoke checks validated against real targets
- Contracts use `version: 1.0.0` with change history
