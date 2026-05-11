# Specification Delta

## Capability 对齐（已确认）

- Capability: `scrapling-stealthy-fetch-contract`
- 来源: `integrate-cloakbrowser-engine` proposal + user confirmation
- 变更类型: removed (superseded)
- 用户确认摘要: scrapling-stealthy-fetch 被 cloakbrowser-fetch 替代，标记为 superseded。保留 spec 供历史引用

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- 本 capability 已被 superseded，不再作为活跃引擎的行为依据
- 活跃替代：`cloakbrowser-fetch-contract` (`openspec/specs/cloakbrowser-fetch-contract/spec.md`)

## REMOVED Requirements

### Requirement: 引擎活跃状态

**Reason**: `scrapling-stealthy-fetch` (Playwright + JS injection stealth) is superseded by `cloakbrowser-fetch` (patched Chromium binary with 57 C++ source-level patches). CloakBrowser provides fundamentally superior stealth: its patches are compiled into the browser binary rather than injected via JavaScript, making them undetectable by fingerprinting scripts. Verification confirmed CloakBrowser passes Cloudflare Turnstile (6-8s auto-resolve), reCAPTCHA v3 (score 0.9), TLS fingerprint detection, and major bot detection sites — capabilities that scrapling-stealthy-fetch could not reliably achieve.

**Migration**: Strategies and workflows that reference `scrapling-stealthy-fetch` SHALL migrate to `cloakbrowser-fetch`. The scrapling-stealthy-fetch registry entry is retained with `status: superseded` for historical reference. Automated migration is NOT required — existing references will not break but should be updated at next strategy review.

## RENAMED Requirements

- FROM: `### Requirement: Engine status`
- TO: `### Requirement: Engine status (superseded — see cloakbrowser-fetch)`

All other requirements (Input contract, Error contract, Smoke-check scenarios) in this spec are **preserved for historical reference** but are no longer active. Refer to `cloakbrowser-fetch-contract/spec.md` for the active replacement.
