# Design

## Context

`convert_page_full`（CV1 kernel）当前是 4 步：extract infobox → preprocess HTML → convert → prepend infobox。CV3（`sample_converter._apply_extraction`）调它之后**额外**跑 ~50 行 markdown 层 post-op（config-driven：`text_normalization`/`url_conversion`/`youtube_cleanup` + 3 个 cleanup ops + 无条件 escape-artifact 清理）。CV4（`_process_html_page`）完全跳过这段。结果：4 站配置这些 key 的策略，explore 产出 ≠ pipeline 产出；等价证明 fixture 刻意省略分歧 key，永远绿但绑不住真实策略；`convert.py:165` 的 proxy 注释虚假；registry 把 3 个 cleanup_ops 错指 sample_converter.py。

规范真源：`specs/convert/spec.md` 的 MODIFIED `convert-kernel-three-layer-interface`——新增第 4 个公开入口 `apply_post_conversion_ops` + 4 个新 scenario。

## Goals / Non-Goals

**Goals:**
- 消除 CV3/CV4 的 markdown 层 post-op 分歧：post-op 抽成 kernel 公开函数 `apply_post_conversion_ops(md, extraction_rules)`，两条 B 轴路径都调它
- 让等价证明对真实策略自洽：新增启用分歧 key 的 fixture，断言 CV3≡CV4≡kernel
- 履行不变量 I2（mirror 不含变换逻辑）：CV3 `_apply_extraction` 删掉内联 post-op，回归 explore spec 声明的「4 步」薄壳
- 订正 `convert.py:165` 虚假注释 + `capability-registry.yaml` 错误归属

**Non-Goals:**
- 不让 CV4 改走 `convert_page_full`——`convert-kernel-three-layer-interface` spec 刻意让 CV4 直接用 class（link-index 状态）。本 change 尊重该决策
- 不改 post-op 的变换语义或清单（只搬家，不增删能力）
- 不把 escape-artifact 清理改成 config-gated（保留无条件；见 D4）
- 不重写 `00-target-architecture.md` §3.1 的维度坐标（仅订正 post-op 归属措辞）

## Decisions

**D1 — post-op 函数的物理归宿 = `converter.py` 内、`convert_page_full` 之后。** 候选：(a) 新模块 `lib/extraction/post_ops.py`；(b) `converter.py` 内 `convert_page_full` 之后。选 (b)：post-op 与转换产出强相关、且 `convert_page_full` 是它的主调用方，同模块避免 import 开销 + 读者一处看全转换管线。函数签名 `apply_post_conversion_ops(md: str, extraction_rules: dict) -> str`，纯函数（无 self、无 I/O）。代码 = 把 `sample_converter._apply_extraction:140-205` 的 post-op 块原样搬过来（含 `re` 用法），不改逻辑。

**D2 — `convert_page_full` 调它作为第 5 步；CV3 `_apply_extraction` 删内联块。** CV3 经 `convert_page_full` 自动获得 post-op，行为字节不变（同一组变换、同一调用序）。`_apply_extraction` 收缩为 `return convert_page_full(html, extraction_rules)`（保留 `known_pages` 参数签名以免破坏调用方，但函数体内不再使用——post-op 不需要它）。explore spec `apply-extraction-uses-shared-lib` 声明的「4 步」由 `convert_page_full` 承接，post-op 是 kernel 的第 5 步（kernel spec 声明），explore spec 不再提及 post-op。

**D3 — CV4 `_process_html_page` 显式调 `apply_post_conversion_ops`。** CV4 不能走 `convert_page_full`（需要 `build_link_index(manifest_pages, redirect_map)` 的实例状态）。所以在 `md_content = converter.convert_body(...)` 之后插入 `md_content = apply_post_conversion_ops(md_content, extraction_config or {})`。这是**唯一的行为变更点**：CV4 此前跳过，现在 honoring 相同 key。`convert.py:165` 注释订正为事实（proxy 声称变真）。

**D4 — escape-artifact 清理保留无条件。** 当前 CV3 无条件跑 `\*\*\*`→`***` + `\*+`→`*+`。它是 no-op sentinel（kernel 不 escape 星号，所以没东西可清）。搬进 `apply_post_conversion_ops` 后两条路径都跑。sentinel 原本的「CV3-vs-CV4 分歧检测」职责被 byte-equality 证明吸收（统一后无分歧可测；要测 kernel 是否开始 escape，等价证明的 byte 比对即 canary）。design 选择无条件而非 config-gated，因为：它是安全网（清理意外 escape），config-gate 反而会让遗漏的 escape 漏进产出。`ponytail:` ceiling：若未来 kernel 故意要保留某些 escape，此无条件清理会误删——届时再 gate。

**D5 — 等价证明加 fixture `RULES_WITH_POSTOPS`。** 当前 `RULES` 只 base_url + cleanup=strip_footer。新增 `RULES_WITH_POSTOPS` = `RULES` + 启用 `text_normalization:[fix_spaces]`、`url_conversion:{enabled:true}`、`youtube_cleanup:{enabled:true}`、`cleanup` 追加 `strip_empty_parens`/`fix_separators`/`normalize_internal`。HTML fixture 加几行触发这些 op 的内容（一个 `/images/` 相对图、一个 `(/wiki/x)` 内链、一个 `Load video\nYouTube\n...ContinueDismiss` 块、一个 `()` 空括号、两个相邻链接无分隔）。3 个既有 test 各加一个 `RULES_WITH_POSTOPS` 变体断言 CV3≡CV4≡kernel。

**D6 — `capability-registry.yaml` 3 处改指。** `strip_empty_parens`/`fix_separators`/`normalize_internal` 的 `implemented_in` 从 `scripts/explore/sample_converter.py` 改为 `scripts/lib/extraction/converter.py`。doctor `--check capabilities` 应继续过。

## Risks / Migration

**风险**：
- *中。* CV4 行为变更是真实质量影响：4 站策略的 pipeline 产出 Markdown 会变。缓解：每个配置分歧 key 的站点跑 `python3 scripts/test_runner.py site-samples --domain <domain>` 确认无破坏性回归。若某站回归失败，说明该 post-op 在 pipeline 语义下有害——回到 design 评估是否 gate（但预期都是修复性改善）。
- post-op 抽取是纯文本移动，CV3 侧回归面极小（同函数、同变换序）。
- 等价证明新 fixture 若发现 CV3≠CV4，说明抽取有 bug——TDD 先写 fixture（RED：CV4 当前不跑 post-op，所以 CV3≠CV4）→ 实现（GREEN）。

**迁移**：无外部调用方感知。`_apply_extraction` 签名不变；`convert_page_full` 签名不变（只内部多一步）；CV4 多调一个公开函数。

**C10 全局同步**：不触发（不触碰 tracked files）。

**预存结构缺陷（归档时顺带修）**：`openspec/specs/convert/spec.md` 与 fetch spec 同病——用 change-only `## ADDED Requirements` 头 + 缺 `## Purpose`。`openspec archive` 会拒绝。归档前改为 `## Requirements` + 补 Purpose（与 fix-crawl-scrapling-bare-call-bug 对 fetch 的修复同模式；convert spec 的 Purpose 已在其 Capability 对齐段有素材，提炼一句即可）。

**验证锚点**：`node`/`python3 -m unittest tests/test_convert_equivalence.py`（含新 fixture）；`python3 -m unittest tests/lib/`（post-op 单测）；逐站 `site-samples` 回归；`chrome-agent doctor --check capabilities`。
