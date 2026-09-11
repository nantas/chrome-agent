# Design

## Context

实现以本 change 的八份 delta specs 为准。现有代码已经恢复 explore 页面发现与确认门；缺陷集中在生产转换、缓存与恢复边界。

| 证据 | 当前行为 | 对应规范 |
|---|---|---|
| `phases/convert.py` 的 `_process_html_page` | preprocess 删除容器，未 extract/prepend | [convert](specs/convert/spec.md)、[extract-kernel](specs/extract-kernel/spec.md) |
| `phases/fetch.py` 标题集合 fastpath | 不检查 acquisition 与必要 payload | [fetch-phase-cache-fastpath](specs/fetch-phase-cache-fastpath/spec.md) |
| `cache.py` 标题替换及反解 | 分隔符碰撞，原始标题不可恢复 | [mediawiki-cache-integrity](specs/mediawiki-cache-integrity/spec.md) |
| `phases/convert.py` resume 与 mismatch warning | 旧文件可跳过；旧模式只警告 | [pipeline-convert-phase](specs/pipeline-convert-phase/spec.md) |
| `wikitext_to_md.py` 搜索起点 | 文首守卫修挂死，仍跳过文首第一表 | [pipeline-converters](specs/pipeline-converters/spec.md) |
| CLI `timeout: 600_000`、freeze `indent=2` | 大站超时、全文件重排版 | [cli](specs/cli/spec.md)、[strategy](specs/strategy/spec.md) |

诊断基线：26 项 Python 和 9 项 Node 现有测试通过，但合成 infobox 对照失败；现有等价 fixture 没启用 infobox。当前 Apple 缓存没有 HTML，报告中的字节数不是本轮可重现证据。LSP 工具及关联 skill 在本会话不可用，规划使用已核实调用链及定向源码读取。

## Goals / Non-Goals

**Goals:**

- 共享全页转换在删除 infobox 前保存字段，生产链接与共享后处理不退化。
- 身份错误或内容模式不匹配的缓存不能进入 fetch skip、convert dispatch 或 resume success。
- 缓存命名安全且兼容旧数据；表格扫描有明确前进不变式。
- 大站可以显式延长子进程时间；freeze 不制造无关 diff。

**Non-Goals:**

- 不做 D1–D7 二次重构，不改变 manifest 准入、页面分类或确认门。
- 不改输出 Markdown 文件名规则、不批量迁移历史缓存/产物、不在本 change 中执行 my-wiki ingest。
- 不增加第三方依赖、不写全新 wikitext 解析器，不用站点特判修通用转换。

## Decisions

### 1. 扩展共享全页入口，CV4 注入状态

建议兼容接口为 `convert_page_full(html, extraction_rules, *, converter=None, source_dir="")`。类型遵循 Python 3.9；不新增执行路径 context 开关。

CV4 构建现有 `HtmlToMarkdownConverter`，保留 manifest link index 和 redirect map，再把它交给共享入口。共享入口执行 extract → preprocess → body → prepend → post-ops；CV4 只添加 frontmatter、标题、图片元数据和 card stats。card stats 继续读取原始 HTML。

共享入口统一决定 URL 上下文：配置 `image_handling.base_url` 的主机优先，其次注入 converter 的域，最后空字符串。无状态两参调用保持既有行为；注入 converter 的规则必须与调用规则等价。使用标准 URL 解析，覆盖带尾斜杠 base URL。

`extract_infobox` 已有 inline renderer、handler 和 `source_dir` 参数，但当前字符串/BS4 分支没有消费全部上下文。实施时在共享提取层接通这些参数，复用 converter 的链接渲染，不在 CV4 拼字符串补链接；用带跨目录链接的 portable infobox 和既有 table infobox fixture 证明行为。保持已注册字段 handler 与无 infobox 情形。实施补充：提取/删除共同遵守 enabled；默认 selector 统一为 aside.portable-infobox，禁用时仅走正文转换，避免旧内核无条件 prepend 的重复字段。

拒绝仅在 CV4 复制 extract/prepend：它能局部修复，但继续保留两个编排源。也不直接丢弃 converter 改为当前两参调用，否则 link index 与相对目录会丢失。

### 2. 缓存用版本化哈希键，读旧写新

新键为 `v2-<sha256(exact-title UTF-8)>.json`，沿用 platform/domain 外层目录。它不依赖输出文件命名，不折叠空格、下划线、大小写或 Unicode。写入包含原始 title、cache schema version、resolved acquisition、source base URL 与 payload；返回前始终核对原始 title，即使发生理论哈希冲突也不能返回他页数据。

临时文件使用同目录唯一名称后 `os.replace`，避免同名 `.tmp_` 竞争。枚举通过 metadata 获取标题，不从 filename 反推。每个 run 构建一次已解析条目的索引，避免 fetch 和 convert 重复读取整站 JSON。

读取优先有效 v2；其次检查旧 space-normalized 与 separator-sanitized 候选，候选路径必须留在缓存目录。旧文件只有身份与内容准入通过才能使用；不把斜杠展开成任意目录。损坏/缺 title/标题不符返回 miss+reason。读操作不迁移、不重写；未来成功抓取才写 v2，旧文件保留。

此存储协议需要在实施时记录 ADR，说明哈希、旧读策略及输出命名边界；不借本 change 改动 `obsidian-safe-filenames` 的任务。

### 3. fetch 与 convert 共用缓存准入

在 cache 模块提供单一 admission API，返回可用 entry 或具名拒绝原因，并携带 expected/actual mode、缺失字段等诊断。以 `_STRATEGY_REGISTRY` / `build_pipeline` 解析的 effective acquisition 为准，不从缺省 frontmatter 写入 `unknown`。

