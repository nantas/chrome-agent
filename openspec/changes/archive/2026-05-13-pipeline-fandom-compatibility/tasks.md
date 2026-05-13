# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 3 个 delta spec 的实现范围与边界（api-error-semantics、mediawiki-api-extraction-pipeline、site-strategy）
- [x] 1.2 确认依赖关系：本 change 依赖 `pipeline-governance-and-variant` 的 platform_variant 传递框架已就位
- [x] 1.3 grep 所有 `sites/strategies/*/strategy.md` 扫描 content_profile 引用，生成待修复列表

## 2. 核心实现任务

### 2.1 API 错误语义化

- [x] 2.1.1 在 `client.py` 中定义 `PageNotFoundError`（继承 `Exception`），docstring 标注触发条件
  - Spec: `api-error-semantics` — Requirement "异常层次结构"
- [x] 2.1.2 修改 `_request()`：检测 `data["error"]["code"]`，missingtitle/nosuchpage → raise `PageNotFoundError`
  - Spec: `api-error-semantics` — Scenario "missingtitle 页面触发 PageNotFoundError"
  - Design: Decision 1
  - 验证方式：mock API 返回 `{"error": {"code": "missingtitle"}}` 可触发 `PageNotFoundError`

### 2.2 Phase A 页面过滤（Fandom variant）

- [x] 2.2.1 在 `run_phase_a()` 中新增：当 `platform_variant == "fandom"` 时过滤 `_tr` 后缀页面
  - Spec: `mediawiki-api-extraction-pipeline` — Requirement "Phase A Fandom 翻译页过滤"
  - Design: Decision 2
- [x] 2.2.2 在 `run_phase_a()` 中新增：当 `platform_variant == "fandom"` 时执行 `prop=info` 批量存在性验证
  - Spec: `mediawiki-api-extraction-pipeline` — Requirement "Phase A 页面存在性验证"
  - 验证方式：mock API 返回 `missing` 页面被过滤，manifest 中不包含

### 2.3 Phase B 错误处理

- [x] 2.3.1 修改 `process_single_page()`：在 `content_strategy.fetch_page_content()` 调用处捕获 `PageNotFoundError`，返回 `status: "skipped"`
  - Spec: `api-error-semantics` — Requirement "Phase B 对 PageNotFoundError 的优雅处理"
  - Design: Decision 3
- [x] 2.3.2 修改 `run_phase_b()` 统计：增加 `stats["skipped"]` 字段；failure_rate 仅统计 `status: "error"`（排除 skipped）
  - Spec: `mediawiki-api-extraction-pipeline` — Scenario "统计区分 skipped"
  - Design: Decision 4
  - 验证方式：包含 skipped 页面时 failure_rate 正确排除 skipped

### 2.4 _process_html_page None-safety

- [x] 2.4.1 在 `phase_b.py` 的 `_process_html_page()` 中，将 `raw.get("html", "")` 改为 `raw.get("html") or ""`
  - Spec: `api-error-semantics` — Requirement "_process_html_page None-safety"
  - 验证方式：`raw = {"html": None}` 时返回 `status: "empty"` 而不崩溃

### 2.5 Registry 补充

- [x] 2.5.1 在 `strategies/__init__.py` 或 `strategies/template_processor.py` 中实现 `FandomInfoboxTemplateProcessor`（最小可用版本）
  - Spec: `mediawiki-api-extraction-pipeline` — Requirement "Registry 补充 fandom_infobox"
  - 验证方式：解析 `{{Infobox item|name=Acorn|image=Acorn.png}}` 返回正确 frontmatter
- [x] 2.5.2 在 `_STRATEGY_REGISTRY["template_processor"]` 中注册 `"fandom_infobox": FandomInfoboxTemplateProcessor`
  - 验证方式：registry 中包含该 ID

### 2.6 策略文件修正

- [x] 2.6.1 修正 `sites/strategies/neonabyss.fandom.com/strategy.md`：
  - `link_resolver: "short_name"` → `"short_name_with_cross_namespace"`
  - `template_processor: "fandom_infobox"`（保持，因已注册）
  - 新增 `api.platform_variant: fandom`
  - Spec: `site-strategy` — Requirement "neonabyss.fandom.com 策略文件 content_profile 修正"
- [x] 2.6.2 确认扫描发现的任何其他策略文件 content_profile 问题已修复
  - Spec: `site-strategy` — Requirement "现有策略文件排查"

## 3. 收敛与验证准备

- [x] 3.1 整理验证检查点：pipeline 在 neonabyss 策略上可完成 Phase B（不再因 missingtitle 崩溃）；skipped 统计正确；策略文件引用合法
- [x] 3.2 标记需要回写的变更：client.py + phase_a.py + phase_b.py + strategies/ + orchestrate.py + 策略文件

## 4. 验证与回写收敛

- [x] 4.1 基于实现结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行 writeback.md 中定义的回写目标
