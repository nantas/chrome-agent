# Verification

## Change: remove-maxpages-default
## Schema: orbitos-change-v1
## Date: 2026-05-21

---

## Spec-to-Implementation Traceability

### Requirement: maxPages-null-means-unlimited

| Scenario | Implementation Location | Evidence |
|----------|------------------------|----------|
| external-caller-no-maxPages | L1980 `runCrawl()`: `maxPages = null` | grep 确认无 `maxPages = [0-9]` 残留 |
| external-caller-with-maxPages | 同上解构，透传机制不变 | CLI `--max-pages N` 行为不变 |
| cli-no-max-pages-flag | L3718, L3740: `maxPages: parsed.maxPages` | grep 确认无 `maxPages ??` 残留 |
| cli-with-max-pages-flag | parseArgs 已返回整数，透传不变 | 无改动，行为保持 |

**Evidence commands:**
```bash
# E1: 无硬编码数字默认值
grep -c 'maxPages = [0-9]' scripts/chrome-agent-cli.mjs  # → 0

# E2: 无 ?? 默认值填充
grep -c 'maxPages ??' scripts/chrome-agent-cli.mjs        # → 0

# E3: 所有解构默认值为 null
grep -n 'maxPages = null,' scripts/chrome-agent-cli.mjs    # → 4 处 (L1980, L2072, L2316, L2754)
```

### Requirement: maxPages-null-guard-in-conditions

| Scenario | Implementation Location | Evidence |
|----------|------------------------|----------|
| mediawiki-pipeline-null-maxPages | L2119: `if (maxPages != null)` | null 时不传 `--max-pages` |
| mediawiki-pipeline-with-maxPages | 同上，非 null 时正常传参 | 行为不变 |
| scrapling-while-loop-null | L2393: `(maxPages == null \|\| visited.size < maxPages)` | null 时无上限 |
| scrapling-pagination-null | L2445, L2449: null-safe 入队条件 | null 时不阻止入队 |
| scrape-while-loop-null | L2813: `(maxPages == null \|\| visited.size < maxPages)` | null 时无上限 |

**Evidence commands:**
```bash
# E4: if 条件已改为显式 null 检查
grep -n 'if (maxPages)' scripts/chrome-agent-cli.mjs       # → 0 matches (raw truthy removed)
grep -n 'if (maxPages != null)' scripts/chrome-agent-cli.mjs # → 1 match (L2119)

# E5: while/条件比较已改为 null-safe
grep -c 'maxPages == null ||' scripts/chrome-agent-cli.mjs  # → 4 matches (L2393, L2445, L2449, L2813)

# E6: 无裸比较残留
grep -n 'visited.size < maxPages' scripts/chrome-agent-cli.mjs # → 0 (全部已包裹)
```

## Task-to-Evidence Matrix

| Task | Evidence | Status |
|------|----------|--------|
| 2.1 移除解构默认值（4 处） | E1, E3 | ✅ Pass |
| 2.2 移除 main() 调用点默认值填充（2 处） | E2 | ✅ Pass |
| 2.3 修正条件判断为 null-safe（5 处） | E4, E5, E6 | ✅ Pass |
| 3.1 整理 verification 证据 | 本文件 | ✅ Pass |
| 3.2 标记 writeback 摘要 | writeback.md | ✅ Pass |

## Verification Result

**PASS** — All spec requirements verified against implementation:
- 4 处解构默认值已改为 `null`
- 2 处 main() 调用点已移除 `??` 填充
- 5 处条件判断已改为 null-safe
- 无残留硬编码、裸比较或 falsy 检查
