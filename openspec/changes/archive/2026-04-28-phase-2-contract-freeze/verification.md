# Verification

## Change: phase-2-contract-freeze

### 5.1 Contract Compliance Verification

All 5 engine contract specs verified against `capability-contracts` metamodel and `engine-contracts` compliance criteria:

| Criteria | scrapling-get | scrapling-fetch | stealthy-fetch | chrome-devtools-mcp | chrome-cdp |
|----------|:---:|:---:|:---:|:---:|:---:|
| Input Contract dimension | ✅ | ✅ | ✅ | ✅ | ✅ |
| Output Contract dimension | ✅ | ✅ | ✅ | ✅ | ✅ |
| Error Contract dimension | ✅ | ✅ | ✅ | ✅ | ✅ |
| Smoke-check scenario | ✅ | ✅ | ✅ | ✅ | ✅ |
| SHALL/MUST language | ✅ (48) | ✅ (46) | ✅ (31) | ✅ (42) | ✅ (39) |
| Scenario blocks | ✅ (23) | ✅ (17) | ✅ (14) | ✅ (25) | ✅ (17) |

### 5.2 Engine-Contracts Aggregation Verification

| Check | Status |
|-------|:------:|
| References all 5 engine contracts | ✅ |
| Error matrix with per-engine coverage | ✅ |
| Smoke-check inventory with targets | ✅ |
| Escalation chain documented | ✅ |
| Compliance criteria defined | ✅ |

### 5.3 Governance Plan Verification

`docs/governance-and-capability-plan.md` Phase 2 section updated:

| Field | Status |
|-------|:------:|
| Required specs: 6 actual capabilities | ✅ |
| `error-handling` removed (merged into each contract) | ✅ |
| Deliverables updated (5 contracts + aggregation + verification) | ✅ |
| Exclusivity boundary clarified | ✅ |

### 5.4 Smoke Check Evidence Verification

| Smoke Check | Method | Evidence | Result |
|------------|--------|----------|:------:|
| Scrapling get — WeChat article | Scrapling get | This session: title "Karpathy：一切软件，都将为 Agent 重写", cover image, DOM order body | ✅ Success |
| Scrapling fetch — x.com tweet | Scrapling fetch | This session: SPA rendered tweet (author, text, video thumbnail), login gate at bottom | ✅ Success (known limitation: registration prompt) |
| Scrapling stealthy-fetch — wiki.supercombo.gg | Scrapling stealthy-fetch | This session: CF Turnstile solved, article content returned, NOT challenge shell | ✅ Success |
| chrome-devtools-mcp — x.com hashtag | Existing site doc | `sites/x.com-public-hashtag-search-login-gate.md` | ✅ Existing evidence |
| chrome-cdp — fanbox.cc | Existing site doc | `sites/fanbox.cc-content-download.md` (12,924 bytes) | ✅ Existing evidence |
| x.com tweet site doc | Newly created | `sites/x.com-public-tweet.md` | ✅ Created |

### Conclusion

All verification criteria are satisfied. The 5 engine contracts are frozen as the behavioral source of truth for Phase 3 (strategy library standardization).
