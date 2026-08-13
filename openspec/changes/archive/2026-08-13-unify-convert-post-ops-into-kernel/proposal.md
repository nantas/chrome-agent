# Proposal

## 问题定义

`convert` 能力的旗舰契约——CV3（explore）与 CV4（pipeline）镜像对相同 HTML 产出等价 Markdown——存在一个**结构性的盲区**：CV3 在 `sample_converter._apply_extraction` 调用内核 `convert_page_full` 后，额外跑一段 **markdown 层 post-op** 变换（由策略 `text_normalization`/`url_conversion`/`youtube_cleanup` + 3 个 `cleanup` ops 驱动 + 无条件的 escape-artifact 清理）；CV4（`_process_html_page`）**完全不跑这段**。结果是：任何配置了这些 key 的策略，explore 采样产出与 pipeline 生产产出**系统性分歧**。

三个并发症状：

1. **等价证明自废武功**：`tests/test_convert_equivalence.py` 的 fixture 刻意省略所有分歧 key（docstring 自承 post-op「all inert under the minimal ruleset」）。证明永远绿，但绑不住真实策略的 CV3↔CV4 等价。
2. **虚假的 proxy 注释**：`convert.py:165` 声称「explore samples then serve as a valid quality proxy for pipeline production output」——本分歧直接证伪这句话。
3. **registry 固化错误归属**：`capability-registry.yaml` 把 `strip_empty_parens`/`fix_separators`/`normalize_internal` 三个 cleanup_ops 的 `implemented_in` 指向 `sample_converter.py`（explore 路径，markdown 层），与其余 8 个指向 `preprocessor.py`（HTML 层）的 cleanup 形成两层分裂——同一个「cleanup」概念跨 A 轴两层、只对一条 B 轴路径可达。

**根因（架构层）**：违反 `00-target-architecture.md` 不变量 I2「mirror 不包含转换逻辑，只做编排」。CV3 的 post-op 是实打实的 markdown 变换逻辑，栖居在 mirror 内——ADR 自己的治理机制没被遵守。同时 `explore-scaffold.md::apply-extraction-uses-shared-lib` 声明 `_apply_extraction` 是 **4 步管线**，这段 post-op 是未声明的第 5 步（spec 与代码双重漂移）。

## 范围边界

**In scope**：
- 把 CV3 `_apply_extraction` 的 post-op 块抽成 kernel 公开函数 `apply_post_conversion_ops(md, extraction_rules) -> str`，落在 `scripts/lib/extraction/converter.py`
- `convert_page_full` 在现有 4 步后调用它作为第 5 步（CV3 经 convert_page_full 自动获得，行为不变）
- CV4 `_process_html_page` 在 `convert_body` 后调用 `apply_post_conversion_ops`（**修复点**：pipeline 此前跳过，现在 honoring 相同 key）
- CV3 `_apply_extraction` 删除内联 post-op 块（现在只是 `convert_page_full` 的薄壳），回归 explore spec 声明的 4 步语义
- 订正 `convert.py:165` 注释（本 change 后该 proxy 声称变为真）
- 强化等价证明：新增第二个 fixture `RULES_WITH_POSTOPS`（启用分歧 key），断言 CV3≡CV4≡kernel——让契约对真实策略自洽
- `capability-registry.yaml` 3 个 cleanup_ops 的 `implemented_in` 改指 `converter.py`
- `convert-kernel-three-layer-interface` spec 声明第 4 个公开入口 `apply_post_conversion_ops`

**Out of scope**：
- CV4 改为通过 `convert_page_full` 路由——**不做**。three-layer interface spec 刻意让 CV4 直接用 `HtmlToMarkdownConverter` class（link-index 状态需求）；本 change 尊重该决策，post-op 经独立函数被两条路径各自调用
- escape-artifact 无条件清理的语义改变——保留为无条件（当前是 no-op sentinel；统一后两条路径都跑，sentinel 的「分歧检测」职责被 byte-equality 证明吸收，design.md 记录）
- 新增 markdown 变换能力（post-op 清单不变，只搬家）
- `00-target-architecture.md` §3.1 CV3 行的维度坐标重写（仅订正 post-op 归属措辞）

**不变性**：CV3（explore）产出 Markdown 字节级不变（post-op 从 _apply_extraction 内联移入 convert_page_full，同一组变换、同一调用点）。CV4（pipeline）产出对**未配置**分歧 key 的策略字节级不变（post-op 是 config-gated no-op）；对**配置了**的 4 策略产出会变化（预期质量修复）。

## Capabilities

### New Capabilities

_(无)_

### Modified Capabilities

- `convert`: 既有 `convert-kernel-three-layer-interface` requirement 增加第 4 个公开入口 `apply_post_conversion_ops`（markdown 层 post-conversion 变换的唯一实现）；`convert_page_full` 增加 post-op 步骤；强化等价证明覆盖分歧 key fixture

## Capabilities 待确认项

- [x] 能力清单已与用户确认（仅 Modified `convert`；用户指令「继续执行 new#1」，New #1 = CV3 post-op 分歧，归属 convert 能力，kernel 落点 lib/extraction/converter.py）

## Impact

- **代码**：`scripts/lib/extraction/converter.py`（+1 公开函数 `apply_post_conversion_ops`、`convert_page_full` +1 调用）、`scripts/explore/sample_converter.py`（`_apply_extraction` 删除 ~50 行内联 post-op 块）、`scripts/pipeline/pipeline/phases/convert.py`（`_process_html_page` +1 调用 + 注释订正）、`configs/capability-registry.yaml`（3 处 `implemented_in` 改指）
- **测试**：`tests/test_convert_equivalence.py`（+1 fixture `RULES_WITH_POSTOPS` + 3 个断言 CV3≡CV4≡kernel）；可能新增 `tests/lib/test_post_conversion_ops.py`（post-op 函数的单元测试，覆盖每个 config key 的 on/off）
- **行为变更（重要）**：CV4 pipeline 产出对 4 站配置分歧 key 的站点策略会变化——经 `python3 scripts/test_runner.py site-samples --domain <domain>` 逐站回归确认无破坏性回归
- **规范**：`openspec/specs/convert/spec.md` delta（MODIFIED `convert-kernel-three-layer-interface`）；`openspec/specs/explore/explore-scaffold.md`（`apply-extraction-uses-shared-lib` post-op 不再在 _apply_extraction）
- **C10 全局同步**：不触发（不触碰 tracked files）
- **风险**：中等。CV4 行为变更需 site-samples 把关；post-op 抽取是纯文本移动，回归面小

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`00-target-architecture.md` §3.1 + 不变量 I2、§4.3、`05-converter-architecture.md`、`convert-kernel-three-layer-interface` requirement
  - 项目页：架构再审查报告 New #1、`sample_converter.py:140-205`、`convert.py:163-184`、`test_convert_equivalence.py`
  - 回写目标：`convert/spec.md` + `explore-scaffold.md` + `capability-registry.yaml` + `00-target-architecture.md` §3.1（C10 不触发）
