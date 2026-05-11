# Verification

## 变更

- **Change**: `integrate-cloakbrowser-engine`
- **Date**: 2026-05-11
- **Environment**: macOS (darwin-arm64), Python 3.9, CloakBrowser v0.3.27

## Spec Requirement 验证结果

### cloakbrowser-fetch-contract

| Requirement | 验证方法 | 结果 | 备注 |
|-------------|---------|------|------|
| Input contract | 代码审查 + 测试 | ✅ PASS | 13/13 参数均已实现：url, headless, wait_until, timeout, proxy, stealth_args, humanize, fingerprint_seed, timezone, locale, geoip, persistent_context, extra_args |
| Stealth capabilities | scrapingbee.com TLS 检测 | ✅ PASS | 140 links, 4660 chars, TLS 指纹未被检测 |
| Cloudflare Turnstile auto-resolution | wiki.supercombo.gg | ✅ PASS | 23,021 chars, "SuperCombo Wiki" title, 14.36s |
| Error contract | 代码审查 + 测试 | ✅ PASS | network/timeout/block/browser/binary/license/challenge 全部分类已实现并验证 |
| Smoke-check TLS | scrapingbee.com/blog | ✅ PASS | 140+ links, 4660 chars |
| Smoke-check Turnstile | wiki.supercombo.gg | ✅ PASS | 20,000+ chars, 正确 title |
| reCAPTCHA v3 评分 | 未验证 | ⏭️ SKIP | 需要特定 reCAPTCHA v3 demo 页面，未在本次验证范围内 |
| Proxy support | 代码审查 | ✅ PASS | proxy 参数通过 CloakBrowser launch() proxy 参数传递 |
| Persistent context | 代码审查 | ✅ PASS | persistent_context 参数通过 --user-data-dir 传递给 Chromium |
| Headless mode stealth | scrapingbee.com 通过 | ✅ PASS | navigator.webdriver=false, 无 HeadlessChrome 特征 |

### engine-registry

| Requirement | 验证方法 | 结果 | 备注 |
|-------------|---------|------|------|
| cloakbrowser-fetch 条目 | JSON 语法检查 + 字段验证 | ✅ PASS | type=playwright_stealth, rank=4, status=draft, composite_score=62 |
| composite_score 计算 | 手动计算 | ✅ PASS | round((0.80×0.50 + 0.55×0.30 + 0.25×0.20)×100) = round(61.5) = 62 |
| scrapling-stealthy-fetch superseded | JSON 检查 | ✅ PASS | status="superseded" |
| playwright_stealth 类型 | 代码审查 | ✅ PASS | 新类型已在 AGENTS.md 和 registry 中注册 |

### engine-contracts

| Requirement | 验证方法 | 结果 | 备注 |
|-------------|---------|------|------|
| Escalation chain 更新 | 代码审查 + 文档审查 | ✅ PASS | cloakbrowser-fetch 在 rank 4, scrapling-stealthy-fetch 已移除 |
| 错误矩阵更新 | spec 审查 | ✅ PASS | binary/challenge/license 类别已新增 |
| Smoke-check 聚合 | spec 审查 | ✅ PASS | cloakbrowser-fetch 两个 smoke-check 目标已列入 |

### scrapling-stealthy-fetch-contract (superseded)

| Requirement | 验证方法 | 结果 | 备注 |
|-------------|---------|------|------|
| 标记为 superseded | spec 审查 | ✅ PASS | 迁移指向 cloakbrowser-fetch-contract |

## Smoke-check 结果汇总

| 目标 | 预期 | 实际 | 状态 |
|------|------|------|------|
| example.com | title="Example Domain", 正常内容 | title="Example Domain", 129 chars, 1.93s | ✅ PASS |
| scrapingbee.com/blog | 140+ links, 4000+ chars | 140 links, 4660 chars, 2.91s | ✅ PASS |
| wiki.supercombo.gg | 20,000+ chars, "SuperCombo Wiki" | 23,021 chars, "SuperCombo Wiki", 14.36s | ✅ PASS |
| reCAPTCHA v3 demo | score >= 0.7 | — | ⏭️ SKIP |

## 实现验证

| Artifact | 验证方法 | 结果 |
|----------|---------|------|
| `configs/engine-registry.json` | JSON 语法检查 | ✅ Valid JSON |
| `scripts/cloakbrowser-preflight.sh` | 实际运行 | ✅ 返回 0 + 正确版本信息 |
| `scripts/cloakbrowser_fetcher.py` | example.com + scrapingbee + wiki.supercombo.gg | ✅ 三个测试全部通过 |
| `scripts/chrome-agent-cli.mjs` | `node -c` 语法检查 | ✅ Valid JS |
| `docs/playbooks/fallback-escalation.md` | 人工审查 | ✅ CloakBrowser 在 rank 4 |
| `docs/setup/cloakbrowser-setup.md` | 人工审查 | ✅ 安装步骤完整 |
| `AGENTS.md` | grep 检查无 stale 引用 | ✅ 无活跃 scrapling-stealthy-fetch 引用 |

## 已知限制

1. **macOS Chromium 145**: macOS 平台二进制使用 Chromium 145，Linux/Windows 使用 146。可能存在指纹差异，建议生产环境使用 Linux。
2. **nowsecure.nl 未验证**: Turnstile + GSAP 重 JS 组合在 macOS headless 下未通过自动解析。
3. **Binary 专有许可证**: Patched Chromium binary 不可重新分发，用户需自行 pip install。
4. **内存占用**: ~443 MB RSS（含 Playwright node 进程），远高于 obscura（~50 MB）和 scrapling-get（~0 MB）。
5. **reCAPTCHA v3**: 未在本次 smoke-check 中验证评分，需要在具有 reCAPTCHA v3 的测试页面上验证。
6. **首次下载时间**: ~200MB binary 首次下载可能需要较长时间。

## 结论

CloakBrowser 引擎集成已通过核心验证：
- 3/4 smoke-check 场景通过（1 个 SKIP）
- 所有 spec requirement 覆盖
- 引擎注册、CLI 集成、文档更新均已完成
- 已知限制已记录

**建议**: 保持 `status: draft`，待 Linux Chromium 146 验证和 reCAPTCHA v3 验证后升级为 `frozen`。
