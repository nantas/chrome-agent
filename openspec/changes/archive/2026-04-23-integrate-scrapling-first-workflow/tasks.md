# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `specs/scrapling-first-browser-workflow/spec.md` 覆盖 Scrapling-first routing、fallback boundaries、environment contract、verification baseline、documentation and site knowledge。
- [x] 1.2 确认本地前置条件：`uv` 可用，系统 Python 不作为 Scrapling 运行时，Scrapling 运行环境需要 Python `>=3.10`。
- [x] 1.3 确认实现不引入凭据管理、默认 Spider/checkpoint、代理池或大型自动化框架。

## 2. 核心实现任务

- [x] 2.1 更新 `AGENTS.md`：保留 Content Retrieval / Platform/Page Analysis 分类，但把两类任务的工具优先级改为 Scrapling-first，并写清 `chrome-devtools-mcp` 与 `chrome-cdp` 的 fallback 触发条件。
- [x] 2.2 更新 `README.md`：将当前状态、原则、工作规则和 open gaps 改为 Scrapling-first，并保留 DevTools/CDP 的诊断与 live-tab 边界。
- [x] 2.3 新增 Scrapling setup 文档：记录 `uv` Python `>=3.10` 环境、Scrapling 安装、`scrapling install`、CLI smoke check、MCP server 配置和失败排查。
- [x] 2.4 更新项目 MCP 配置或配置说明：在 Scrapling CLI/MCP smoke check 成功后加入 Scrapling MCP server 路径，同时保留现有 `chrome-devtools` 配置。
- [x] 2.5 新增或更新 `docs/decisions/` 决策记录：说明 Scrapling-first 取代 DevTools-first 作为抓取优先路径，旧决策仍适用于诊断和 live-session fallback。
- [x] 2.6 更新 `docs/playbooks/browser-tooling-evaluation.md`：加入 Scrapling-first 评估矩阵、成功标准、失败记录字段和 fallback 证据要求。
- [x] 2.7 在需要时补充 `sites/` 说明：仅在验证中获得可复用站点经验时记录 Scrapling 成功、失败或 fallback 规则。

## 3. 收敛与验证准备

- [x] 3.1 运行环境 smoke checks：验证 Python `>=3.10` 环境、Scrapling 可导入、`scrapling --help` 或等价 CLI 命令可运行、浏览器依赖安装状态可确认。
- [x] 3.2 运行公开页面 baseline：至少验证 static public page，并记录 Scrapling fetcher path、title、final URL、content excerpt 和 fallback 是否需要。
- [x] 3.3 运行动态页面 baseline：验证一个 JS-rendered or dynamic page，并记录 DynamicFetcher 或对应路径是否可用。
- [x] 3.4 运行文章抽取 baseline：验证正文 reading order 和 inline image URL 保留；失败时记录最终 URL、缺失节点和 fallback 路径。
- [x] 3.5 运行受保护页面 baseline：验证 protected-page attempt，并记录 Scrapling stealth/session 路径、阻断状态和是否需要 DevTools/live-tab fallback。
- [x] 3.6 在用户批准确切目标页后验证登录态只读实验：先尝试 Scrapling session path，再记录是否成功、失败或需要 `chrome-cdp` live-tab fallback；任何 logout、redirect、reset 或 write-action 风险都必须停止并记录。

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`，覆盖 spec-to-implementation 与 task-to-evidence。
- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`，列出目标文档、字段映射、前置条件和冲突处理。
- [x] 4.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据：链接、时间、执行人、结果。
