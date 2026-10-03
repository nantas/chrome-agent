# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 核对三份 delta 的 requirement/scenario 与当前实现，记录 P-1～P-4 已归档、P-5～P-7 未提交的边界；快照现有 preprocessor/策略/注册/测试/样本，标明接纳与保留范围。
- [x] 1.2 重跑 outputs/debug-dd2-followup/minimal.py 与 probes.py，保存五项 RED 和因果对照；将最小输入转为 tests/ 自包含 fixtures，正式测试不得引用 outputs 或依赖网络。

## 2. 核心实现任务

每个 slice 内逐个新增场景 RED→GREEN，不先堆所有失败测试；完成一个可验证行为再扩展。以下路径与名称遵循 design，行为验收以三份 specs 为准。

### Slice A — DOM 安全 tooltip（convert: tooltip-normalization-preserves-dom）

- [x] 2.1 RED：真实 convert_page_full 覆盖普通/nowrap/空 span + image + heading/table、嵌套 tooltip、相同/不同目标链接和可见文本，证明当前关闭站点绕过时粘连；不只验证 HTML 标签平衡。
- [x] 2.2 GREEN：结构化解包与兼容链接合并替换全局闭标签删除，保持入口签名；Fallen Templar 不启用 nowrap workaround 也独立渲染 Skills，既有 tooltip 行为回归通过。

### Slice B — 列表包装（convert: wrapped-list-items-preserved）

- [x] 2.3 RED：真实 full conversion 验证奖励列表四图保留、四层以上包装、子有序列表编号/顺序、普通 inline 保留；分别验证无配置旧行为与配置启用行为。
- [x] 2.4 GREEN：收敛 unwrap_list_item_wrappers 为终止明确的结构遍历，不固定三轮、不提升真正子列表；同步保留操作的能力声明，Shambler 109 图及文本顺序通过。

### Slice C — 配置校验与配对标题（strategy-schema / convert / explore-workflow: s8-declared-heading-semantics）

- [x] 2.5 RED：校验 heading_normalization 缺省/空列表/有效字段/未知键/错误类型/无效 CSS，以及策略加载与 capability gate 传递；锁定非法配置显式失败。
- [x] 2.6 GREEN：接入 extraction schema、配置传递与能力注册，缺省行为兼容，禁止错误配置静默忽略；更新 DD2 frontmatter 的声明及必要 registry 镜像。
- [x] 2.7 RED：完整转换验证隐藏 h3 与可见同名邻接标签合并、错名/非邻接/未配置不处理、重复执行不重复、id/图片/链接保留；用两页精简 fixture 固定 14/3 标题语义。
- [x] 2.8 GREEN：共享预处理实现配对规范化，在一般隐藏清理前保留源层级/id 与可见内容，记录不匹配证据，不复活无关隐藏元素。
- [x] 2.9 RED：S8 从原始来源和声明规则验收层级与唯一性；仅粗体、删标题、错误层级必须失败；缺来源/歧义明确，main/iterate 对同输入一致。
- [x] 2.10 GREEN：接入 source context 的章节期望与实际 heading 对比，独立检查正常标题及配对标题，避免转换输出自证正确；两页保留章节与链接锚点定位。

### Slice D — S6 分隔行识别（explore-workflow: s6-table-data-row-classification）

- [x] 2.11 RED：逐个覆盖短横线数据、真正 delimiter、无表头、escaped pipe、嵌套表和合并表头；保留超过既有阈值的真实删行反例。
- [x] 2.12 GREEN：根据表格位置/单元格语法区分 delimiter 与数据/合成表头，保持阈值；Inn 15 条数据恢复计数，94/94 对齐，现有表格回归通过。

### Slice E — S5 标识与版本样式归因（explore-workflow: s5-source-attributed-version-anomalies）

- [x] 2.13 RED：源已有 Config2fc、转换新增粘连、源一次输出多次、代码/链接目标排除、无来源、source note 与其他真实异常并存场景。
- [x] 2.14 GREEN：可见候选按原始保留来源进行有限次数/上下文归因，notes 不触发 space normalization；真实新增异常仍 fail，重复词及其他异常逻辑独立。

### Slice F — 绕过操作收敛（convert: cleanup-workarounds-require-conversion-evidence）

- [x] 2.15 RED：针对原 P-6/P-7 声明补 full conversion 测试，覆盖空 id/name anchor、媒体与块边界；如果未产生 RED，明确记录“不成立”而非编造修复需求。
- [x] 2.16 GREEN：在根因修复后运行三项操作全部组合及已影响样本；移除 DD2 中无独立收益的配置，保留必要操作并修正语义安全性；删除实现/注册前审计全部引用，保存每项决策证据。

### Slice G — 来源感知离线批量审计（explore-workflow: source-aware-offline-batch-audit）

- [x] 2.17 RED：自包含 manifest 经真实 batch API/CLI 验证原始 source context、scope、相对路径、精确页面身份、缺输入/映射歧义、输出不得覆盖输入、禁网络、notes/skip 汇总；与 main/iterate 对照同判。
- [x] 2.18 GREEN：实现 tracked batch_audit 入口并注册，将临时全量脚本适配为调用者；提供页面映射下的本地化链接身份对照，缺证据明确表示；报告保留逐页结果及每检查覆盖率。

### Slice H — 共享入口等价（convert: structural-fix-shared-entry-proof）

- [x] 2.19 RED：扩展既有 explore/pipeline/crawl 镜像 fixture，包含上述列表、tooltip、配置标题、infobox/post-op canary；比较 core 字节并用独立结构断言检出内容丢失。
- [x] 2.20 GREEN：仅修必要编排/上下文传递使镜像通过，不复制转换实现；保留失败不降级、缓存 HTML 不重抓、失败页不进入成功产物的既有回归。

## 3. 收敛与验证准备

- [x] 3.1 对 209 页缓存建立确定的输入与配置快照，输出到独立 debug 目录；离线重放 core 及本地化产物审计，禁止网络和覆盖正式 collection，记录无法提供外部元数据的限制。
- [x] 3.2 独立检查图片 multiset、标题级别/次序、链接目的与锚点、逐表数据；报告每项 pass/fail/skip，逐页解释剩余问题，不以总体无 FAIL 代替覆盖证明。
- [x] 3.3 运行 `.venv/bin/python -m unittest discover -s tests -v`、`node --test tests/*.test.mjs`、`.venv/bin/python scripts/test_runner.py site-samples --domain darkestdungeon.wiki.gg`；golden 如有正确语义差异，先独立验证并记录审查再更新，不盲目覆盖 13 样本基线。
- [x] 3.4 验证 Python 3.9 语法、schema/registry 一致性、`node scripts/chrome-agent-cli.mjs doctor --check capabilities --format json` 与 diff 检查；若触发 C10 则同步全局副本/hash；移除代码调试探针，保留明确标记的诊断证据。

## 4. 验证与回写收敛

- [x] 4.1 基于真实结果生成 verification.md，逐条映射三份 spec/scenario 与测试证据、任务与执行结果，包含绕过消融决策和 209 页覆盖缺口。
- [x] 4.2 读取 binding 的 spec_standard_ref，基于验证结论生成 writeback.md，列出本地文档与 handoff 的字段映射、前置条件和执行范围。
- [x] 4.3 执行 binding 所列本地回写并记录时间/执行人/结果；纠正 handoff 的 markdownify/colspan 归因与提交状态，不抹除历史现场；记录三份 delta 归档清单，实际归档另行执行。
