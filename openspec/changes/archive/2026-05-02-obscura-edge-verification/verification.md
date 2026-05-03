# Verification Report

**Change:** obscura-edge-verification
**Date:** 2026-05-02
**Schema:** orbitos-change-v1

## 1. Verification Scope

This change verifies two gaps left by `add-obscura-engine`:

1. **Parallel fetching capability** of `obscura scrape` via `obscura-worker` binary.
2. **Stealth mode depth** against anti-bot and heavy-JS sites.

## 2. Parallel Fetching Verification

| Criterion | Result |
|-----------|--------|
| Worker binary build | ✅ SUCCESS (without `--features stealth`) |
| 3-URL parallel execution | ✅ 3/3 success |
| Content correctness | ✅ All titles/eval results correct |
| Parallel speedup | ✅ ~2.2× vs serial baseline |
| Process leak check | ✅ Zero lingering workers |

**Evidence:** `reports/2026-05-02-obscura-parallel-test.md`

## 3. Stealth Comparison Verification

| Site | Obscura Plain | Obscura Stealth | Scrapling Stealthy |
|------|---------------|-----------------|-------------------|
| wiki.supercombo.gg (CF) | Challenge page | Challenge page | Challenge page |
| nowsecure.nl (Turnstile) | **Timeout / JS hang** | **Timeout / JS hang** | Full content |
| video.dmm.co.jp (JS) | Age gate + JS errors | Age gate + JS errors | Age gate |
| scrapingbee.com/blog (SPA) | **Empty body** | **Empty body** | Full content |

**Key Findings:**
- `--stealth` produced identical output to plain mode on all tested sites.
- Obscura V8 hangs on heavy JS animations (GSAP).
- Obscura fails to hydrate SPA content (empty body on scrapingbee.com/blog).
- Neither engine bypassed Cloudflare challenge pages.

**Evidence:** `reports/2026-05-02-obscura-stealth-comparison.md`

## 4. Conclusion

| Dimension | Verdict |
|-----------|---------|
| Parallel fetching | ✅ PASSED |
| Stealth / anti-bot depth | ⚠️ CONDITIONAL PASS with significant limitations |
| Overall engine readiness for `frozen` | ❌ NOT READY |

**Decision:** Maintain `obscura-fetch` status as `draft`. Update spec with Known Limitations. Do not modify `engine-registry.json` status.
