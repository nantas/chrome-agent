# Design

## Context

治理框架 change（`pipeline-governance-and-variant`）建立了策略 schema 约束和 platform_variant 框架。本 change 在此框架下修复 Fandom 站点的管线兼容性问题，具体针对 Neon Abyss postmortem 中的 P1、P2（部分）、P6、P7。

修复都是在治理约束下的旧代码修补，不引入新的治理规则。

## Goals / Non-Goals

**Goals:**
- 引入 `PageNotFoundError` 异常层次，分离 missingtitle 和系统错误（spec: `api-error-semantics`）
- 修复 `_process_html_page()` 的 None-safety（spec: `api-error-semantics`）
- Phase A 增加 Fandom 翻译页过滤和存在性验证（spec: `mediawiki-api-extraction-pipeline`）
- Phase B 对 `PageNotFoundError` 优雅跳跃（spec: `mediawiki-api-extraction-pipeline`）
- 注册 `fandom_infobox` 到 `_STRATEGY_REGISTRY`（spec: `mediawiki-api-extraction-pipeline`）
- 修正 neonabyss 策略文件的 content_profile 和 platform_variant（spec: `site-strategy`）
- 扫描所有策略文件排查 ID 引用问题（spec: `site-strategy`）

**Non-Goals:**
- 不实现 checkpoint/resume（P4）
- 不修改 bash timeout 相关逻辑（P3）
- 不修改非 Fandom 相关代码

## Decisions

### Decision 1: 异常类的存放位置

**选择**：在 `client.py` 中定义 `PageNotFoundError` 异常类。

**理由**：
- `client._request()` 是 API 错误发生的准确位置
- 所有抛出的异常在同一文件中定义，查询方便
- 导入简单：`from .client import PageNotFoundError`

### Decision 2: Phase A 过滤的实现方式

**选择**：在 `run_phase_a()` 函数中，在 `discover_pages` 调用之后、manifest 构建之前，增加 Fandom 特定的过滤步骤。

**理由**：
- 保持 `DiscoveryStrategy` 的平台无关性（策略类不变）
- Fandom 过滤逻辑是管线层面的关心（依赖 platform_variant 参数）
- 过滤后的 pages 列表继续进入后续的 categories 发现和 manifest 构建

### Decision 3: FandomInfoboxTemplateProcessor 的最小可用范围

**选择**：实现一个最小可用的 `FandomInfoboxTemplateProcessor`，仅支持：
- 解析 `{{Infobox ...|param1=val1|param2=val2}}` 格式
- 提取参数到 frontmatter
- 从 wikitext 中移除 infobox 调用
- 基本模板展开（`{{ItemLink|...}}` 等）

**理由**：
- 当前 neonabyss 策略使用 `html_rendered` 内容获取，不经过 wikitext 路径
- 但 Phase B 的 `_process_html_page()` 中已有 wikitext fallback 路径
- 最小实现保证注册 ID 完整可用，功能可后续增强

### Decision 4: 统计维度扩展

**选择**：在 `run_phase_b()` 的 `stats` dict 中增加 `"skipped"` 字段，failure_rate 改为以 total 为分母计算（含 skipped）。

**理由**：
- skipped 与 error 是不同语义：skipped 是预期中的页面不存在，error 是异常
- 统一按 total 计算 failure_rate 保持分母一致
- 50% fallback 阈值只按 error 计算（skipped 不计入）

## Risks / Migration

### Risk 1: PageNotFoundError 可能未被所有调用点捕获

**风险**：`client._request()` 改为在某些场景下抛出 `PageNotFoundError` 而非 `RuntimeError` 后，可能存在未更新 catch 的调用点。

**缓解**：
- `PageNotFoundError` 继承自 `Exception`，现有 `except Exception` 仍然捕获
- 唯一受影响的差异化处理在 `process_single_page()` 中—已计划修复

### Risk 2: Fandom 翻译页过滤规则可能过粗略

**风险**：`title.endswith("/tr")` 或 `"tr"` 规则可能误杀以 `tr` 结尾的合法页面。

**缓解**：
- 仅在 `platform_variant == "fandom"` 时启用
- `prop=info` 页面存在性验证作为第二道防线
- 未来可以增加更精确的模式匹配（如正则 `_tr$` 确保仅匹配翻译页后缀）
