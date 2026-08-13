# Design

## Context

`standalone.py` 的三个函数（`fetch_and_convert` / `reconvert_file` / `reprocess_pages`）服务于 `cli.py` 的 fetch/reprocess/reconvert 子命令，是单页/增量操作入口。它们被搭建时复制了当时 `convert.py` 的编排逻辑，此后 `convert.py` 经历了 4d 重构（preprocess_html 纳入 HTML 路径、convert_page_full 成为声明内核入口），standalone 没有跟随，产生了 preprocess 漂移。`tests/test_convert_equivalence.py`（本 session 建的 CV3/CV4/CV5 等价证明）只覆盖声明的三条路径，不覆盖 standalone，所以漂移未被捕获。

折叠目标是让 standalone 成为 CV4 的薄壳变体，复用已被守护的编排核心，而非继续各自维护。

`specs/convert/spec.md` 是行为真源。

## Goals / Non-Goals

**Goals:**

- fetch/reprocess/reconvert 三子命令的 HTML 模式产出对齐 pipeline 子命令（修 preprocess 漂移）
- standalone.py 不再持有独立的编排实现（消解重复 + 消除未来漂移面）
- §3.1 声明 standalone 变体 + 内核三层接口，使 4d 模型表达完整

**Non-Goals:**

- 改 cli.py 子命令签名 / 参数 / 退出码
- 触碰 wikitext 模式路径
- 改内核 `converter.py`（类/函数/full-orchestration 三层保持）
- C4 cli.mjs 提取

## Decisions

### D1：fetch_and_convert 委托 convert_single_page 而非 convert_page_full

两个候选内核入口：
- `convert_page_full(html, rules)`：声明 kernel entry，返回纯 MD（无 frontmatter / 无标题前置）
- `convert_single_page(raw, page_info, ...)`：CV4 镜像，返回带 frontmatter + 标题前置 + card_stats 的完整 page MD

standalone 子命令的输出格式（带 frontmatter、带 `# title`、带 card_stats）与 CV4 一致，而非纯 MD。故委托 `convert_single_page`，把 fetch 来的 html/images 组装成 `raw` + `page_info` 传入。这样 standalone 输出 ≡ CV4 输出，且 CV4 已被等价测试守护——standalone 自动获得等价保证。

若委托 `convert_page_full` 则需 standalone 自己重做 frontmatter/title/card_stats 装配，等于保留重复编排，违背折叠目标。

### D2：raw 组装 — images 与 content_acquisition

`convert_single_page` 的 HTML 分支触发条件（见 convert.py）：`acq == "html_rendered"` 或 `html and not wikitext and not acq`。standalone 传入 `raw = {"html": html, "images": images, "content_acquisition": "html_rendered"}` 显式走 HTML 路径，images 非空时复用 CV4 的首图注入逻辑（`_first_image_name` + skip_patterns）。extraction_config 透传给 CV4，preprocess_html 由 CV4 内部执行——漂移自动修复。

### D3：reconvert_file 双分支对齐

- **有 source_url 分支**：当前转调 `fetch_and_convert`，自动获益于 D1/D2，无需额外改
- **无 source_url 分支**：当前 `converter.clean_html(body) + converter.convert(...)`，绕过 preprocess 且无 frontmatter 重建以外的逻辑。改为 `convert_page_full(body, extraction_config or {})`，对齐声明的 kernel entry。frontmatter 重建逻辑保留（读回原 frontmatter，body 换成 kernel 输出）

### D4：extraction_config 接口补齐

当前 `fetch_and_convert` 已接受 `extraction_config` 形参但 HTML 分支未透传（漂移根因之一）。折叠后透传给 `convert_single_page`。`cli.py::cmd_fetch` 当前不传 extraction_config（用 None）——保持，行为上是「无配置清理」，与现状一致；漂移修复针对的是「有配置时三子命令该清理却没清理」。

### D5：regression test 证明漂移修复

新增 `tests/test_standalone_convert.py`：构造含 `#catlinks` 的 HTML + `extraction_config = {"cleanup": ["strip_footer"]}`，调 `fetch_and_convert`（mock 掉 ApiClient 网络层），断言输出不含 catlinks 文本。这条测试在折叠前会 FAIL（证明漂移存在），折叠后 PASS（证明修复）——符合 TDD RED→GREEN。

### D6：三层接口声明写入 §3.1

在 `00-target-architecture.md` §3.1 的「目标模块」表之后补一段「内核三层接口」声明，引用本 spec 的 `convert-kernel-three-layer-interface` requirement。同时在表 CV4 行补注「直接用类入口（声明，见三层接口）」。

## Risks / Migration

- **ApiClient 依赖**：`fetch_and_convert` 仍需 `probe_api_endpoint` + `ApiClient` 做网络获取（这是它相对 pipeline 缓存路径的差异——standalone 现取现转）。折叠不改网络层，只改「取到 html 之后怎么转」。regression test 需 mock ApiClient。
- **行为变化可见性**：有 cleanup 配置的站点，fetch/reprocess/reconvert 子命令的输出会变化（开始应用清理）。这是 bug 修复方向，但若有人依赖旧的「未清理」输出需知晓。在 verification + commit message 标注。
- **equivalence 边界**：standalone 折叠后 ≡ CV4，但 standalone 仍带网络取数（CV4 假设 raw 已就绪）。等价仅在「转换核心」层面成立，不在「取数」层面——声明中区分。
