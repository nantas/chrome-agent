# Design

## Context

行为依据为 `specs/convert/spec.md`、`specs/explore-workflow/spec.md`、`specs/strategy-schema/spec.md`。本地诊断已通过真实 convert_page_full 和 self_check 重放，最小 RED 与单变量证据保存在 `outputs/debug-dd2-followup/`。实现必须把最小 fixture 移入 tests，不能依赖该目录。

现有共享内核是 selectolax HtmlToMarkdownConverter；preprocess_html 使用 BeautifulSoup。旧 handoff 中 markdownify 和 colspan 的归因不符合当前执行路径，应在后续状态回写中纠正。上一 change 已完成 crawl 共享桥接与 S1/S5重复/S9 来源契约；本 change 保持其失败不降级及 mirror 等价要求。

## Goals / Non-Goals

**Goals:** DOM/列表保真、明确的章节语义、自检能区分来源内容与转换缺陷、全量审计结果可解释可重复。

**Non-Goals:** 不迁移解析库、不引入第三方测试框架、不网络采集、不复制完整 DD2 collection converter 成新内核、不任意改写源文、不将所有隐藏文本或粗体提升为标题。

## Decisions

### 1. 在共享 tooltip 入口修复 DOM，而非依赖站点 unwrap

对应 convert / tooltip-normalization-preserves-dom。保留 `merge_tooltip_links` 入口兼容性，以结构操作精确解包 tooltip 和 icon-size 容器；禁止全局删闭标签。链接合并只处理相邻、同目标且图标/文本角色明确的节点；不能吞掉其他链接或文本。

用真实 full conversion 锁定普通 span+img+h2+table 的失败，而不是只断言输出 HTML 标签平衡。对 Fallen Templar 关闭四个新增 cleanup 后重放，确保共享修复仍保留 Skills。开启合法 tooltip 合并用例证明没有通过直接禁用该功能来“修复”。

### 2. 将列表清理作为受配置控制的结构规范化

对应 convert / wrapped-list-items-preserved。接纳当前 unwrap_list_item_wrappers 的已证实行为，但以有界节点集合/结构严格减少的迭代替代固定三轮。仅处理直接阻挡 li 的表现性包装链；遇到真正嵌套 ul/ol 保留层级，不把任意后代 li 提到父列表。

现有未提交实现/14 项测试先保留快照，逐项调整；真实转换测试补足图片、文本、顺序与编号断言。此配置继续由站点声明，不扩张为所有容器的通用展平。

### 3. 显式配置标题配对，不依赖“看起来像标题”

对应 convert / configured-semantic-heading-pairs、strategy-schema 两条 requirements，以及 explore-workflow / s8-declared-heading-semantics。

新增字段：

```yaml
extraction:
  heading_normalization:
    - heading_selector: "h3:has(.mw-headline > div[style*='display:none'])"
      label_selector: ".headerdd2"
```

示例用于说明字段，最终 DD2 selector 在真实两页 fixture 上验证后收敛。CSS 由共享 BeautifulSoup 选择器边界验证和消费，不要求 selectolax 支持相同扩展语法。校验失败显式报配置错误。

配对条件：同父节点、下一元素兄弟（忽略空白/注释）、非空规范化标签相等或通过明确的 label_aliases 源名称→可见名称映射、源节点确为 h1–h6。执行位置在普通隐藏清理之前、原始 content scope 内：把可见标签内容移入源 heading，保留源 id 与层级、可见图像/链接，移除重复展示标签。没有配对则不改变 DOM，记录不匹配原因。不要复活一般 display:none 内容。

配对判定做成无渲染副作用的小函数，转换与审计可共享规则解释；审计仍从原始 HTML 生成 expected heading 记录，不读取转换后的 Markdown/cleaned DOM 作唯一期望。测试必须有独立常量期望与删标题反例，防止共享判定同时出错而全绿。

### 4. S6 解析表格结构，保留短横线数据行

对应 explore-workflow / s6-table-data-row-classification。先识别 Markdown 表格块及 delimiter 位置，再区分 header/body；按单元格语法识别实际 delimiter，处理 escaped pipe。空合成表头单独处理，不能靠“整行只有空格、冒号、短横线和竖线”筛掉所有行。

