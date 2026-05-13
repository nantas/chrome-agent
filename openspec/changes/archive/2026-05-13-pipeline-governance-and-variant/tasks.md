# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 5 个 delta spec 的实现范围与边界（pipeline-strategy-schema、platform-variant-framework、site-strategy、agents-governance、mediawiki-api-extraction-pipeline）
- [x] 1.2 确认无外部依赖项（所有变更在 chrome-agent 仓库内完成）
- [x] 1.3 在代码库中 grep 所有 strategy.md 的 content_profile 引用，识别现有策略文件中是否存在未注册 ID 引用

## 2. 核心实现任务

### 2.1 Pipeline 启动时策略 schema hard-fail 校验

- [x] 2.1.1 在 `build_pipeline()` 中增加 content_profile ID 校验逻辑：遍历 content_profile 各字段，对照 `_STRATEGY_REGISTRY` 校验存在性
  - Spec: `pipeline-strategy-schema` — Requirement "策略文件 ID 引用完整性校验", Scenario "Pipeline 启动校验 hard-fail"
  - Design: Decision 1
  - 验证方式：NEONABYSS 策略使用 `short_name`（不存在的 ID）时 pipeline 返回 EXIT_STRATEGY_ERROR，日志包含缺失 ID 提示
- [x] 2.1.2 将 `_STRATEGY_REGISTRY` 暴露为模块级 `STRATEGY_REGISTRY` 公共 API
  - Spec: `mediawiki-api-extraction-pipeline` — Requirement "Registry 暴露为可导入模块"
  - Design: Decision 2
  - 验证方式：`from ..pipeline.orchestrate import STRATEGY_REGISTRY` 可正常工作
- [x] 2.1.3 增加 `run_pipeline()` 对 `ValueError` 的捕获，返回 `EXIT_STRATEGY_ERROR`

### 2.2 bootstrap-strategy 输出校验

- [x] 2.2.1 在 `strategy_scaffold_generator.generate()` 中导入 `STRATEGY_REGISTRY`
- [x] 2.2.2 生成 scaffold 后、写入文件前，校验 content_profile 字段的所有 ID 在 registry 中存在
  - Spec: `pipeline-strategy-schema` — Scenario "bootstrap-strategy 输出前校验"
  - Design: Decision 3
  - 验证方式：模板引用无效 ID 时生成失败并报告缺失 ID

### 2.3 platform_variant 解析与传递

- [x] 2.3.1 在 `run_pipeline()` 中解析 `platform_variant`，默认 `"standard"`
  - Spec: `platform-variant-framework` — Requirement "platform_variant 声明字段"
  - Design: Decision 4
  - 验证方式：日志输出包含 `Platform variant: standard`（默认值）
- [x] 2.3.2 扩展 `run_phase_a()` 和 `run_phase_b()` 函数签名，增加可选的 `platform_variant` 参数（当前仅接受和记录，不实现行为分支）
  - Spec: `platform-variant-framework` — Scenario "Variant 传递"
  - 验证方式：函数签名变更后 pipeline 对现有策略行为不变

### 2.4 策略模板更新

- [x] 2.4.1 更新 `sites/templates/mediawiki-fandom.yaml` 增加 `api.platform_variant: fandom`
- [x] 2.4.2 更新 `sites/templates/mediawiki-wiki-gg.yaml` 增加 `api.platform_variant: wiki-gg`
- [x] 2.4.3 更新 `sites/templates/mediawiki.yaml` 保持无 platform_variant 或显式 `standard`
- [x] 2.4.4 清理现有 strategy 模板内容：移除可能导致引用未注册 ID 的内容（如有 content_profile 占位符）

### 2.5 AGENTS.md 治理约束

- [x] 2.5.1 在 AGENTS.md Section 7（策略库治理）之后新增 `### Pipeline Strategy Schema 治理` 子章节
  - Spec: `agents-governance` — Requirement "Pipeline Strategy Schema 治理章节"
  - Design: Decision 5
- [x] 2.5.2 在子章节中写入：权威来源声明、策略文件约束、扩展协议、注册 ID 清单、Registry 变更约束
  - 引用 `scripts/mediawiki-api-extract/pipeline/orchestrate.py` 中的 `_STRATEGY_REGISTRY`
  - ID 清单保持与代码同步
- [x] 2.5.3 同步更新 `openspec/specs/agents-governance/spec.md` 主 spec（如有变更）

### 2.6 site-strategy-schema 主 spec 同步

- [x] 2.6.1 在 `openspec/specs/site-strategy-schema/spec.md` 中增加 `platform_variant` 字段定义
- [x] 2.6.2 增加 `content_profile` ID 引用完整性约束的描述
- [x] 2.6.3 更新 capability 声明（新增 `page_parse_config` 等如有需求）

## 3. 收敛与验证准备

- [x] 3.1 整理验证检查点：pipeline 新策略文件拒绝执行 / 现有策略文件正常执行 / bootstrap-strategy 输出校验 / AGENTS.md 章节完整性
- [x] 3.2 标记需要回写的变更：AGENTS.md 更新 + 模板更新 + 主 spec 同步

## 4. 验证与回写收敛

- [x] 4.1 基于实现结果生成 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
