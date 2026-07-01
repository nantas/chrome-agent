# Proposal

## 问题定义

chrome-agent 的 Convert 能力当前有 **3 份独立的 HTML→Markdown 实现**，违反了 [ADR 0013 的 4 维领域模型](../../../docs/adr/0013-four-dimensional-domain-model.md) 和 [00-target-architecture.md](../../../docs/architecture/00-target-architecture.md) §3.1 的目标架构：

| 实现 | 技术 | 调用者 | 状态 |
|------|------|--------|------|
| `lib/extraction/converter.py` (683 行) | selectolax | pipeline convert.py + explore sample_converter.py + standalone.py | ✅ 共享内核 |
| `lib/extraction/html_to_markdown.py` (337 行) | python regex | pipeline(cdp) convert_html.py + test_runner.py | ⚠️ 独立路径 |
| `pipeline/converters/fandom_html_to_markdown.py` (271 行) | bs4+markdownify | 无 | ❌ 死代码 |

根因：
- `fandom_html_to_markdown.py` 创建于 2026-06-10（Nintendo 门户需求），但所有功能已被 `converter.py` + `preprocessor.py` 的配置驱动 cleanup ops 覆盖，自始至终零调用者。
- `html_to_markdown.py` 创建于同一时期，使用 python regex 而非 selectolax，仅被 CDP 执行路径（`convert_html.py`）调用——它和 `converter.py` 做同一件事（HTML→MD），只是用了不同的底层实现。

这意味着：
1. **C 轴（策略变体）通过代码分叉表达**——fandom 逻辑应该走 strategy.md 配置驱动，不应该有独立文件
2. **B 轴（执行路径）复制了内核**——CDP 路径用 regex 实现，pipeline 路径用 selectolax 实现，实际上执行的是同一能力
3. **没有镜像等价测试**——三条路径的输出从未对比过，无法证明它们等价

## 范围边界

**包含**：
- 删除 `pipeline/converters/fandom_html_to_markdown.py`（死代码）
- 将 CDP 路径 (`pipeline/phases/convert_html.py`) 从 `html_to_markdown` 切到 `converter.py.convert_html_to_markdown(wiki_domain=None)`
- 删除 `lib/extraction/html_to_markdown.py`
- 添加 mirror equivalence golden snapshot 测试（同一 HTML 样本走 explore + pipeline 两条路径，断言输出相同）
- 更新 `test_runner.py` 使用 converter.py 替代 html_to_markdown
- 更新架构文档回写

**不包含**：
- 修改 `converter.py` 核心逻辑（仅增加调用入口如有需要）
- 修改 `chrome-agent-cli.mjs` 的 JS `htmlToMarkdown()` fallback（该函数是 Node.js 侧的独立轻量兜底，注册为基础设施，不参与能力体系）
- 修改 preprocessor 的 `context` 参数（属于 change `unify-extract-fetch-kernels`）
- 修改其他 Convert 变体（wikitext、card_stats、link_fixer）

## Capabilities

### Modified Capabilities

- `pipeline-convert-phase`: Convert HTML 阶段统一走 selectolax 内核，删除 regex 独立路径；CDP 路径纳入镜像等价测试
- `pipeline-converters`: 删除 `fandom_html_to_markdown.py` 模块；所有策略变体通过 strategy.md 配置驱动

## Impact

| 受影响的文件 | 变更类型 |
|-------------|---------|
| `scripts/pipeline/converters/fandom_html_to_markdown.py` | 删除 |
| `scripts/lib/extraction/html_to_markdown.py` | 删除 |
| `scripts/pipeline/pipeline/phases/convert_html.py` | 修改 import 路径 |
| `scripts/test_runner.py` | 修改 import 路径 |
| `tests/` | 新增 golden snapshot 测试 |
| `docs/architecture/01-overview.md` | 移除死代码引用（已完成于 Stage 2） |
| `docs/architecture/05-converter-architecture.md` | 更新模块清单（已完成于 Stage 2） |
| `AGENTS.md` §2 | 更新 Convert 能力表（已完成于 Stage 2） |

## 关联绑定

- 关联 binding: [binding.md](./binding.md)
- 已确认标准页 / 项目页 / 回写目标：`openspec/specs/pipeline-converters/spec.md`, `docs/architecture/00-target-architecture.md`, `AGENTS.md` §2
