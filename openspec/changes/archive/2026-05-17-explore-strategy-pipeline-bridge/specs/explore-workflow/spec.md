# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md`
- 变更类型: `modified`
- 用户确认摘要: `runExplore()` 策略命中路径扩展；`main.py` engine 选择引用 API 探测结果；SKILL.md 新增转换路径

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: explore-strategy-matched-conversion-engine-info

When `runExplore()` in `chrome-agent-cli.mjs` matches an existing strategy, the result SHALL include `conversion_engine` and `converter_path` fields to guide the agent toward the correct sample conversion path.

#### Scenario: strategy-matched-output-extended
- **WHEN** `runExplore()` finds a matching strategy
- **AND** the strategy has `api.platform: "mediawiki"`
- **THEN** the result SHALL include `conversion_engine: "mediawiki-api"`
- **THEN** the result SHALL include `converter_path: "scripts/explore/sample_converter.py fetch-and-apply"`

#### Scenario: non-api-strategy-no-change
- **WHEN** `runExplore()` finds a matching strategy without an API platform
- **THEN** the result SHALL include `conversion_engine: "<recommendedFetcher>"`
- **THEN** `converter_path` SHALL be absent or indicate scrapling-based conversion

### Requirement: main-py-api-config-engine-selection

The engine selection in `scripts/explore/main.py` SHALL prioritize the API discovery result (`api_config`) over the probe chain's first successful engine.

#### Scenario: api-discovered-prioritized
- **WHEN** `main.py` Phase 6 selects the sample conversion engine
- **AND** `api_config` is not None and `api_config.get("type") == "mediawiki"`
- **THEN** the engine SHALL be `"mediawiki-api"`
- **THEN** the probe chain engine SHALL NOT be used

#### Scenario: no-api-preserves-existing-logic
- **WHEN** `api_config` is None or not a known API type
- **THEN** the existing logic: `protection.get("engine_override") or probe_result.get("success_engine") or "scrapling-get"` SHALL apply
