# Proposal

## 问题定义

两处 convert 路径的声明与现实漂移，合并为一个 change 修复：

**C5 — `standalone.py` 是未声明的第三编排器，且存在真实等价漂移：**

`scripts/pipeline/cli.py` 的 5 个子命令中，`fetch` / `reprocess` / `reconvert` 三个都经 `scripts/pipeline/standalone.py`（共 ~247 行），只有 `pipeline` 子命令走声明的 orchestrator→convert（CV4 镜像）路径。`standalone.py::fetch_and_convert` 几乎完整复制了 `convert.py::_process_html_page` 的编排（HtmlToMarkdownConverter 实例化、frontmatter YAML 装配、`# {title}` 条件前置、`extract_card_stats` 注入），但**直接 `converter.convert_body(html)`，跳过了 `preprocess_html(html, extraction_config)`**。后果：cleanup_selectors、strip_footer、lazyload 等配置驱动的清理在三个 standalone 子命令里全部失效，而 `pipeline` 子命令会执行——同一策略下两条路径产出不同 Markdown，违反 ADR 0013 §4.3 的镜像等价契约。`00-target-architecture.md` §3.1 的镜像表完全未登记 standalone。

**C3 — convert 内核三层入口缺声明，易被误判为漂移：**

`lib/extraction/converter.py` 有三个公开入口：`HtmlToMarkdownConverter` 类（实现层）、`convert_html_to_markdown()` 函数（无状态便捷入口）、`convert_page_full()` 函数（全页编排，声明的单一 kernel entry）。三层是合理分层（CV4 因需 link index/source_dir 实例状态而合理直接用类），本 session 等价测试已守护，但 §3.1 未声明「为什么 CV4 直接用类而非走函数入口」，未来审查会重复质疑。

## 范围边界

**范围内：**
- `standalone.py::fetch_and_convert` 改为构造 `raw`/`page_info` 后委托 `convert.convert_single_page(...)`（CV4 镜像），消除 ~60 行重复编排，自动修复 preprocess 漂移
- `standalone.py::reconvert_file` 无 source_url 分支改用 `convert_page_full(body, {})` 对齐内核入口（有 source_url 分支转调新 `fetch_and_convert`，自动获益）
- `standalone.py::reprocess_pages` 循环保持，转调新 `fetch_and_convert`
- `00-target-architecture.md` §3.1：将 standalone 声明为 CV4 薄壳变体（B 轴：pipeline-standalone）；补「内核三层接口」声明
- 回归测试：覆盖 fetch 子命令产出含 cleanup 效果（证明 preprocess 漂移已修）

**范围外：**
- `cli.py` 子命令签名/参数/退出码变更（保持不变）
- wikitext 模式路径（本就走 `convert_wikitext_to_markdown`，与本次 HTML 漂移无关）
- `lib/extraction/converter.py` 任何代码变更（内核不动）
- C4（cli.mjs crawl handler 提取）—— 独立 change，本次之后
- 任何新能力

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `convert`: 声明 standalone 编排器为 CV4 薄壳变体（B 轴 pipeline-standalone），等价证明复用 `tests/test_convert_equivalence.py`；补内核三层接口契约（类/函数/full-orchestration 各自适用条件）

## Capabilities 待确认项

- [x] 能力清单已确认（仅 convert 一个能力，Modified）

## Impact

- **行为影响**：fetch/reprocess/reconvert 子命令的 HTML 模式产出 SHALL 与 pipeline 子命令对齐（含 preprocess 清理效果）。方向是修 bug（配置驱动的清理此前在这三子命令里静默失效），非引入新差异。wikitext 模式零影响
- **spec 影响**：convert capability 增补 standalone 变体声明 + 内核三层接口契约
- **测试影响**：新增 standalone 回归测试（证明 fetch 子命令应用 cleanup_selectors）；现有 `test_convert_equivalence.py` 继续守护 CV4 内核等价
- **代码量**：standalone.py 净减（折叠重复编排）；00-target-architecture 增声明段落

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：ADR 0013、00-target-architecture §3.1+§4.3、GOVERNANCE §3
  - 项目页：架构审查报告候选 3+5、arch-review-followups verification
  - 回写目标：00-target-architecture §3.1、CONTEXT.md（如需）
