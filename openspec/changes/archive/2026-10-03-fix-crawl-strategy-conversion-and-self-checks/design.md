# Design

## Context

行为输入为 `specs/convert/spec.md`、`specs/fetch-strategy-selector/spec.md`、`specs/explore-workflow/spec.md`。

现有 sitemap extraction 与普通 crawl 都调用 CLI 的 convertTraversalToMarkdown；cache --phase convert 另有循环。前者把策略转为引擎参数，CloakBrowser 参数为空，其后本地 Scrapling 全页转换；get 虽传 -s，仍使用另一转换器。prefetched 分支失败还会进入 JS htmlToMarkdown。现有结构断言只证明 helper 被调用，不能证明真实产出等价。

Explore main/iterate 均把原始整页 HTML 交给 run_checks，仅传 image skip patterns。S1 数全页、S9 只扫词表、S5 只扫 Markdown。当前共享内核表格修复已通过 13 个站点样本；本 change 复用该内核，不复制算法。

## Goals / Non-Goals

**Goals:** 实现三份 delta 中的跨引擎转换一致性、明确失败、来源感知自检和真实边界回归；同一个 change 交付 P-1～P-4。

**Non-Goals:** 不调整发现/确认 Gate、采集范围或引擎优先级；不自动抓取、不修改 wiki 笔误；独立 fetch/scrape 保持旧契约；不重构全部 CLI，不引入新的站点转换器。

## Decisions

### 1. 在 crawl 层统一转换，而非给引擎补更多 flags

对应 convert 的 crawl-strategy-html-shared-conversion。

新增轻量应用层 bridge（建议 scripts/lib/crawl_conversion.py）和 Node 适配入口；bridge 只校验/编排并调用 convert_page_full，不含转换逻辑。Node 经 resolveAppPython 运行模块，使用 JSON stdin 传 html_path、output_path 和 extraction；当前 crawl 沿用共享入口的无状态 rendering context，结构化输出结果；配置不能拼入 shell 或 Python 源码。HTML 使用文件避免大 payload stdout 限制。

复用调用者已经匹配/准入的 strategy.document，extraction 缺失映射为空对象，类型/字段非法返回配置错误。获取阶段只请求 HTML，先做 content admission，再交 bridge。已匹配策略不走 buildScraplingExtractionArgs 的 Markdown 分支，也不走 htmlToMarkdown。未知策略才保留通用路线。

普通/sitemap 已获取成功的 HTML 按 URL 传给转换器；parallel prefetched HTML、cache HTML 走相同入口。拒绝/失败的获取结果不得被当成空预取而意外触发重新抓取。MediaWiki API 若到达该 HTML 边界，也必须先提供 HTML 再转换，不能以 .md 扩展名掩盖 HTML 输出。既有独立 Python pipeline 路线不改编排。

选择此方案而非只修 CloakBrowser selector：实测 -s 能移除皮肤，但 Plague Doctor 表格仍达 600 列。也不从 Node 调用 explore 的 sample CLI：生产应依赖 shared library，不能反向依赖采样工作流。

### 2. 明确 core、包装与本次成功集合

对应 convert 的 equivalence-proof / fails-closed。

共享 core 返回的字节在链接相对化之前对比。crawl 的文件命名、内部链接相对化和 merge 留在外层，分别测试；不强行引入手工样本的标题/来源包装。六份 staging baseline 先按固定的已声明包装移除前四行标题/来源及末尾换行，再比较正文；正式小 fixture 直接比较 core 字节，禁止宽泛 normalize 掩盖缺失。

每页先写隔离临时产物，成功后发布；返回按 URL 记录的成功/失败列表。修正 cache 分支用 urls.slice(count) 伪造身份的行为。assembly/collect artifacts 以本次成功集合为准；失败页已有旧 md 可保留作旧证据，但不得列为本次成功或合并输入。所有分支 bridge 失败都返回明确原因；保留本次 raw HTML 诊断入口。获取 fallback 与转换失败是不同阶段，前者现有规则不受禁降级契约影响。

### 3. 自检输入增加可选、显式的来源上下文

对应 explore-workflow 的 self-check-source-context。

run_checks 保留现有 positional 参数，新增 keyword-only source context；由一个共享构造入口从 raw HTML、input_scope、current extraction 和 source_url 生成。main/iterate 在转换和每次 remediation 重试后均传当前规则；sample acquisition 结果标明 full_document 或 content_fragment，不能靠是否有 body 标签猜测。旧调用仍可运行，但来源不足的检查返回明确 skip；其他检查照常执行。

上下文保留：原始 HTML；选中正文节点；独立保留 infobox 节点；明确排除的皮肤/导航节点；声明的图片过滤和 lazyload 规则；来源证据错误。正文/infobox 用节点身份去重，保留原始文本块。full_document 声明 selector 不命中返回 scope failure；明确标记的 API fragment 直接作为内容范围。

不把 preprocess_html 的结果当唯一 oracle：它会删除 infobox、执行 cleanup；转换和审计共用同一错误清理结果会让误删一起变绿。可以复用规则解析、URL 标准化等小工具，但保留删除前来源与排除理由。不会为修复 S1 改变共享 converter 的 selector fallback 语义；审计单独报告 scope failure。

