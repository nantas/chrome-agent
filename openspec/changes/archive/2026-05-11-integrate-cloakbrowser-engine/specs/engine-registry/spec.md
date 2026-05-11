# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-registry`
- 来源: `integrate-cloakbrowser-engine` proposal + user confirmation
- 变更类型: modified
- 用户确认摘要: 新增 cloakbrowser-fetch 引擎条目（`playwright_stealth` 类型，rank 4），标记 scrapling-stealthy-fetch 为 superseded

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: cloakbrowser-fetch engine entry

The system SHALL register the cloakbrowser-fetch engine in `configs/engine-registry.json` with the following characteristics:

```json
{
  "id": "cloakbrowser-fetch",
  "type": "playwright_stealth",
  "characteristics": {
    "efficiency": {
      "score": 0.25,
      "note": "Playwright-based patched Chromium. ~443MB RSS (Chromium + node), 4-8s cold start. Higher overhead than scrapling-fetch due to additional patched binary."
    },
    "stability": {
      "score": 0.55,
      "note": "v0.3.27 upstream with active maintenance. 57 C++ patches rebased per Chromium version. macOS Chromium 145 vs Linux/Windows 146 version gap introduces platform variance. Supersedes scrapling-stealthy-fetch."
    },
    "adaptability": {
      "score": 0.80,
      "note": "Full Chromium capabilities. Handles Cloudflare Turnstile (6-8s auto-resolve), reCAPTCHA v3 (score 0.9), TLS fingerprint detection, SPA, heavy JS. Not suitable for CF non-Turnstile JS challenges without headed mode."
    }
  },
  "composite_score": 62,
  "default_rank": 4,
  "best_for": ["high_protection", "turnstile_protected", "recaptcha_protected", "tls_fingerprint_detected", "dynamic_content", "dynamic_list", "spa"],
  "contract_spec": "cloakbrowser-fetch-contract",
  "status": "draft"
}
```

The `composite_score` SHALL be derived using the formula: `round((adaptability × 0.50 + stability × 0.30 + efficiency × 0.20) × 100)`.

#### Scenario: cloakbrowser-fetch registry entry validation

- **WHEN** the `cloakbrowser-fetch` registry entry is validated
- **THEN** all three characteristic dimensions SHALL have non-null scores and notes
- **AND** `id` SHALL match the contract spec directory stem `cloakbrowser-fetch-contract`
- **AND** `type` SHALL be `playwright_stealth`
- **AND** `status` SHALL be `draft`
- **AND** `composite_score` SHALL equal `round((0.80 × 0.50 + 0.55 × 0.30 + 0.25 × 0.20) × 100)` = `62`
- **AND** `default_rank` SHALL be 4

### Requirement: scrapling-stealthy-fetch engine status update

The system SHALL update the `scrapling-stealthy-fetch` engine entry to reflect its superseded status.

```json
{
  "id": "scrapling-stealthy-fetch",
  "status": "superseded"
}
```

#### Scenario: scrapling-stealthy-fetch supersession

- **WHEN** the engine registry is queried for high-protection engines
- **THEN** `scrapling-stealthy-fetch` SHALL have `status: "superseded"`
- **AND** `cloakbrowser-fetch` SHALL be the recommended replacement
- **AND** existing strategies that reference `scrapling-stealthy-fetch` SHALL NOT break — the entry remains in the registry for historical reference

### Requirement: Engine type extension note

The `playwright_stealth` engine type SHALL be explicitly recognized in the engine type registry. CloakBrowser is the first engine using this type; it represents a Playwright-based engine with source-level stealth patches compiled into the Chromium binary.

#### Scenario: playwright_stealth type versus playwright

- **WHEN** an engine has type `playwright_stealth`
- **THEN** it SHALL share the same base capabilities as `playwright` (full browser, CDP support, Playwright API)
- **AND** it SHALL additionally provide source-level fingerprint stealth that `playwright` does not
- **AND** it SHALL have higher resource requirements than standard `playwright` (larger binary, additional memory)
