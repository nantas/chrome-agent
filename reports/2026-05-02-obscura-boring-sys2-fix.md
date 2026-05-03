# Obscura boring-sys2 Build Fix & Stealth Root Cause Analysis

**Date:** 2026-05-02
**Change:** obscura-edge-verification (follow-up exploration)

## Goal

Fix the `--features stealth` build failure on macOS arm64 (`boring-sys2` linker error), then re-verify the "SPA hydration failure" finding from `reports/2026-05-02-obscura-stealth-comparison.md`.

## boring-sys2 Build Failure — Root Cause & Fix

### Root Cause Chain

```
wreq v6.0.0-rc.28 → boring2 v5.0.0-alpha.13 → boring-sys2 v5.0.0-alpha.13
  ↓
prefix-symbols feature → objcopy required for symbol renaming
  ↓
macOS arm64: objcopy NOT available → build script skips prefix_symbols()
  ↓
BUT: PrefixCallback (bindgen link_name override) still registered
  ↓
Rust code expects boring_sys2_d2i_X509 but .a library has d2i_X509
  ↓
Linker error: symbol "build_script_main_*" not found
```

### Two-Step Fix

| Step | Action | Purpose |
|------|--------|---------|
| 1 | `brew install binutils` | Provides `objcopy` (at `/opt/homebrew/opt/binutils/bin/gobjcopy`) |
| 2 | Remove `features = ["prefix-symbols"]` from wreq in `crates/obscura-net/Cargo.toml` | Avoids BoringSSL ARM assembly × Apple linker incompatibility (`__compact_unwind` section alignment errors on `.S.o` files) |

### After Fix

```
cargo build --release --features stealth  →  55s, success ✅
StealthHttpClient:  found in binary ✅
wreq:               1034 references found ✅
```

## Stealth Verification (Post-Fix)

### Headers Difference (Proof stealth mode uses different HTTP stack)

| Dimension | Plain (reqwest) | Stealth (wreq) |
|-----------|----------------|----------------|
| Accept-Encoding | gzip, deflate, br | absent |
| Priority | absent | `u=0, i` |
| Upgrade-Insecure-Requests | `1` | absent |

### Site-by-Site Results

| Site | Plain | Stealth (wreq) | Scrapling Stealthy | Conclusion |
|------|-------|----------------|-------------------|------------|
| news.ycombinator.com | ✅ 1.3s | ✅ 1.3s | ✅ 4.8s | Stealth works, no regression |
| scrapingbee.com/blog | ❌ empty body | ❌ empty body | ✅ 215KB | **Not SPA** - TLS-level detection, wreq impersonation still identified |
| wiki.supercombo.gg (CF) | ❌ challenge | ❌ challenge | ❌ challenge | Expected - full browser needed for CF |
| nowsecure.nl (Turnstile) | ❌ V8 timeout | ❌ V8 timeout | ✅ full content | V8 JS issue (GSAP), not stealth-related |

### Corrected Diagnosis: scrapingbee.com/blog

**Previous report conclusion** (incorrect): "Obscura fails to hydrate SPA content — empty body due to V8 JS execution gap."

**Corrected conclusion**: `scrapingbee.com/blog` **is SSR** (server-rendered). `curl` retrieves full 48KB content with 143 `<a>` tags. The server detects Obscura's HTTP client identity (even wreq's TLS impersonation) and returns an empty `<body>` skeleton. This is anti-bot detection at the **network layer**, not a JavaScript execution issue.

## Remaining Issues (unresolved)

1. **V8 JS exception → event loop deadlock** (nowsecure.nl): `execute_script_with_timeout` interrupts script execution, but the event poll loop (`run_event_loop`) has no error monitoring. An unhandled JS exception causes infinite microtask polling.
   - Fix location: `page.rs` / `runtime.rs` — add per-cycle error check in event loop

2. **wreq TLS impersonation insufficient for advanced anti-bot**: Chrome 145 TLS fingerprint emulation doesn't fool anti-scraping companies' multi-layer detection (TLS + HTTP headers + request timing + JS environment context).

## Build File Changes

| File | Change | Status |
|------|--------|--------|
| `crates/obscura-net/Cargo.toml` | Removed `features = ["prefix-symbols"]` from wreq dependency | 🔧 Modified (uncommitted) |
| `openspec/specs/obscura-fetch-contract/spec.md` | Added Known Limitations section (build constraints, TLS detection) | ✅ Previously written |
