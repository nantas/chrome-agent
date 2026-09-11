# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 核对八份 `specs/*/spec.md` 与 design 的模块边界，记录当前 HEAD、四个既有修改文件及无关未跟踪内容；保留缓存/表格补丁意图，不覆盖用户修改。
- [x] 1.2 阅读对应 P0/P1 与 testing-governance 规范；核对 `obsidian-safe-filenames` 的同文件影响，确认只改内部缓存协议，不改输出命名。测试统一放 `tests/`，Python unittest / Node node:test，无新增依赖。

## 2. 核心实现任务

严格按每对 RED → GREEN 顺序推进；一个场景通过后再做下一个，不先写完所有测试。已有工作区补丁已修的场景，以受控 HEAD 复现或 mutation 证明测试能捕获原缺陷，禁止回滚用户工作区来制造 RED。

### Slice A — 共享全页 infobox 编排

- [x] 2.1 RED：在 `tests/test_convert_equivalence.py` 通过真实 `convert_single_page` 构造启用 infobox 的自包含 HTML，断言独有字段名/值和 `## Infobox` 出现一次；证明当前生产路径失败。覆盖 `convert` / `extract-kernel`。
- [x] 2.2 GREEN：扩展 `convert_page_full` 可选 converter/source_dir 参数，CV4 委托完整五步，保留 frontmatter/card stats 与两参兼容；移除 CV4 重复后处理，跑该场景及现有等价/standalone 测试。
- [x] 2.3 RED：逐个增加 infobox 跨目录链接、redirect、配置 base URL/无 base URL、field handler、无匹配 infobox 和 post-op fixture；每个新增场景独立证明当前缺口，等价比较仅去除声明包装。
- [x] 2.4 GREEN：在共享提取层接通 renderer/handler/source_dir，统一 URL 上下文并拒绝冲突规则；逐场景使 2.3 通过，保留表格/图片/正文已有行为，不新增站点特判。

### Slice B — 缓存身份与兼容读取

- [x] 2.5 RED：在 `tests/` 的 cache 测试通过 save/load/list 公共入口覆盖 `A/B`、`A_B`、`A:B`、`A B`、Unicode、长标题与并发写，证明碰撞/反解缺陷；全部使用临时目录。
- [x] 2.6 GREEN：在 `cache.py` 实现版本化哈希键、原 title 校验、metadata 枚举和唯一临时文件原子写，使 2.5 通过；记录缓存存储协议 ADR（先选择未占用编号）。覆盖 `mediawiki-cache-integrity`。
- [x] 2.7 RED：逐个构造两种旧命名、标题不符、损坏 JSON、markerless 合格 HTML、路径越界候选，验证兼容读取和拒绝行为。
- [x] 2.8 GREEN：实现 v2 优先/安全 legacy fallback，读不改旧文件，诊断明确；证明 2.7 场景和既有缓存调用方测试通过。

### Slice C — acquisition 准入与 fetch 快速路径

- [x] 2.9 RED：通过 fake ApiClient + 真实 `run_fetch` 覆盖全兼容无请求、混合模式仅重抓缺口、default profile、`--re-fetch`、新获取内容不满足请求；断言不兼容 hybrid 不计入 HTML skip。覆盖 `mediawiki-cache-integrity` / `fetch-phase-cache-fastpath`。
- [x] 2.10 GREEN：实现单一 admission API；从 resolved strategy 取模式，复用 acquisition 的动态 fallback 判定；fetch 索引按准入分组，新响应准入后才统计成功，保留仅实际请求延时规则；逐个通过 2.9。

### Slice D — convert 与 resume 不接受旧结果

- [x] 2.11 RED：经真实 convert phase，构造 HTML 策略+旧 hybrid cache+已存在 Markdown/completed 状态；断言 `cache_incompatible`、无隐式 fetch、不能进入成功 assembly。覆盖 `pipeline-convert-phase`。
- [x] 2.12 GREEN：在 resume 和路由前执行统一准入，移除 warning 后继续旧模式的行为；将无效完成状态和失败结果正确传给 orchestrator/assembly，旧物理文件不作为本次成功。
- [x] 2.13 RED：逐个验证匹配 fingerprint 才跳过、旧无 fingerprint 状态重转、payload/config/acquisition/link-target/revision 变化重转，以及 `--no-resume`、写入中断和重抓失败；使用临时输出目录。
- [x] 2.14 GREEN：状态增加逐页转换指纹与 converter revision，稳定摘要排除 fetched_at；成功落盘才记录完成，复用全局 link/config 摘要，逐个通过 2.13。

