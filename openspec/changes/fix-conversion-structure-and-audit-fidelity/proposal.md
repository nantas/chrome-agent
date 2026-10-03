# Proposal

## 问题定义

DD2 全量 209 页暴露共享转换与自检剩余缺陷。P-1～P-4 已在 `4c781e3` 修复归档，本 change 处理后续问题，不重开旧 change。

- P-7 的根因是 `merge_tooltip_links()` 删除所有 span 闭标签却只移除两类开始标签，破坏 DOM，导致普通 span 后的标题/表格粘连；现有 nowrap 解包只是绕过。
- P-5 的共享列表渲染只遍历直接 li，跳过包装列表；Shambler 关闭解包后图片由 109 降为 105。
- P-6 空 inline/空段落归因未证实：Fallen Templar 组合对照只对 nowrap 解包敏感，现有结构层测试不足以证明转换修复。
- Inn 的 S6 将 15 条只含短横线的真实数据行当分隔行，产生 94/79 行误报；不是 colspan 损失。
- Enemies 两页的 14/3 个隐藏语义标题被删，可见分组标签成为粗体，章节层级降级。
- Lair 源文已有 Battle Config2fc，S5 版本号正则误报；旧修复只覆盖重复文本来源归因。
- 临时全量脚本没有传来源上下文，报告 S9 209 页全 skip、S5 44 页 skip，不代表验证全通过。

诊断入口：`outputs/debug-dd2-followup/minimal.py`（5 项确定性 RED）、`probes.py` / `probes.json`（现场单变量对照）；本地证据不是正式测试依赖。

## 范围边界

包含：DOM 安全的 tooltip 处理、配置驱动的列表包装规范化、清理绕过操作的消融验证、配置驱动的隐藏/可见标题配对规范化、S6 表格行识别、S5 版本样式异常来源归因，以及可重复的来源感知全量离线审计。

排除：重新抓取、网络验证、发布正式产物、改写源文笔误、把任意粗体当标题、恢复所有隐藏元素、以新 golden 掩盖差异、改变已匹配策略失败不得降级的契约。不能用生产转换器产出充当唯一审计 oracle。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `convert`: 修复 tooltip/list 结构保真并增加配置驱动的配对标题规范化，保留共享内核等价边界。
- `explore-workflow`: 修正 S6/S5 判定，按声明标题语义执行 S8，建立来源感知离线批量审计与覆盖率表达。
- `strategy-schema`: 定义标题配对配置、校验和安全默认值，收敛经真实转换证明的 cleanup 配置。

## Capabilities 待确认项

- [x] 能力清单按用户已确认方案映射既有 convert、explore-workflow、strategy-schema，无新增站点专用能力，无阻塞问题。

## Impact

- 共享实现：`scripts/lib/extraction/converter.py`、`preprocessor.py`、`schema.py`；自检与消费方：`scripts/explore/self_check.py`、main/iterate（按需要）。
- 配置：DD2 strategy frontmatter 与对应 registry 镜像、`configs/capability-registry.yaml`；保留无关 registry 改动。
- 测试：`tests/` 的 unittest/node:test，自包含 fixtures；DD2 缓存 209 页作附加离线重放，13 个站点样本必须通过或对明确语义修复提供人工可审查差异。
- 离线审计：把可复用检查边界落实到 tracked 代码和测试；本地全量脚本只负责调用，不继续作为唯一不可复现的质量入口。
- 文档和规范按 binding 回写；实现/验证证据在后续阶段生成，不提前宣称通过。

## 关联绑定

- 关联 binding: `binding.md`。
- 标准页：binding 的 `spec_standard_ref`；项目页/回写目标采用 binding 所列五份 architecture 页面、CONTEXT-MAP 与 handoff 状态追加。
