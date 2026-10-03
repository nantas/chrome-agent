# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 核对三份 delta 与 design 的调用点矩阵：普通/sitemap/预取/cache；检查当前表格内核与已有未提交变更，保留其他 change、策略和样本。
- [x] 1.2 将诊断最小 HTML 转为 tests/ 内自包含 fixture；确定正式测试入口，真实 DD2 输入仅用于附加重放，测试不得依赖 outputs 或全局引擎安装。

## 2. 核心实现任务

每个 slice 内完成 RED 后立即 GREEN，再进入下一 slice；每个新增场景也依此循环，不集中编写全部红灯测试。

### Slice A — crawl 到共享内核（convert: crawl-strategy-html-shared-conversion）

- [x] 2.1 RED：真实 convertTraversalToMarkdown 编排配合仅替换获取边界的 fixture，证明 CloakBrowser skin、selector-only 嵌套表格/cleanup 产出不等价；保留 infobox/post-op canary，记录失败输出。
- [x] 2.2 GREEN：新增结构化应用层 bridge，经 resolveAppPython 调用 convert_page_full；接入最小 crawl 路径，使 core 字节等价测试通过，校验规则和空 extraction 行为。新增模块同步能力注册与等价测试指针。

### Slice B — 全入口接入（convert / fetch-strategy-selector）

- [x] 2.3 RED：逐个补普通遍历、sitemap、prefetched/parallel、cache --phase convert 的实际编排测试，断言已获取 HTML 不重抓、shared core 等价；补未匹配路线与独立 fetch 兼容反例。
- [x] 2.4 GREEN：全部匹配策略入口接入同一转换边界，传递 URL/规则/context；更新过时的 crawl helper 源码字符串断言，保留 fetch/helper 的 selector 与注入安全测试。

### Slice C — 失败与产物身份（convert: crawl-strategy-conversion-fails-closed）

- [x] 2.5 RED：逐个覆盖非法配置、bridge/依赖失败、预取失败、旧 Markdown、A/C 成功 B 失败，断言无通用降级且本次 artifacts/merge 不含失败页。
- [x] 2.6 GREEN：隔离临时产物、明确错误/证据与 URL 成功集合；修复 cache 计数切片身份错配；仅发布和合并本次成功页，使上述失败测试通过。

### Slice D — 来源上下文与 S1（explore-workflow: source-context / intended-image-retention）

- [x] 2.7 RED：全页皮肤图误报、API fragment 无 wrapper、正文 selector 不命中各建来源 fixture；增加正文/独立 infobox 丢图、同数换图、重复图缺一次、过滤和 lazyload 反例。
- [x] 2.8 GREEN：实现保存 raw 证据的来源上下文及 image multiset 审计，新增 keyword-only context 保持旧调用可运行；配置排除不以清理后输出充当唯一 oracle，使 S1 正反例通过。

### Slice E — S9 导航归因（explore-workflow: source-based-navigation-leakage）

- [x] 2.9 RED：合法三行 Items、真实 skin 登录/注册泄漏、正文合法 Special 链接、body/nav 同值冲突和缺来源场景，逐一验证当前误报/漏报。
- [x] 2.10 GREEN：移除通用内容词判定，以导航来源序列和正文对应关系归因；缺证据明确 skip，使合法内容通过且真实导航 fixture 失败。

### Slice F — S5 来源笔误（explore-workflow: source-attributed-repetition）

- [x] 2.11 RED：源文 of of / over over、转换新增重复、源一处输出两处、跨内联格式/空白、不同块边界及 source note 与 raw-tag 异常并存场景。
- [x] 2.12 GREEN：实现可见文本候选与逐次来源匹配，notes 独立于既有 anomalies；没有来源时显式表达不确定性，保持真实错误 fail。

### Slice G — main/iterate 与汇总（explore-workflow: summary-and-remediation-compatibility）

- [x] 2.13 RED：真实 self_check/context 接入 main 与 iterate 测试，验证当前规则更新后重建上下文、两入口同判、notes/skip 不触发错误 KI/自动修复、独立失败仍进入现有处理。
- [x] 2.14 GREEN：样本结果携带输入 scope/source_url，main/iterate 传当前上下文，汇总保留 notes 和来源缺口；保持 pass/fail/skip 协议并通过所有调用者回归。

## 3. 收敛与验证准备

- [x] 3.1 运行上述 Node/Python 定向测试、既有 fetch/内容准入/crawl 等价与 Explore 测试，再运行 `.venv/bin/python -m unittest discover -s tests -v` 和相关完整 Node suite；记录命令、结果及 spec 场景映射。
- [x] 3.2 重放六份真实 DD2 HTML：crawl core 对比共享内核和声明包装后的 staging baseline；检查章节、图片 multiset、链接、表格，验证 S1/S9/S5 修复结果；不得把单纯全绿当作反例覆盖的替代。
- [x] 3.3 执行 `.venv/bin/python scripts/test_runner.py site-samples --domain darkestdungeon.wiki.gg`，确认 13 样本通过；不更新 golden 来掩盖差异。
- [x] 3.4 执行能力 doctor 检查与 C10 全局同步，核对 installed-hash/current HEAD；清理临时调试日志，保留明确标记的诊断证据，检查 Python 3.9/ESM/函数声明约束。

## 4. 验证与回写收敛

- [x] 4.1 基于实际实现生成 verification.md：spec-to-implementation、task-to-evidence、原始复现和反例结果；说明依赖的既有表格 change，不提前声称已修复。
- [x] 4.2 读取 binding 的 spec_standard_ref，生成 writeback.md，列出项目页面摘要/测试命令/镜像关系更新和准确路径。
- [x] 4.3 完成 binding 所列回写，记录执行人/时间/结果；记录归档合并清单：三份 delta 及旧 fetch-strategy-selector 中与 crawl 新契约冲突的非目标说明；保留 fetch 范围。实际归档另行执行。