### Slice E — wikitable 扫描前进

- [x] 2.15 RED：在 `tests/` 添加有 subprocess timeout 的文首单表+尾文回归；对已存在守卫用隔离 HEAD/mutation 证明捕获挂死。再逐个覆盖文首两表、文中表、嵌套和未闭合余文，验证内容与顺序。覆盖 `pipeline-converters`。
- [x] 2.16 GREEN：优先处理首次 offset 0 表，再按单调 cursor 扫描；保留已有解析语法和余文，逐个通过 2.15。不得只证明“不挂死”而遗漏第一表或单元格。

### Slice F — MediaWiki 子进程超时

- [x] 2.17 RED：扩展 `tests/mediawiki-crawl.test.mjs` 及 CLI 参数入口测试，通过 stub spawn 验证默认600秒、自定义3600秒、非法/缺值、discovery/extraction预算、超时failure envelope和确认门不变。覆盖 `cli`。
- [x] 2.18 GREEN：实现 `--pipeline-timeout-seconds` 校验/传递和诊断字段，更新 CLI help；不实际等待长超时、不影响其他backend；通过 2.17 和现有 MediaWiki 失败契约测试。

### Slice G — freeze 稳定发布

- [x] 2.19 RED：在生命周期测试用临时 registry 覆盖四空格/两空格、尾换行、原位更新、新增append、重复freeze字节稳定，以及发布失败回滚。覆盖 `strategy`。
- [x] 2.20 GREEN：保留输入格式和无关条目顺序，创建时默认四空格，沿用校验与原子发布；通过 2.19，不直接重排真实 registry。

## 3. 收敛与验证准备

- [x] 3.1 对 fake API → cache → convert → assembly 跑离线集成恢复：旧hybrid/旧completion起步，返回含infobox HTML，验证新输出字段完整、失败页不混入、第二次同输入可resume；不依赖临时handoff或真实网站。
- [x] 3.2 运行 `.venv/bin/python -m unittest discover -s tests -v` 与 `node --test tests/*.test.mjs`，记录新旧失败归属；按改动覆盖保留的 pipeline 旧测试。确认 Python 3.9 兼容、纯ESM和无新增测试依赖。
- [x] 3.3 运行 growagarden.fandom.com、neonabyss.fandom.com、slaythespire.wiki.gg、bindingofisaacrebirth.wiki.gg 的 `python3 scripts/test_runner.py site-samples --domain DOMAIN`（可用仓库 `.venv/bin/python`）；记录缺fixture/skip，不能标为全站质量通过。若改策略必须满足 C9，golden 变更先核对字段而非直接接受。
- [x] 3.4 检查 capability registry 与等价测试指针；若增加能力实现文件则同步注册。按 C10 Case 6 同步 runtime/skill，刷新 installed-hash 至当时 HEAD，验证 `chrome-agent doctor --format json` 和 `chrome-agent doctor --check capabilities`，记录任何环境阻塞。

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现生成 `verification.md`，建立八份spec→代码→测试证据映射；区分离线通过、站点样本和未执行的全站恢复，不用1,596/1,602固定页数作成功证据。
- [x] 4.2 读取 binding 的标准引用，基于 verification 生成 `writeback.md`；列明架构/CLI/CONTEXT更新与恢复手册，缓存协议ADR及 `obsidian-safe-filenames` 交叉影响。
- [x] 4.3 执行 binding 中本仓文档回写并记录证据；手册给出新manifest审核、缓存清点、重抓/离线重转两条路径、新输出目录和字段验收。全站抓取与my-wiki ingest保留为独立恢复任务，不在此执行。
- [x] 4.4 验证 change 与能力 doctor；归档前把delta合并到现有规范。`strategy` 的既有生命周期正文位于 `openspec/specs/strategy/strategy-lifecycle.md`，避免另建冲突真源；同步纠正旧入口编排说明，保留不受本change影响的requirement。
