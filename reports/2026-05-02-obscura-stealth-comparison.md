# Obscura Stealth Comparison Report

**Date:** 2026-05-02
**Change:** obscura-edge-verification
**Tester:** agent

## 1. Objective

Compare Obscura (`obscura fetch`) vs Scrapling (`stealthy-fetch`) on sites with anti-crawling measures, evaluating success rate, content completeness, and execution stability.

## 2. Test Methodology

For each target site, three fetches were executed:

| Mode | Command |
|------|---------|
| Obscura (plain) | `obscura fetch <URL> --dump html` |
| Obscura (stealth) | `obscura fetch <URL> --dump html --stealth` |
| Scrapling (stealthy) | `scrapling extract stealthy-fetch <URL> <out.html>` |

Metrics recorded: exit code, output size, presence of expected content, execution time, error/warning logs.

## 3. Results

### 3.1 wiki.supercombo.gg (Cloudflare Challenge Page)

| Mode | Size | Time | Exit | Content |
|------|------|------|------|---------|
| Obscura plain | 6,044 B | 1.0 s | 0 | "Just a moment..." CF challenge page |
| Obscura stealth | 6,044 B | 1.1 s | 0 | "Just a moment..." CF challenge page |
| Scrapling stealthy | 31,649 B | 6.5 s | 0 | "Just a moment..." CF challenge page (HTTP 403 on 2nd GET) |

**Verdict:** ❌ No bypass. All three modes received the Cloudflare challenge page.

### 3.2 nowsecure.nl (Cloudflare Turnstile + Heavy JS)

| Mode | Size | Time | Exit | Content |
|------|------|------|------|---------|
| Obscura plain | 539 B | 60+ s | 0* | TIMEOUT — JS error: `Cannot read properties of null (reading 'replace')` |
| Obscura stealth | 539 B | 60+ s | 0* | TIMEOUT — Same JS error |
| Scrapling stealthy | 178,908 B | 4.6 s | 0 | Full page content successfully retrieved |

*Obscura process hung; output captured before manual termination.

**Verdict:** ❌ Obscura FAIL (hang/timeout due to unhandled JS exception). ✅ Scrapling PASS.

### 3.3 video.dmm.co.jp (JS Dynamic / Adult Content Age Gate)

| Mode | Size | Time | Exit | Content |
|------|------|------|------|---------|
| Obscura plain | 15,145 B | 2.1 s | 0 | Age gate page (`年齢認証 - FANZA`) with JS console errors |
| Obscura stealth | 15,145 B | 2.1 s | 0 | Age gate page with JS console errors |
| Scrapling stealthy | 47,512 B | 6.0 s | 0 | Age gate page (`年齢認証 - FANZA`) |

**Verdict:** ⚠️ Both engines reached the age gate (expected for this domain). Obscura faster but emitted JS errors (`Cannot read properties of undefined (reading 'length')`).

### 3.4 scrapingbee.com/blog (Dynamic SPA Blog)

| Mode | Size | Time | Exit | Content |
|------|------|------|------|---------|
| Obscura plain | 117,620 B | 3.5 s | 0 | Empty `<body>` (only inline CSS/preload tags, no articles) |
| Obscura stealth | 117,620 B | 3.5 s | 0 | Empty `<body>` (same as plain) |
| Scrapling stealthy | 215,068 B | 4.2 s | 0 | Full blog content with 29+ content markers (articles, posts, etc.) |

**Verdict:** ❌ Obscura FAIL — did not render dynamic content. The 118KB consists almost entirely of inline CSS; `<body>` contains only empty `<form>` elements. ✅ Scrapling PASS — full SPA render.

## 4. Summary Matrix

| Site | Obscura Plain | Obscura Stealth | Scrapling Stealthy |
|------|---------------|-----------------|-------------------|
| wiki.supercombo.gg (CF) | ❌ Challenge page | ❌ Challenge page | ❌ Challenge page |
| nowsecure.nl (Turnstile) | ❌ Timeout/JS error | ❌ Timeout/JS error | ✅ Full content |
| video.dmm.co.jp (JS/Age) | ⚠️ Age gate + JS errors | ⚠️ Age gate + JS errors | ⚠️ Age gate |
| scrapingbee.com/blog (SPA) | ❌ Empty body | ❌ Empty body | ✅ Full content |

## 5. Key Observations

1. **Obscura `--stealth` had zero observable effect** in all four tests. Output sizes and behavior were identical between plain and stealth modes.
2. **Obscura's V8 JS engine fails on complex modern JS** — GSAP/transform libraries on nowsecure.nl cause unhandled exceptions that hang the page load; DMM's JS also triggers errors.
3. **Obscura does not execute dynamic SPA content** — scrapingbee.com/blog returned empty body, indicating the JS-driven content hydration never completed.
4. **Scrapling (Playwright-based) handles all tested sites without crashes** — even when blocked by Cloudflare, it degrades gracefully and returns the challenge page content.
5. **Neither engine bypassed Cloudflare challenge pages** — this is expected behavior for both tools against strong CF protections.

## 6. Conclusion Grading

| Dimension | Grade | Notes |
|-----------|-------|-------|
| Anti-CF Challenge Bypass | N/A | Neither engine expected to bypass strong CF |
| JS Execution Stability | ❌ FAIL | Obscura hangs/crashes on heavy JS sites |
| Dynamic Content Render | ❌ FAIL | Obscura fails to hydrate SPA content |
| Stealth Mode Effectiveness | ❌ FAIL | `--stealth` produces identical results to plain |
| Overall Reliability | ⚠️ CONDITIONAL | Works for simple static pages; fails on dynamic/heavy-JS sites |

**Overall Status:** ⚠️ CONDITIONAL PASS with significant limitations

Obscura (`obscura-fetch`) is **not ready for `frozen` status** based on stealth validation. The engine works for lightweight static pages and parallel fetching, but exhibits critical failures on:
- Heavy JS animation libraries (hang/timeout)
- SPA content hydration (empty body)
- Stealth mode appears non-functional in current build

Recommendation: Update `obscura-fetch-contract` spec to explicitly document these boundaries (JS complexity limits, SPA hydration limitations, stealth mode pending verification) and **retain `draft` status**.
