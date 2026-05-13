# Proposal

## 问题定义

Neon Abyss Fandom Wiki crawl 暴露的 7 个问题中，P1（Phase B missingtitle 未处理）、P6（_process_html_page None-safety）、P7（Phase A 包含不存在的页面）和 P2（策略注册表缺 short_name 和 fandom_infobox）属于具体的管线代码缺陷。这些问题在 `pipeline-governance-and-variant` change 建立的治理框架下，可以进行针对性修复。

本 change 聚焦于在治理框架约束下修复现有管线代码，使 Fandom 站点的 MediaWiki API 管线可正常执行。

## 范围边界

**范围内：**
- 修复 `client._request()` 的 API error 语义化，区分 missingtitle 和系统错误
- 修复 `HtmlRenderedAcquisitionStrategy.fetch_page_content()` 处理 missingtitle（不抛异常、返回空内容）
- 修复 `_process_html_page()` 的 None-safety（`raw.get("html") or ""`）
- 修复 Phase A 的页面过滤逻辑（排除翻译页、对 Fandom variant 增加内容页验证）
- 补充 `_STRATEGY_REGISTRY` 中缺失的 `fandom_infobox` 模板处理器
- 修正 `neonabyss.fandom.com/strategy.md` 的 content_profile 引用（`short_name` → `short_name_with_cross_namespace`，或注册正确的 ID）

**范围外：**
- 不涉及 checkpoint/resume 机制（P4，留作后续独立 change）
- 不涉及 bash timeout 配置（P3，运行环境问题）
- 不涉及新的平台变体体系（已由 governance change 覆盖）
- 不改变现有非 Fandom 站点的行为（wiki.gg / standard MediaWiki）

## Capabilities

### New Capabilities
- `api-error-semantics`: MediaWiki API 响应错误的语义化层次结构，包括可跳过的业务异常（missingtitle、nosuchpage）和不可恢复的系统异常

### Modified Capabilities
- `mediawiki-api-extraction-pipeline`: 修复 Phase A 页面过滤、Phase B None-safety、Phase B missingtitle 优雅处理；补充 Registry 中缺失的策略 ID（fandom_infobox）
- `site-strategy`: 修正 neonabyss.fandom.com 策略文件的 content_profile 引用，使其符合刚刚建立的 schema 约束

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

| 受影响组件 | 影响类型 | 描述 |
|-----------|---------|------|
| `scripts/mediawiki-api-extract/client.py` | 功能新增 | `PageNotFoundError` 新异常类 |
| `scripts/mediawiki-api-extract/strategies/acquisition.py` | 行为变更 | HTML 获取路径对 missingtitle 的处理 |
| `scripts/mediawiki-api-extract/pipeline/phase_b.py` | 行为变更 | None-safety + missingtitle skip |
| `scripts/mediawiki-api-extract/pipeline/phase_a.py` | 行为变更 | Fandom 翻译页过滤 + 存在性验证 |
| `scripts/mediawiki-api-extract/pipeline/orchestrate.py` | 结构变更 | Registry 补充 fandom_infobox 条目 |
| `sites/strategies/neonabyss.fandom.com/strategy.md` | 内容修正 | content_profile 引用修正 |

## 关联绑定

- 关联 binding: `binding.md`
- 治理框架 change: `openspec/changes/pipeline-governance-and-variant/`
