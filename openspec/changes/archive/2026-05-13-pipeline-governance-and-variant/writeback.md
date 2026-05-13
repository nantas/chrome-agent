# Writeback

## 回写目标

本 change 的实现直接修改了目标文件（非延迟回写），以下记录回写目标及其执行状态。

### 目标 1: AGENTS.md

- **目标文件**: `AGENTS.md`
- **变更内容**: Section 7 之后新增 `### Pipeline Strategy Schema 治理` 子章节
- **包含内容**: 权威来源声明、策略文件约束、扩展协议、注册 ID 清单、Registry 变更约束、platform_variant 声明
- **前置条件**: `_STRATEGY_REGISTRY` 结构已确认
- **执行状态**: ✅ 已直接写入

### 目标 2: orchestrate.py

- **目标文件**: `scripts/mediawiki-api-extract/pipeline/orchestrate.py`
- **变更内容**:
  - `build_pipeline()`: warning → ValueError hard-fail
  - 模块级 `STRATEGY_REGISTRY = _STRATEGY_REGISTRY` 公共导出
  - `run_pipeline()`: try/except ValueError → EXIT_STRATEGY_ERROR
  - `run_pipeline()`: platform_variant 解析 + 传递给 phase_a/b
- **前置条件**: 无
- **执行状态**: ✅ 已直接写入

### 目标 3: strategy_scaffold_generator.py

- **目标文件**: `scripts/explore/strategy_scaffold_generator.py`
- **变更内容**: `generate()` 函数中增加 importlib 导入 STRATEGY_REGISTRY + content_profile ID 校验
- **前置条件**: orchestrate.py 已导出 STRATEGY_REGISTRY
- **执行状态**: ✅ 已直接写入

### 目标 4: 策略模板

- **目标文件**: `sites/templates/mediawiki-fandom.yaml`, `sites/templates/mediawiki-wiki-gg.yaml`
- **变更内容**: 新增 `api.platform_variant` 字段
- **前置条件**: platform_variant 受控词汇表已定义
- **执行状态**: ✅ 已直接写入

### 目标 5: agents-governance spec

- **目标文件**: `openspec/specs/agents-governance/spec.md`
- **变更内容**: 新增 Pipeline Strategy Schema 治理章节 Requirement
- **前置条件**: AGENTS.md 章节已写入
- **执行状态**: ✅ 已直接写入

### 目标 6: site-strategy-schema spec

- **目标文件**: `openspec/specs/site-strategy-schema/spec.md`
- **变更内容**: 新增 platform_variant 字段定义 + content_profile ID 引用完整性约束
- **前置条件**: platform_variant 和 registry 结构已确认
- **执行状态**: ✅ 已直接写入

## 审计证据

| 执行人 | 时间 | 目标 | 结果 |
|--------|------|------|------|
| pi-agent | 2026-05-13 | AGENTS.md Pipeline Strategy Schema 治理章节 | ✅ 已写入 |
| pi-agent | 2026-05-13 | orchestrate.py hard-fail + STRATEGY_REGISTRY + platform_variant | ✅ 已写入 |
| pi-agent | 2026-05-13 | strategy_scaffold_generator.py content_profile 校验 | ✅ 已写入 |
| pi-agent | 2026-05-13 | mediawiki-fandom.yaml / mediawiki-wiki-gg.yaml platform_variant | ✅ 已写入 |
| pi-agent | 2026-05-13 | agents-governance/spec.md 新增 Requirement | ✅ 已写入 |
| pi-agent | 2026-05-13 | site-strategy-schema/spec.md 新增字段和约束 | ✅ 已写入 |
