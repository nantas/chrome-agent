# 2026-05-02 Obscura Verification Outcome

## Context

`add-obscura-engine` change (2026-05-02) completed core implementation with `obscura-fetch` registered as `draft`. Two critical verification gaps remained before `frozen` promotion:

1. **Parallel fetching**: `obscura scrape` depends on an independent `obscura-worker` binary not included in precompiled releases.
2. **Stealth depth**: Initial benchmark only tested `scrapingbee.com/blog` with medium-protection Cloudflare; strong anti-bot and heavy-JS sites were unverified.

This decision record documents the verification execution and the resulting status determination.

## Verification Execution

### Parallel Fetching

- Built `obscura-worker` from source (`cargo build --release` without `--features stealth` due to `boring-sys2` linker failure on macOS arm64).
- Tested `obscura scrape` against 3 mixed-scenario URLs with concurrency=3.
- **Result**: 3/3 successful, ~2.2× speedup over serial baseline, zero worker process leaks.
- **Status**: ✅ PASSED

### Stealth Comparison

Tested 4 sites across Obscura (plain + stealth) and Scrapling (`stealthy-fetch`):

| Site | Obscura Plain | Obscura Stealth | Scrapling Stealthy |
|------|---------------|-----------------|-------------------|
| wiki.supercombo.gg (CF challenge) | Challenge page | Challenge page | Challenge page |
| nowsecure.nl (Turnstile + heavy JS) | **Timeout / JS hang** | **Timeout / JS hang** | Full content |
| video.dmm.co.jp (JS dynamic) | Age gate + JS errors | Age gate + JS errors | Age gate |
| scrapingbee.com/blog (SPA) | **Empty body** | **Empty body** | Full content |

Key findings:
- `--stealth` produced **identical** output to plain mode (pre-built binary lacked stealth). Post-fix build with wreq shows header differences, but still fails against advanced anti-bot.
- Obscura's V8 engine **hangs/timeouts** on heavy JS animation libraries (GSAP on nowsecure.nl).
- `scrapingbee.com/blog` empty body is **not SPA hydration failure** but **TLS-level detection** — the page is SSR (curl gets full 48KB content with 143 `<a>` tags). The server detects reqwest/wreq TLS fingerprint and returns an empty skeleton.
- Neither engine bypassed Cloudflare challenge pages (expected).

**Status**: ⚠️ CONDITIONAL — significant limitations on JS complexity and anti-bot detection.

## Decision

**Maintain `obscura-fetch` status as `draft`.** Do NOT promote to `frozen` at this time.

Rationale:
- Parallel fetching passes, but stealth/JS-rendering verification reveals critical gaps.
- `obscura-fetch` is reliable for lightweight static and mildly-dynamic pages, but cannot be trusted for:
  - Heavy JS animations / complex frontend frameworks
  - SPA content hydration
  - Any scenario where `--stealth` is expected to provide measurable benefit
- Promoting to `frozen` would imply a stability contract that the current v0.1.0 build cannot fulfill.

Actions taken:
1. Reports archived to `reports/2026-05-02-obscura-parallel-test.md` and `reports/2026-05-02-obscura-stealth-comparison.md`.
2. `obscura-fetch-contract` spec updated with Known Limitations section documenting JS complexity bounds, SPA hydration risk, and stealth build constraints.
3. `configs/engine-registry.json` remains unchanged (`status: draft`).

## Consequences

### Positive
- Verification artifacts establish quantitative evidence for `obscura-fetch` capability boundaries.
- Parallel fetching is validated and safe to use for batch scenarios where content correctness is independently verified.
- Clear escalation criteria: when Obscura fails on JS complexity, escalate to `scrapling-fetch` or `scrapling-stealthy-fetch`.

### Risk / Follow-up
### Follow-up exploration (2026-05-02, after archive) confirmed:

1. **`boring-sys2` build**: ✅ FIXED with two steps:
   - `brew install binutils` (provides `objcopy`)
   - Remove `features = ["prefix-symbols"]` from wreq in `crates/obscura-net/Cargo.toml`
   - Now `cargo build --release --features stealth` succeeds (55s)
   - See `reports/2026-05-02-obscura-boring-sys2-fix.md`

2. **`scrapingbee.com/blog` empty body**: ❌ Corrected diagnosis — it's **TLS detection** at the network layer, not a V8 execution gap. Even wreq's Chrome 145 TLS impersonation is detected by anti-scraping services. The page is SSR.

3. **`nowsecure.nl` V8 timeout**: ❌ Still unresolved — `execute_script_with_timeout` interrupts script execution but `run_event_loop` has no error monitoring. Unhandled JS exceptions cause infinite microtask polling. Fix would require modifying Obscura's `page.rs` / `runtime.rs`.
