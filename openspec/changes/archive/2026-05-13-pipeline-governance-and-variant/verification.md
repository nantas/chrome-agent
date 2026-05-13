# Verification

## Spec-to-Implementation 覆盖

### pipeline-strategy-schema

| Requirement | Scenario | 实现位置 | 状态 |
|------------|----------|---------|------|
| 策略 ID 注册中心权威声明 | Registry 作为引用完整性依据 | `orchestrate.py` — `STRATEGY_REGISTRY` 公共导出 | ✅ |
| 策略文件 ID 引用完整性校验 | Pipeline 启动校验 hard-fail | `orchestrate.py` — `build_pipeline()` ValueError | ✅ |
| 策略文件 ID 引用完整性校验 | Pipeline 降级已弃用 | `orchestrate.py` — warning 移除，改为 ValueError | ✅ |
| 策略文件 ID 引用完整性校验 | bootstrap-strategy 输出前校验 | `strategy_scaffold_generator.py` — importlib 校验 | ✅ |
| 扩展协议 | 合规扩展 | AGENTS.md Pipeline Strategy Schema 治理章节 | ✅ |
| 扩展协议 | 违规扩展被拒绝 | `build_pipeline()` ValueError 拒绝未注册 ID | ✅ |
| Registry 变更约束 | 安全删除/安全新增 | AGENTS.md Registry 变更约束章节 | ✅ |

### platform-variant-framework

| Requirement | Scenario | 实现位置 | 状态 |
|------------|----------|---------|------|
| platform_variant 声明字段 | variant 声明示例 | `orchestrate.py` — `run_pipeline()` 解析 | ✅ |
| platform_variant 声明字段 | variant 默认值 | `orchestrate.py` — 默认 `"standard"` | ✅ |
| platform_variant 声明字段 | variant 与 template 映射 | `mediawiki-fandom.yaml` / `mediawiki-wiki-gg.yaml` 更新 | ✅ |
| Variant 行为分支接口 | Variant 传递 | `phase_a.py` / `phase_b.py` 签名扩展 + 日志 | ✅ |
| Variant 注册扩展 | 新增 variant 时的分支扩展 | AGENTS.md variant 受控词汇表 | ✅ |

### site-strategy (modified)

| Requirement | Scenario | 实现位置 | 状态 |
|------------|----------|---------|------|
| YAML frontmatter 新增字段 | platform_variant | `site-strategy-schema/spec.md` 新增字段定义 | ✅ |
| content_profile ID 引用约束 | 引用已注册 ID | `build_pipeline()` 正常通过 | ✅ |
| content_profile ID 引用约束 | 引用未注册 ID | `build_pipeline()` ValueError 拒绝 | ✅ |
| content_profile ID 引用约束 | content_profile 不完整 | `build_pipeline()` 仅校验已指定字段 | ✅ |
| 注册表 ID 清单同步 | AGENTS.md ID 参考表 | AGENTS.md Pipeline Strategy Schema 治理章节 | ✅ |

### agents-governance (modified)

| Requirement | Scenario | 实现位置 | 状态 |
|------------|----------|---------|------|
| Pipeline Strategy Schema 治理章节 | 章节结构 | AGENTS.md + `agents-governance/spec.md` | ✅ |

### mediawiki-api-extraction-pipeline (modified)

| Requirement | Scenario | 实现位置 | 状态 |
|------------|----------|---------|------|
| Pipeline 启动时策略 schema hard-fail 校验 | 校验通过 | `build_pipeline()` 正常返回 | ✅ |
| Pipeline 启动时策略 schema hard-fail 校验 | 校验拒绝 | `run_pipeline()` 捕获 ValueError → `EXIT_STRATEGY_ERROR` | ✅ |
| Pipeline 启动时策略 schema hard-fail 校验 | 无 content_profile | `build_pipeline()` 全默认，不触发校验 | ✅ |
| Pipeline platform_variant 行为分支 | Variant 传递 | `run_pipeline()` 解析 + 传递给 phase_a/b | ✅ |
| Registry 暴露为可导入模块 | 外部导入 registry | `STRATEGY_REGISTRY = _STRATEGY_REGISTRY` | ✅ |

## Task-to-Evidence 映射

| Task | 证据 |
|------|------|
| 1.1-1.3 | Spec 阅读确认 + grep 结果 |
| 2.1.1 | `orchestrate.py` — `build_pipeline()` ValueError 替代 warning |
| 2.1.2 | `orchestrate.py` — `STRATEGY_REGISTRY = _STRATEGY_REGISTRY` |
| 2.1.3 | `orchestrate.py` — `run_pipeline()` try/except ValueError |
| 2.2.1-2.2.2 | `strategy_scaffold_generator.py` — importlib 导入 + 校验循环 |
| 2.3.1 | `orchestrate.py` — `platform_variant = strategy.get(...)` |
| 2.3.2 | `phase_a.py` / `phase_b.py` — keyword-only `platform_variant` 参数 |
| 2.4.1 | `mediawiki-fandom.yaml` — `platform_variant: fandom` |
| 2.4.2 | `mediawiki-wiki-gg.yaml` — `platform_variant: wiki-gg` |
| 2.4.3 | `mediawiki.yaml` — 保持不变（无 platform_variant） |
| 2.4.4 | grep 确认模板无 content_profile 占位符 |
| 2.5.1-2.5.2 | AGENTS.md — Pipeline Strategy Schema 治理子章节 |
| 2.5.3 | `agents-governance/spec.md` — 新增 Requirement |
| 2.6.1-2.6.3 | `site-strategy-schema/spec.md` — 新增 platform_variant + 引用约束 |
| 3.1-3.2 | 验证检查点 + 回写目标标记 |

## 回写目标确认

| 回写目标 | 变更内容 | 状态 |
|---------|---------|------|
| `AGENTS.md` | 新增 Pipeline Strategy Schema 治理子章节 | ✅ 已直接写入 |
| `scripts/mediawiki-api-extract/pipeline/orchestrate.py` | hard-fail 校验 + STRATEGY_REGISTRY 导出 + platform_variant 解析 | ✅ 已直接写入 |
| `scripts/explore/strategy_scaffold_generator.py` | importlib 导入 + content_profile 校验 | ✅ 已直接写入 |
| `sites/templates/mediawiki-fandom.yaml` | `platform_variant: fandom` | ✅ 已直接写入 |
| `sites/templates/mediawiki-wiki-gg.yaml` | `platform_variant: wiki-gg` | ✅ 已直接写入 |
| `openspec/specs/agents-governance/spec.md` | Pipeline Strategy Schema 治理 Requirement | ✅ 已直接写入 |
| `openspec/specs/site-strategy-schema/spec.md` | platform_variant + 引用约束 | ✅ 已直接写入 |