保留当前来源结构计数/10% 阈值；不重新写渲染器做 oracle，也不将此次 Inn 问题误修成 colspan 调整。实际 Inn 的 15 条 `|  | - |  |` 均为数据。用超过阈值的删行反例证明检查仍有检错能力；同时保持嵌套表、合并表头和现有转置相关回归。

### 5. S5 将版本样式候选纳入来源归因

对应 explore-workflow / s5-source-attributed-version-anomalies。复用可见文本提取边界，避免对图片/链接目的地址、代码做版本空格判断。候选与原始保留文本按上下文/出现次数比较，源已有 Config2fc 给 note；新增粘连仍 fail。复用“源一次不豁免无限输出次数”的原则，保持重复词、raw tag、escape 等独立结果。

不在检查器中自动修改源标识，也不因某个 note 丢掉其他 anomaly。若现有自动修复没有安全的对应转换操作，保留失败与证据而不生成不实修复动作。

### 6. 用 tracked 批量审计入口替代一次性脚本的隐式契约

对应 explore-workflow / source-aware-offline-batch-audit。计划新增 `scripts/explore/batch_audit.py`，通过 `python -m scripts.explore.batch_audit --manifest ... --output ...` 离线调用。输入 JSON 包含 extraction 快照、页面稳定 ID/title、source_url、html_path、markdown_path、input_scope，以及可选 page/link mapping。文件路径相对 manifest 所在目录解析；逐页记录缺文件/缺 scope；输出只写显式报告路径，拒绝与输入路径冲突。

每页调用与 main/iterate 同一检查边界并显式 build_source_context；S6/S8 也使用原始来源及意图保留范围。面向最终本地化 Markdown 时，需用映射把目标链接还原为可比较的来源身份；无映射的歧义如实记录。Core 审计和外层链接/标题包装审计分开记录，不能靠无差别剥离内容得到等价结论。

不复制 `outputs/dd2-scope-discovery/convert_dd2_collection.py` 的 LinkedConverter、链接生成或文件组装。该脚本只适配为提供输入/调用审计入口的现场工具；正式回归调用 tracked API/CLI。新模块按 capability registry 的既有结构注册，不能为凑注册新增业务能力。

### 7. 根因修复后评估绕过操作

对应 convert / cleanup-workarounds-require-conversion-evidence。对 strip_empty_inline_tags、strip_empty_paragraphs、unwrap_nowrap_spans 跑全部组合及实际影响样本，记录独立收益。没有收益则撤出 DD2 配置；是否移除实现/注册先查所有引用，不能伤及其他策略。空 id/name anchor 属有效语义，不是噪音；保留测试必须走 full conversion，不能只验证 soup 中标签消失。

## Risks / Migration

- DOM 序列化可能改变空白或 tooltip 文字间隔：使用内容 canary、旧有链接合并测试和各镜像字节等价检查，所有差异按来源解释。
- 站点隐藏标题可能不邻接或名称不同：安全默认不配对并记录，不扩大 selector 硬凑 14/3。
- 标题恢复改变锚点：检查本页与集内引用定位，保留源标识映射；不能只检查链接数量。
- 209 页可能暴露新真实异常：逐页分类 fail/skip，不要求通过放宽规则凑 209 页全绿。网络调用全部禁用；含视频的转换重放使用缓存或固定外部元数据边界并披露限制。
- 现有 13 个样本可能产生正确结构差异：先保留旧基线、独立核对图片/链接/表格/标题，再提供可审查差异；禁止整批盲目接受 golden。
- C9：修改共享库同时补 tests，Python unittest / Node node:test，vertical slice RED→GREEN；Python 3.9 兼容。C11：配置/schema/能力同步与 doctor；C10 仅当实际修改触发文件时执行。
- 实施前核对工作区所有权，保留与本 change 无关的注册表格式化、采集产物与其他 active changes；本提案不提交或改写这些文件。

### 实施确认（2026-10-03）

用户明确批准为 Cultist (Cosmic)→Cultist、Lost Battalion→The Lost Battalion、Plague Eaters→Plague Eaters (Gentry)、Shambler (Cosmic)→Shambler 配置精确 label_aliases。保留可见名称和图像/链接，沿用隐藏 heading 的层级与原始 ID；不采用模糊匹配。S8 期望使用对应可见名称。