| 请求模式 | 可用 payload |
|---|---|
| html_rendered | 非空 html；hybrid 的空 rendered_html 不算 |
| wikitext_only | string wikitext；空页不误判损坏 |
| hybrid_wikitext_plus_rendered | wikitext；按现有 acquisition 的动态内容判定，确实需要 rendered fallback 时还需非空 rendered_html |

动态内容判定应由 acquisition 暴露/复用同一策略逻辑，禁止在 cache 复制正则。HTML 抓取退回 wikitext 的结果不满足 HTML 请求；新获取内容也必须通过准入后才能统计 fetched 成功，避免新抓到无效内容却标绿。

明确 marker 不匹配则拒绝，即便另一字段碰巧存在；markerless legacy 只接受表示无歧义的 payload，并在内存适配。来源 endpoint 有记录时核对；无记录的 legacy 以明确 platform/domain 目录范围兼容，不声称验证了缺失的来源。

fetch 保留“全兼容不建线程池、部分兼容仅调度缺口”的优化；去掉旧 spec 对任意数据规模固定小于一秒的要求。convert 阶段不隐式抓取，不按旧 acquisition 偷换路线，拒绝结果进入当前失败统计。

### 4. resume 使用转换指纹，先准入后跳过

在 `.pipeline_state.json` 增加每页 conversion fingerprint。保留旧 completed_pages 读取，但缺 fingerprint 只作为历史提示。指纹采用稳定序列化后哈希，包含：原始转换 payload 摘要（不含 fetched_at）、resolved content profile、extraction/output 语义配置、page target、manifest link-index 与 redirect-map 摘要、显式 converter contract revision。

全局配置和 link-index 摘要每 run 算一次；每页只组合本页 payload 与 target。首次引入 revision 将所有旧无指纹完成状态视为需要重新转换，确保已丢 infobox 的历史文件不会直接跳过。

只有输出成功落盘后才持久化 fingerprint/completed；中断导致有文件无状态时安全重做。缓存准入或转换失败时撤销当前完成资格，不删除用户旧文件，但 extraction results/assembly 不能把它当作本次成功。编排层必须保留 convert 写入的指纹，不得在最终 state flush 中覆盖掉指纹或并回旧完成集合。Fetch 将失败 title 传入 convert（包括强制重抓旧兼容缓存失败），fetch-only 返回非零；显式 fetch+convert 组合不提前退出。验收覆盖同输出目录、旧完成状态和失败重抓的整条路径。手册推荐新输出目录，避免旧物理文件混入人工交付。

### 5. wikitable 扫描修复保持有限

在首次扫描时先判断 offset 0 的 `{|`，否则寻找下一个换行后 `{|`；消费后把 cursor 移到对应闭合标记之后。保留现有嵌套深度处理；未闭合输入终止并保留余文，绝不回到已消费的起点。

先用有超时的独立子进程锁住原挂死模式，再覆盖文首多表、文中表、尾文及未闭合输入。现有工作区的 `i == 0` 守卫保留其意图，但被正确的起点选择取代；不扩展未支持的表格语法。

### 6. timeout 与 registry 发布

`--pipeline-timeout-seconds` 仅用于 MediaWiki crawl 子进程，默认 600，允许 1–86400 的整数。参数解析和 spawn 之间显式传递；同一 crawl 内 discovery/extraction 各自使用该预算。保留 API request timeout 和其他 backend 的行为。测试注入 spawn 验证毫秒值与超时 failure envelope，不真实等待十分钟。

freeze 从旧 registry 文本读取缩进与尾换行约定，保留字典顺序；原位替换已有 domain，新增才 append。新 registry 采用四空格。仍沿用现有 validation/临时文件/rollback 路径，重复 freeze 应字节稳定。

## Risks / Migration

- 缓存验证增加 JSON 读取成本：单次索引、复用已读 entry，优先保证正确性；测试断言无网络/无线程，而不写脆弱耗时阈值。
- v2 缓存可与旧文件并存，短期增大磁盘占用；不自动删除旧缓存，回滚前记录版本边界。
- 旧完成状态重算会增加首次运行耗时，但避免继续交付缺字段的内容。模式变更缺 HTML 时必须重新获取，不能仅改 cache marker。
- 公共全页入口扩展会影响 explore/standalone/production；同 context 比较 core bytes，额外独立断言标签、值、次数与链接，避免等价测试只证明“两边一起错”。
- 冻结修改仍要运行相关生命周期测试；若实施修改站点策略，运行对应 domain site-samples。Grow a Garden 当前样本不是完整 Apple HTML，不能把缺 fixture 的 skip 当作质量通过。
- 实施验收不依赖临时 handoff 目录。自包含 fixture 必须在无缓存 checkout 可运行；真实站点样本缺失需在 verification 记录，不编造全站通过。

### 恢复手册需给出的步骤（本 change 不执行全站恢复）

1. 用已修复的 discovery-only 生成当前策略的新 manifest，审核目录、排除项与差异；旧 1,596 页 manifest 的 37 个 root 不会自动迁移，新发现应归 Misc。
2. 清点缓存 payload，明确缺失 HTML；对比新旧采集模式，不以历史页数硬编码验收。
3. 审核范围后在新输出目录通过 `python3 -m scripts.pipeline` 的受支持入口执行 `--re-fetch --no-resume`，或使用带超时配置的 CLI 和新输出目录。应用层解释器优先仓库 `.venv/bin/python`。
4. 已有合格 HTML 的离线重转可用 `--phase convert assemble --no-resume --no-api-probe`；缺 HTML 时不能采用这条路径。
5. 检查抽样实体的 infobox 字段名及值、跨目录链接、表格、失败/缺页数。通过后再交回独立 my-wiki ingest 任务；不覆盖既有个人产品拆解。
