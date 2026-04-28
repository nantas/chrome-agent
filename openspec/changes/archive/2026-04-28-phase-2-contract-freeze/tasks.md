# Tasks

## 1. Smoke-check 证据收集

- [x] 1.1 执行 Scrapling get smoke check：抓取 mp.weixin.qq.com 公开文章，验证 DOM 顺序 + 内联图片 URL 保留 — 成功：提取到文章标题 "Karpathy：一切软件，都将为 Agent 重写"、封面图 URL 保留、正文字体 DOM 顺序（spec: scrapling-get-contract, Smoke-check scenario requirement）
- [x] 1.2 执行 Scrapling fetch smoke check：抓取 x.com/<user>/status/<id> 公开推文，验证 SPA 渲染内容（作者、推文文本、媒体链接），如被登录门重定向则记录为 known limitation — 成功：SPA 渲染推文内容（作者 @CopyRebeldia、推文文本、视频缩略图），底部登录门出现但内容已加载（known limitation: 底部注册提示，但核心推文内容已获取到）（spec: scrapling-fetch-contract, Smoke-check scenario requirement）
- [x] 1.3 执行 Scrapling stealthy-fetch smoke check：抓取 wiki.supercombo.gg/w/Street_Fighter_6，验证 `solve_cloudflare=true` 突破 CF Turnstile，返回文章内容而非挑战壳（spec: scrapling-stealthy-fetch-contract, Smoke-check scenario requirement）
- [x] 1.4 执行 chrome-devtools-mcp smoke check：诊断 x.com/hashtag/StreetFighter6，收集 snapshot + network，确认登录门检测正确触发 — 已验证：sites/x.com-public-hashtag-search-login-gate.md 记录完整诊断证据（spec: chrome-devtools-mcp-contract, Smoke-check scenario requirement）
- [x] 1.5 执行 chrome-cdp smoke check：在已认证 fanbox.cc 页面验证帖子列表内容、cookie 提取、无 auth redirect — 已验证：sites/fanbox.cc-content-download.md 记录完整认证会话证据（spec: chrome-cdp-contract, Smoke-check scenario requirement）

## 2. 引擎契约 Spec 创建

- [x] 2.1 创建 `openspec/specs/scrapling-get-contract/spec.md`（基于 delta spec 的 ADDED Requirements）
- [x] 2.2 创建 `openspec/specs/scrapling-fetch-contract/spec.md`（基于 delta spec，incorporate smoke check 结果）
- [x] 2.3 创建 `openspec/specs/scrapling-stealthy-fetch-contract/spec.md`（基于 delta spec）
- [x] 2.4 创建 `openspec/specs/chrome-devtools-mcp-contract/spec.md`（基于 delta spec）
- [x] 2.5 创建 `openspec/specs/chrome-cdp-contract/spec.md`（基于 delta spec）
- [x] 2.6 创建 `openspec/specs/engine-contracts/spec.md`（聚合索引，基于 delta spec）

## 3. 证据文档补充

- [x] 3.1 如 fetch smoke check 成功获取推文内容，创建 `sites/x.com-public-tweet.md` 站点经验文档（记录 fetch SPA 渲染的行为特征）

## 4. 总体规划文档更新

- [x] 4.1 更新 `docs/governance-and-capability-plan.md` Phase 2 的描述：修正需要的 specs 列表（移除 `error-handling`，列出 6 个实际 capabilitiy），更新交付物描述（design: Decision 6）

## 5. 验证与回写收敛

### Verification

- [x] 5.1 验证 5 个引擎契约 spec 均包含 input/output/error 三维 + smoke-check scenario（spec: engine-contracts, Contract compliance requirement）
- [x] 5.2 验证 engine-contracts 聚合索引正确引用所有 5 个引擎契约并包含错误矩阵和 smoke-check 清单
- [x] 5.3 验证 governance-plan 中 Phase 2 描述与实际 deliverables 一致
- [x] 5.4 验证所有 smoke check 的执行证据已记录（成功/known limitation）

### Writeback

- [x] 5.5 生成 writeback.md（基于 verification 结论）
- [x] 5.6 执行 writeback：更新 Obsidian 项目页状态（ref: binding.md writeback_targets）
