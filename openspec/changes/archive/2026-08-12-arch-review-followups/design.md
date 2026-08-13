# Design

## Context

本 change 为**回溯性记录**——候选 1 与候选 6 已于本 session 直接实现（commits `f03376d`、`ac08bba`、`42e2dcc`）。design 不重新设计实现，而是固化实现决策的依据，供 verification 阶段核对。`specs/convert/spec.md` 是行为真源。

convert 镜像等价契约来自 ADR 0013 §4.3 与 00-target-architecture.md §4.3：同一 HTML 经内核与镜像产出必须字节级一致。先前唯一的证明文件 `tests/test_golden_convert.py` 断言的是内核内部 A/B（wrapper vs class，构造上恒等）且缓存缺失即 skip，无法兑现跨路径契约——这正是本 change 候选 1 要补的洞。

## Goals / Non-Goals

**Goals:**

- 候选 1：提供 `specs/convert/spec.md` 中 `mirror-equivalence-golden-snapshot` 的真实可执行证明（CV3/CV4/CV5 ≡ CV1 内核）
- 候选 6：消除 fanbox 两脚本间 ~10 个 helper 的复制粘贴

**Non-Goals:**

- 重做实现（已提交）
- 改 convert spec 文本（指针回填已在 `archive/2026-08-12-cleanup-post-4d-drift/` 完成）
- 合并 convert 内核的双公开入口（类 vs 函数）—— 属候选 3 的结构工作，暂停
- cli.mjs / standalone.py 结构重构（候选 4/5）—— 暂停

## Decisions

### D1：fixture 内嵌而非复用 `.cache`

`test_golden_convert.py` 依赖 `.cache/mediawiki/.../Bloody_Gust.json`，缺失即 skip，多数环境空转。新测试内嵌 fixture（覆盖链接/表格/列表/图片 + KI 字符哨兵），永不 skip，确定性可复现。

### D2：判别元素用 `#catlinks` 而非 `.navbox`

第一版用 `.navbox` 作「preprocess 可观测」哨兵失败——`HtmlToMarkdownConverter` 的 `clean_html` 同样剥离 navbox 类。改为 `#catlinks` + `cleanup:["strip_footer"]`：只有 `preprocess_html` 移除它，内核 `clean_html` 不认识，从而突变检查能捕获「CV4 跳过 preprocess」的回归。

### D3：CV4 包装剥离而非重新实现编排

CV4 的 `convert_single_page` 输出含 YAML frontmatter + 条件标题。测试剥离这层**声明的包装**再比内核，而非在测试里重写 CV4 的编排（避免「测试测自己的副本」反模式，见 discovery_summary 教训）。标题条件化（正文已以 `#` 开头则不前置）记录在剥离函数注释。

### D4：convert spec 不改文本

`mirror-equivalence-golden-snapshot` requirement 的指针已在删除批 change 回填为 `test_convert_equivalence.py`。本 change 的 convert delta 为「实现兑现确认」记录（含 fixture-discriminates-preprocessing / test-never-skips 两个新增 scenario 细化契约），不重复改 spec 永久文件。

### D5：fanbox helper 无状态化提取

`sh/sleep/escapeXml/extractChineseText/extractActorNames/downloadCover/generateNfo/findTarget/cdpEval/cdpNav` 提取到 `scripts/lib/fanbox-shared.mjs`，CDP 路径/目标/cookie 改为参数传入，避免模块级 `TARGET`/`FANBOX_COOKIE` 状态泄漏进共享层。`extractActorNames` 候选名单差异（5 vs 12）参数化，各自保留。

### D6：fanbox 不共享差异项

`fetchWithRetry`（外部版有 RATE_LIMITED 哨兵 + 不同重试次数）、`fetchPostDetail`（字段形状不同）差异是实质性的，硬合并是假复用——保留在各自脚本。

## Risks / Migration

- **回溯性 change 的合规性**：实现先于 change。verification 阶段复跑现有测试确认状态与 spec 一致；治理轨迹由本 change 补齐，不产生行为回归。
- **候选 6 两处有意硬化**（已在 commit message 记录）：`downloadCover` curl 失败返回 `"0"` 而非抛异常（两脚本本就有非 200 的 png fallback，原内部版会 Fatal 退出——属修复而非回归）；`generateNfo` 的 `dateadded` 从脚本启动时改为调用时（外部版有 3h 限流冷却，跨午夜时更准确）。
- **fixture 覆盖边界**：等价测试守「同配置下三路径无分叉」这一条契约；站点策略样本测试（`site-samples`）守逐站点配置正确性，二者职责不重叠。