### 4. S1 比较应保留图片 multiset

对应 s1-intended-image-retention。

基于选择前来源上下文，收集正文和独立 infobox 的图片；按已有配置计算可证明的排除，解析 lazyload 实际来源，再与 Markdown 图片比较 multiset。URL 归一遵循 source_url/base_url，仅做语义等价处理，保留区分图片身份的路径/查询。解析需处理括号、转义及已有本地图像映射上下文；无法映射的证据明确报告，不擅自把同名文件视为同图。

独立反例覆盖误删正文图、等量替换图、重复图少一次、infobox 图、过滤图、lazyload 和相对图片。避免原有恒定 -11 触发 image_wrapper 自动修复。

### 5. S9 以导航来源序列归因

对应 s9-source-based-navigation-leakage。

移除通用 _NAV_KEYWORDS。上下文从正文之外的语义导航容器（nav / navigation role）和策略已有排除选择器中，保留有导航结构证据的链接/文本序列。将规范化的 label+target 与输出比较；优先保留 body 合法对应关系，只把有可区分证据的 excluded-only 序列认定为泄漏。一个 Special: 链接或一个 Items 单词不构成充分证据。存在正文/导航同值冲突且无法区分时记录证据不足，不武断 fail。

不新增 per-site 内容词黑名单，也不把所有 cleanup_selectors 排除元素自动认作导航。真实登录/注册导航 fixture 必须失败，合法 Items 列表与正文 Special 链接必须通过。没有来源上下文的旧调用返回 skip，不宣称完成来源验证。

### 6. S5 归因逐次匹配，notes 保持状态兼容

对应 s5-source-attributed-repetition / summary-and-remediation-compatibility。

将候选重复定位到 Markdown 可见文本块，屏蔽目的 URL、图片语法和代码等非正文区域；与源文保留区域的可见文本块做空白/内联格式归一后匹配。以块上下文加 occurrence budget 配对，每个源重复只抵扣对应一次。源文已有重复进入 notes，新增重复进入 anomalies。不同段落不能因归一而拼接出重复。

保留 pass/fail/skip 三种 status，不新增 note status。其他 S5 异常独立运行：来源重复 note 不能覆盖 raw tag 等真实 fail；只有重复判断缺少来源且无其他已确认错误时明确 skip。汇总继续列出 notes/跳过原因，自动修复只处理已确认且已有消费者支持的失败。

### 7. 回归与交付

正式测试放 tests/，Python unittest，Node node:test。先通过真实 crawl→bridge 的最小 fixture 建立红灯，再逐 slice 修改；引擎替身只提供原始 HTML，不模拟 Markdown 转换成功。对 main/iterate 测试真实来源构造和检查器，避免 mock 掉被修复边界。替换旧源码字符串测试中“crawl 必须调用 helper”的过时断言，保留独立 fetch/helper 的契约。

同一 fixture 覆盖 CloakBrowser/get/预取/cache，额外覆盖未匹配路线、配置错误、依赖失败和 stale artifacts。新增 bridge 模块注册为 convert mirror 并指向等价测试；更新 architecture gate/doctor 所需声明，不新增引擎或策略变体。

## Risks / Migration

- crawl 输出会改变（预期修复）。旧输出不作为新成功产物；明确提示重新转换才得到新语义，不批量删除历史文件。
- 空 extraction 的匹配策略也改走内核；增加 generic HTML fixture，明确这是匹配策略的一致性保证。
- 图片/导航归因复杂，优先保守且显式的证据不足；必须同时有误报反例和漏报正例，不能仅以 DD2 全绿宣告正确。
- S1 oracle 可能与 renderer 同错：来源上下文保留原始节点和排除原因，并用人为删除/替换输出的 mutation 反例验证可抓真实丢失。
- 历史 fetch-strategy-selector 规范强制 crawl -s；本 change 完整更新四条 requirement，归档同步其非目标说明，避免继续声称 crawl cleanup 尚未消费。
- 当前未跟踪 DD2 fixture 与 outputs 仅为诊断资料；正式回归用小型 tracked fixture，六份真实样本作为额外验收，保留其他工作区变更。
- CLI 修改执行 C10；不更改引擎版本。若实现实质改变共享内核语义，按既有 contract revision 纪律处理；仅新增 crawl 编排不无故 bump pipeline revision。
- 依赖 fix-wiki-table-sample-integrity 的当前内核行为；不改其 change 文档，归档顺序需保留已有表格规范。

### 实施核对

bridge 保持当前 crawl 的无状态内核上下文，URL/链接相对化留在 Node 外层；没有新增 pipeline state 注入。来源 URL 用于 self-check 链接/图像归一。图片在 S5 可见文本中以边界标记保留，避免删图语法后制造数值重复。

实施期间其他流程更新了站点 cleanup 和 preprocessor；没有覆盖这些改动。现场验收分别固定当前规则与 handoff 规则：前者证明当前镜像等价，后者证明旧基线等价，见 verification。
