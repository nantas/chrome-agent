# Writeback

## Change: pipeline-fandom-compatibility
## Status: Ready for writeback

---

## Writeback Targets

### 1. `scripts/mediawiki-api-extract/client.py`

**变更类型**: 功能新增

**变更内容**:
- 新增 `PageNotFoundError` 异常类（继承 `Exception`），携带 `page_title` 和 `code` 属性
- 修改 `_request()`：检测 `data["error"]["code"]`，`missingtitle`/`nosuchpage` → `raise PageNotFoundError`，其他保持 `RuntimeError`

**回写结论**: 已实现。API 错误响应现在区分可跳过的业务异常（页面不存在）和不可恢复的系统异常。

### 2. `scripts/mediawiki-api-extract/pipeline/phase_a.py`

**变更类型**: 行为变更

**变更内容**:
- 新增 Fandom 翻译页过滤：`platform_variant == "fandom"` 时过滤 `/tr` 和 `_tr` 后缀页面
- 新增 `prop=info` 批量存在性验证：`platform_variant == "fandom"` 时验证页面存在性，过滤 missing 页面
- API 验证失败时 fail-open（保留所有页面）

**回写结论**: 已实现。Phase A 在 Fandom 变体下执行两层过滤：翻译页 → 不存在页。

### 3. `scripts/mediawiki-api-extract/pipeline/phase_b.py`

**变更类型**: 行为变更

**变更内容**:
- `process_single_page()` 新增 `PageNotFoundError` 捕获，返回 `status: "skipped"`
- `_process_html_page()` None-safety 修复：`raw.get("html") or ""`
- `run_phase_b()` 统计扩展：新增 `skipped_count`，`failure_rate` 仅统计 error
- 日志区分 skipped 和 error

**回写结论**: 已实现。Phase B 优雅处理页面不存在，统计维度完整。

### 4. `scripts/mediawiki-api-extract/strategies/template.py`

**变更类型**: 功能新增

**变更内容**:
- 新增 `FandomInfoboxTemplateProcessor` 类（最小可用版本）
- 支持 Fandom `{{Infobox ...}}` 模板参数提取
- 支持 Fandom 辅助链接模板解析（`{{ItemLink}}`, `{{MonsterLink}}` 等）

**回写结论**: 已实现。最小可用版本覆盖 Infobox 参数提取、模板移除和辅助模板清理。

### 5. `scripts/mediawiki-api-extract/strategies/__init__.py`

**变更类型**: 导出更新

**变更内容**:
- re-export 新增 `FandomInfoboxTemplateProcessor`

**回写结论**: 已实现。

### 6. `scripts/mediawiki-api-extract/pipeline/orchestrate.py`

**变更类型**: 结构变更

**变更内容**:
- `_STRATEGY_REGISTRY["template_processor"]` 新增 `"fandom_infobox": FandomInfoboxTemplateProcessor`
- import 新增 `FandomInfoboxTemplateProcessor`

**回写结论**: 已实现。Registry 包含 `fandom_infobox` ID。

### 7. `sites/strategies/neonabyss.fandom.com/strategy.md`

**变更类型**: 内容修正

**变更内容**:
- `link_resolver: "short_name"` → `"short_name_with_cross_namespace"`
- 新增 `api.platform_variant: fandom`

**回写结论**: 已实现。策略文件所有 content_profile ID 均已在 Registry 中注册。

---

## AGENTS.md 影响评估

**是否需要更新 AGENTS.md**: 否

理由：
- 未引入新的引擎或能力
- `_STRATEGY_REGISTRY` 的当前注册 ID 清单在 AGENTS.md Section 7 中已声明为"以代码为准"
- `platform_variant: fandom` 的值已在 AGENTS.md Section 7 的 `platform_variant` 声明表中列出

---

## Verification Summary

34/34 验证检查项全部通过。详见 `verification.md`。
