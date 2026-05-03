# Obscura Parallel Fetch Verification Report

**Date:** 2026-05-02
**Change:** obscura-edge-verification
**Tester:** agent

## 1. Objective

Verify `obscura scrape` parallel execution correctness, performance, and resource isolation after building `obscura-worker` binary.

## 2. Worker Build

| Item | Value |
|------|-------|
| Source | `/Volumes/Shuttle/projects/agentic/obscura` |
| Build command | `cargo build --release` |
| Feature `stealth` | **Skipped** — `boring-sys2` linker error with `--features stealth` on macOS arm64 |
| Worker binary | `target/release/obscura-worker` (57.7MB) |
| Install path | `$HOME/.cache/chrome-agent-obscura/bin/obscura-worker` |
| Main binary | `$HOME/.cache/chrome-agent-obscura/bin/obscura` (pre-installed, 59.7MB) |

### Build Notes
- First attempt with `--features stealth` failed at link stage due to missing `build_script_main_*` symbols from `boring-sys2` (BoringSSL bindings).
- Build **without** `--features stealth` succeeded in ~15 seconds.
- Worker binary does not depend on stealth features; it communicates with main binary via IPC.

## 3. Parallel Test Results

### 3.1 Test Configuration

```bash
obscura scrape \
  "https://httpbin.org/html" \
  "https://quotes.toscrape.com" \
  "https://news.ycombinator.com" \
  --concurrency 3 \
  --eval "document.querySelector('h1')?.innerText || document.title" \
  --format json
```

### 3.2 Results

```json
{
  "total_urls": 3,
  "concurrency": 3,
  "total_time_ms": 1994,
  "avg_time_ms": 664.7,
  "results": [
    {
      "url": "https://httpbin.org/html",
      "title": "",
      "eval": "Herman Melville - Moby-Dick",
      "time_ms": 1159,
      "worker": 0
    },
    {
      "url": "https://quotes.toscrape.com",
      "title": "Quotes to Scrape",
      "eval": "Quotes to Scrape",
      "time_ms": 1993,
      "worker": 1
    },
    {
      "url": "https://news.ycombinator.com",
      "title": "Hacker News",
      "eval": "Hacker News",
      "time_ms": 1396,
      "worker": 2
    }
  ]
}
```

### 3.3 Verification Checklist

| Criterion | Result | Evidence |
|-----------|--------|----------|
| All URLs return successfully | ✅ PASS | 3/3 results, no `error` field |
| Content correctness | ✅ PASS | httpbin: "Herman Melville - Moby-Dick"; quotes: "Quotes to Scrape"; HN: "Hacker News" |
| Parallel efficiency | ✅ PASS | Total 1,994 ms << serial sum ~4,390 ms |
| No worker leaks | ✅ PASS | `ps aux` shows zero `obscura-worker` processes after completion |

### 3.4 Serial Baseline (for comparison)

| URL | Serial Time |
|-----|-------------|
| httpbin.org/html | 1,143 ms |
| quotes.toscrape.com | 1,924 ms |
| news.ycombinator.com | 1,334 ms |
| **Serial total** | **~4,401 ms** |
| **Parallel total** | **1,994 ms** |
| **Speedup** | **~2.2×** |

## 4. Conclusion

`obscura scrape` parallel execution **passes** all verification criteria. Worker binary is functional, process isolation is clean, and parallel speedup is significant (~2.2× for 3 URLs on 3 workers).

**Status:** ✅ PASSED
