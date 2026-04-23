# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 对照 `specs/scrapling-first-browser-workflow/spec.md`，确认本次实现只覆盖默认抓取流程表达重排，不扩展运行时能力或环境配置。
- [x] 1.2 盘点 `AGENTS.md` 中当前分散描述默认抓取流程的章节，标记需要重排、合并或删除的重复规则。

## 2. 核心实现任务

- [x] 2.1 重排 `AGENTS.md` 的默认网页抓取工作流，使操作顺序清晰呈现为：任务路由、live-session 判断、Scrapling-first、按触发条件升级 fallback。
- [x] 2.2 在 `AGENTS.md` 中明确常见抓取场景与 Scrapling 首选路径的对应关系，包括 `get`、`fetch`、`stealthy-fetch`、bulk 和 session 变体的使用边界。
- [x] 2.3 在 `AGENTS.md` 中分离两类 fallback：把 `chrome-devtools-mcp` 写成诊断/证据路径，把 `chrome-cdp` 写成已打开真实标签页的 live-session continuity 路径。
- [x] 2.4 在 `AGENTS.md` 中写清 authenticated read-only 边界：用户批准前提、登录态未继承时的停止条件、以及切换到已批准 live tab 的规则。
- [x] 2.5 清理 `AGENTS.md` 中任何仍暗示 `chrome-devtools-mcp` 或 `chrome-cdp` 是普通网页抓取默认入口的残留措辞。

## 3. 收敛与验证准备

- [x] 3.1 用 `integrate-scrapling-first-workflow` 的 `verification.md` 和 `sites/x.com-public-hashtag-search-login-gate.md` 对照 `AGENTS.md` 草稿，确认默认流程与已验证结果一致。
- [x] 3.2 检查 `README.md`、`docs/decisions/`、`docs/playbooks/` 是否存在与新 `AGENTS.md` 直接冲突的默认路径表述；若存在，记录需要最小同步的目标。

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`，说明 `AGENTS.md` 的主流程、fallback 边界和登录态规则是否已与 spec 对齐。
- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`，列出需要同步的治理文档目标、字段映射和前置条件。
- [x] 4.3 执行 `writeback.md` 中定义的回写目标，并记录可审计证据：链接、时间、执行人、结果。
