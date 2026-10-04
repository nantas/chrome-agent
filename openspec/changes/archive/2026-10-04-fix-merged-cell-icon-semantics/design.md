# Design

## Context

行为依据：`specs/table-grid-parser/spec.md` 和 `specs/strategy-schema/spec.md`。

当前 `_build_table_grid` 首槽使用完整 cell 内容，延续槽克隆 HTML 后对 img 调用 decompose，再交给 `_render_cell_content`。因此源 `or <img> or <img>` 的副本变为 `or or`。源 Crypt Keeper colspan=2，现有 S5 报 `Introduced repeated text: or or`；这不是可通过白名单消除的误报。

前置实现分别来自 fix-wiki-table-sample-integrity（资产不重复）及 fix-conversion-structure-and-audit-fidelity（来源审计/批量入口）。实施与归档时检查 active/archive 状态，不假设永久规范已经回填。

## Goals / Non-Goals

**Goals:** 所有 HTML 共享路径中保留延续格图标语义、图片次数、链接及网格；通过精确配置表达 DD2 标签；用独立源断言验证效果。

**Non-Goals:** 重写表格模型、HTML 表格回退、通用图片命名、放宽 S5、修复锚点、自动发布采集结果。

## Decisions

1. 在现有延续格克隆路径替换 img 为纯文本节点，然后复用 cell/inline 渲染与转义。原节点与首槽不可变；不以 Markdown 正则替换图片。保留既有过滤语义，不能将已排除图片复活。统一 colspan/rowspan 延续内容，不按域名分支。
2. 名称解析顺序及可靠性规则严格按 table-grid-parser delta。匹配只对 alt trim，配置 key 不允许边缘空白；精确映射优先，避免文件名启发式误解状态。值中的 Markdown 字符作为普通文本转义。链接内已有相同标签时不重复添加；只有图标的链接使用替代名称继续保留目标。
3. 配置放在已有 `table_options.merged_cell_icon_labels`，不新增独立转换器或 preprocessor cleanup。DD2 至少声明 Vulnerable、Daze 两项原始文件名 alt；全量审查其他命中时必须有来源证据才增加映射。schema 和 capability registry 的配置消费声明同步，frontmatter 优先。
4. 沿用 S5 来源敏感审计，不增加 Crypt Keeper/or 白名单、不扩大重复词容忍。真正新引入重复词的反例必须继续失败。若全量发现其他投影归因问题，逐项报告，不用 renderer 输出充当 source oracle。
5. 增加 converter contract revision（实施时基于当前最大值递增，不硬编码假设仍为 7），证明旧 fingerprint 缓存被拒绝、相同新输入可复用；该变更无配置也影响含可靠 alt 的合并格。
6. 测试通过公开转换入口进行 vertical slice：配置校验 → colspan 真实问题 → rowspan/链接/过滤边界 → 镜像与缓存。fixture 自包含，不依赖 outputs 或网络。
7. 209 页原始缓存离线重放到独立目录。图片 multiset、网格行列/数值/顺序、标题、链接目标独立比较；文本差异只允许位于源合并格投影的图标位置。不能要求旧错误副本字节不变，也不能只看总图片数。Crypt Keeper S5 应通过，其余新增 fail 逐页分析；缺缓存/缺映射和其他既有 skip 如实报告。

## Risks / Migration

- 全局默认行为改变其他站点的合并格副本；使用 generic fixture、镜像测试及站点样本控制影响。未知名称占位说明信息不足，不宣称已恢复准确语义。
- 图标附近已有同名文字可能造成双标签；消除同一链接内或同一单元格紧邻节点中明确相同的可见标签，不删除独立源文字，不跨节点全局去重。
- 新标签可能包含 `|`、括号、HTML 字符；必须按文本渲染，避免配置注入结构。
- golden 必须先逐格审查预期差异再更新；正式 collection 保持原文件，实施只提供可审核的离线新产物。
- 归档顺序为先同步 fix-wiki-table-sample-integrity 的原 requirement，再同步本修改；前置审计 change 先于本 change 回填。若前置规范已更新，重读最新 block 合并，不能覆盖无关场景。
- verification/writeback 在实施后按真实结果创建，不预写通过结论。回写需读取 binding 的外部标准，仅执行已声明的本地目标。

## 实施期调整（用户已确认）

首次 209 页重放暴露 17 页新增同名重复。用户确认扩展精确邻接去重：不跨内容/换行/块，不合并不同链接目的；纯文本标签移入图标原链接以保留格式和目的，同目标文字链接可承接名称。所有匹配在替换前规划，避免将刚生成的名称误判为原始标签。关联 scenario: adjacent-exact-label；任务 2.5/2.6；原失败证据 outputs/debug-merged-cell-icons/initial-replay-failures.json。
