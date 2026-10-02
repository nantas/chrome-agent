# Design

## Context

输入真源为 `specs/fetch-content-admission/spec.md` 全部五个 requirements 和 `specs/explore/spec.md` 的 deep-discovery / explore-preflight-failure。

现有 Python probe 的 `_build_success` 不检查内容且强制 200；main 先 map_structure 再 identify，且无正文仍可能 generate。Node runScraplingFetch 只检查进程状态，部分路径直接输出 Markdown，容易丢失挑战特征。sample_converter 有独立获取适配器。CloakBrowser 已有标题关键词检查，包含泛化的 cloudflare/attention，既可能误报，也未覆盖本例 Just a second。生产缓存已经有身份、载荷与转换指纹准入，必须在现有边界组合内容检查。

诊断已用本地 406836-byte HTML 回放真实 scrapling 适配器与 probe：返回 success、http_status=200、title=Just a second... - wiki.gg；protection_identifier 返回 cloudflare-managed；fallback 未被调用。回放仅替换 subprocess/preflight，无网络。正式回归须用脱敏最小 fixture，不能依赖 outputs。

## Goals / Non-Goals

**Goals:** 统一正文准入语义，防止挑战页进入成功引擎选择、结构分析、转换、生产缓存及当前 assembly；保留明确失败证据；不牺牲正常页面兼容性。

**Non-Goals:** 独立 API 恢复、验证码绕过、新引擎、站点策略冻结、所有正文质量评分、普遍登录墙/SPA 完整性检测；不将“未发现已知挑战”表述为所有内容质量均合格。

## Decisions

### 1. 单一 Python 准入内核，调用者负责工作流

新增 `scripts/lib/content_admission.py`，提供纯函数 classify_html 与文件入口 admit_html_file，及供 Node 调用的 JSON CLI。使用已有应用层解析库；Node 通过 resolveAppPython 调用，不复制 JS 正则。引擎托管环境只负责获取，应用层在结果返回后做统一检查，避免引擎 venv 导入应用层依赖。

坐标 A=fetch/sub_capability=content_admission、B=shared、C=generic、D=html_generic/html_mediawiki。注册 kernel 和调用关系，提供跨路径等价测试。protection_identifier 消费同一判定；防护历史存在不代表后续正常内容仍受阻。

结果包含 admitted、reason（challenge_page / empty_content / unreadable_output / missing_output / http_error）、protection_type、signals、page_title、content_length。传输层保留 process exit、observed http_status 或 null、诊断路径。signals 只用规则 ID、固定摘要，不回显 token/脚本原文。

### 2. 用页面级组合证据，不做全文关键词黑名单

提取 document title、可见主提示和实际 DOM 属性中的挑战脚本/表单/容器信号，忽略文章代码块里的字面标记。挑战专用结构加页面级等待/验证呈现判拒绝；标题变体覆盖 Just a moment / Just a second / Checking your browser / Enable JavaScript 等，并通过正常页面对照限制误报。单一 Cloudflare 字样、普通 Turnstile iframe、403、长度阈值或缺少 mw-parser-output 不作为挑战判据。

清晰的 HTTP 错误仍失败但不猜测防护供应商。空/不可读结果独立报错。CloakBrowser 的等待机制可保留，最终成功交由共享准入判定；清理泛化标题检查对正常正文的提前拒绝，测试实际等待后的结果边界。

### 3. 同一次获取先验原始 HTML，再做选择器与转换

| 边界 | 接线方式 |
| --- | --- |
| explore/probe_chain.py | 每个 adapter 成功候选先准入；失败保留诊断路径，继续既有链；仅 admitted HTML 可成为 html_content |
| explore/main.py | success_engine 缺失立即输出结构化 failure；不 discover API、不 map/generate/convert；保留既有授权边界 |
| explore/protection_identifier.py | 复用共享信号，避免独立挑战定义；记录失败尝试与最终内容状态的区别 |
| explore/sample_converter.py | HTML 读取后、转换前准入；失败样本参与失败汇总，不因 self-check 跳过而全部通过 |
| CLI runEngineFetch 及直接 adapter 调用者 | HTML 获取先落诊断/临时文件并准入；Markdown 路径使用同一 HTML 做本地转换/选择器提取，不为转换再次访问远端 |
| pipeline HTML 获取及缓存读取 | 组合现有 cache admission，在写成功缓存、convert resume 和 CDP HTML 消费前检查；失败页从本次 assembly 排除 |

API JSON 不被当作 HTML 分类；API 解包出的 HTML 在上述消费边界校验，wikitext/纯文本不适用。保留既有缓存身份与指纹规则，不做批量迁移；旧缓存首次消费时重新准入，拒绝文件作为证据保留。引擎失败时不得误读之前已存在的同路径文件。

### 4. 工作流结果与进程失败分开

main 输出 result（success/partial_success/failure）、reason、probe_chain.results、success_engine、run_dir 及可用 evidence。约定退出码 0=工作流成功、2=有可用正文的部分成功、3=内容不可用；其他错误或无效 JSON 走原内部失败/handoff。Node 只接受退出码与结构一致的已知结果；unknown/malformed 不能伪装成外部受阻。

无内容时 scaffold=null、structure_mapping={}、samples=[]，不给 freeze 建议。所有引擎阻塞则 result=failure；pending 手动 fallback 记录 next_action，不假装已运行。后续引擎恢复正常才允许继续发现。CLI partial_success 仍可表达已有正文但策略待审；不能以 scaffold 路径存在作为 freeze 就绪证明。手动故障处理维持原 Gate，不自动调用用户浏览器。

### 5. 验证按真实边界逐片推进

每片先一个 failing test，再实现通过：共享分类→probe fallback→main 停止→真实 Node/Python 子进程状态→sample→fetch/crawl 同源 HTML→缓存/resume。除网络/引擎边界外尽量保留真实调用者。正常选择器输出使用既有 fixture 比较；共享分类与每个调用者均需反例，不能仅测试 helper。

## Risks / Migration

- 挑战模板变化：保留规则 ID/诊断路径及最小 fixture；本次锁住已见形式，不承诺识别所有防护。
- Python bridge 增加本地 spawn 成本：复用现有应用层解释器，批量路径可一次检查多文件，不引入服务或新依赖。
- Markdown 直出路径变化：保留现有 selector/ai-targeted 行为，对同一 HTML 本地转换的兼容性做回归；不得通过第二次远端获取规避。
- 旧消费者依赖强制 200 或 partial_success：规范明确行为修正，更新 CLI 文档和调用测试；未知状态为 null。
- 旧挑战缓存及已有 Markdown：不删除文件，但当前运行不得 resume 或 assembly 为成功；用户已有草稿保持不动。
- 实施执行 C9 测试、C10 全局同步、C11 注册与 doctor；无引擎升级，C4 不触发。若站点策略实际被修改必须执行对应 site-samples；本范围无需修改。
- 归档前新增永久 fetch-content-admission，Explore 按完整 requirement 合并到既有聚合文件，避免平行规范真源。
