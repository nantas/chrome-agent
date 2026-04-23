# Proposal

## 问题定义

当前仓库已经完成 `Scrapling-first` 集成，并通过公开页、动态页、文章页、受保护页和已批准登录态页面的验证，确认了默认抓取路径与 fallback 边界。但 `AGENTS.md` 里的默认网页抓取工作流仍然分散在 `Workflow`、`Tooling Strategy`、`Selection Rules` 和 `chrome-cdp` 边界等多个章节中，操作层存在三个问题：

- 默认入口、升级条件和登录态边界需要跨多个段落拼接，代理读取成本偏高。
- `Scrapling-first`、`chrome-devtools-mcp` 诊断 fallback、`chrome-cdp` live-tab fallback 的规则有重复表达，容易在后续演化时出现轻微不一致。
- 最新验证结果已经说明，像 `x.com` 这类站点上 Scrapling session 复用可能无法继承现有登录态，`AGENTS.md` 需要把这个结论整理成明确的默认流程，而不是只留在报告和站点笔记中。

本 change 目标是根据现有验证结果，重排 `AGENTS.md` 的默认网页抓取工作流，使默认抓取入口、升级条件和登录态 live-session 边界一眼可见，并保持与前一轮 Scrapling-first 工件完全一致。

## 范围边界

范围内：

- 依据当前验证结果，重排 `AGENTS.md` 中与默认网页抓取流程相关的章节结构和规则顺序。
- 把默认流程整理为清晰主线：先路由任务类型，再优先 Scrapling，最后按触发条件升级到 `chrome-devtools-mcp` 或 `chrome-cdp`。
- 把登录态和 live-session 场景的 read-only 边界、用户批准前提、失败停止条件写成显式规则。
- 让 `AGENTS.md` 对齐既有的 OpenSpec spec、verification、site notes 和 playbook。

范围外：

- 不修改 Scrapling 运行环境、MCP 配置或 CLI 安装方式。
- 不新增抓取器、自动化框架或新的 runtime capability。
- 不改写历史报告，只整理默认工作流表达和必要的治理文档。
- 不重新设计 `README.md` 或其它文档，除非实现时发现与 `AGENTS.md` 存在直接冲突需要最小同步。

## Capabilities

### New Capabilities

### Modified Capabilities

- `scrapling-first-browser-workflow`: 根据已验证结果重排默认网页抓取流程表达，明确 Scrapling-first 主线、诊断 fallback 和 live-tab fallback 的触发边界。

## Capabilities 待确认项

- [x] 能力清单已与用户确认：本次 change 只修改既有 `scrapling-first-browser-workflow` 的治理表达，不引入新 capability。

## Impact

- `AGENTS.md` 将从分散规则集合重排为更显式的默认抓取流程入口。
- 代理后续读取仓库操作规范时，将先按主流程判断是否继续留在 Scrapling，再决定是否升级到 `chrome-devtools-mcp` 或 `chrome-cdp`。
- 登录态场景的决策会更加具体：允许先试 Scrapling session 复用，但若登录态未继承或跳转登录流，应停止该路径并切换到已批准的 live-tab fallback。
- 与 `integrate-scrapling-first-workflow` 相关的验证和站点经验将成为这次文档重排的直接依据。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
  - `project_page_ref`: `/Users/nantasmac/projects/agentic/chrome-agent/AGENTS.md`
  - `writeback_targets`: `/Users/nantasmac/projects/agentic/chrome-agent/AGENTS.md`, `/Users/nantasmac/projects/agentic/chrome-agent/README.md`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/decisions/`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/playbooks/`
