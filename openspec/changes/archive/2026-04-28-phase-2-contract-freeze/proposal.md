# Proposal

## 问题定义

Phase 1 完成了治理基础重建——AGENTS.md 转为纯治理文档、契约元模型（`capability-contracts`）定义了 input/output/error 三维结构和命名规则。但仓库的 5 个引擎（Scrapling get、fetch、stealthy-fetch、chrome-devtools-mcp、chrome-cdp）的接口契约仍然缺失。缺乏契约导致：

1. **引擎选择依赖经验而非规范**：Agent 判断使用哪个引擎时，依赖 AGENTS.md 中的路由规则和先前的站点经验，没有机器可读的引擎行为定义
2. **错误处理无统一语义**：各引擎的错误分类、错误结构、推荐 next action 不一致，运维和调试依赖个人经验
3. **引擎输出不可预期**：没有明确定义每个引擎的输出格式、metadata 字段、图片处理行为
4. **Phase 3 策略库无法启动**：策略库中的字段类型和错误码依赖冻结的引擎契约

Phase 2 需要基于 Phase 1 的契约元模型，为 5 个引擎逐一建立契约规范，并通过真实站点的 smoke check 验证契约的正确性。

## 范围边界

**范围内（本 change）：**
- 为 5 个引擎创建契约 spec：`scrapling-get-contract`、`scrapling-fetch-contract`、`scrapling-stealthy-fetch-contract`、`chrome-devtools-mcp-contract`、`chrome-cdp-contract`
- 创建 `engine-contracts` 聚合索引 spec，汇总所有引擎契约的引用关系和状态
- 每个引擎契约包含 3 个维度：input contract（URL 格式/参数/session 模式/auth 边界）、output contract（提取格式/content 结构/metadata/图片处理）、error contract（错误分类/错误结构/next action）
- 每个引擎契约包含 smoke-check scenario，引用已知验证目标 URL
- 对 Scrapling fetch 引擎补充 Twitter 公开推文的 smoke check 证据（fetch 是现有引擎中证据最弱的）

**范围外（留到后续 Phase）：**
- 不修改任何引擎实现
- 不添加新引擎或扩展工具
- 不涉及策略库标准化（Phase 3）
- 不涉及引擎注册机制（Phase 4）
- 不创建独立的 `error-handling` spec（错误规范融入各引擎契约的 error 维度）

## Capabilities

### New Capabilities

- `scrapling-get-contract`: Scrapling HTTP get 引擎的契约——input/output/error 三维 + 微信公开文章 smoke check（evidence: sites/wechat-public-article.md）
- `scrapling-fetch-contract`: Scrapling Playwright fetch 引擎的契约——input/output/error 三维 + Twitter 公开推文 smoke check（evidence: Phase 2 新补）
- `scrapling-stealthy-fetch-contract`: Scrapling stealthy-fetch 引擎的契约——input/output/error 三维 + Cloudflare Turnstile smoke check（evidence: sites/wiki.supercombo.gg-cloudflare-challenge.md）
- `chrome-devtools-mcp-contract`: Chrome DevTools MCP 诊断引擎的契约——input/output/error 三维 + x.com 诊断 smoke check（evidence: sites/x.com-public-hashtag-search-login-gate.md）
- `chrome-cdp-contract`: Chrome CDP 实时会话延续引擎的契约——input/output/error 三维 + fanbox.cc / x.com 认证 smoke check（evidence: sites/fanbox.cc-content-download.md, sites/x.com-public-hashtag-search-login-gate.md）
- `engine-contracts`: 引擎契约聚合索引——列出所有引擎契约的引用、覆盖状态、engine 类型与使用场景映射表

### Modified Capabilities

（无）

## Capabilities 待确认项

- [x] 能力清单已与用户确认（对话中确认：5 独立契约 + engine-contracts 聚合索引、error 融入各引擎、smoke-check 场景验证、fetch target 为 Twitter 公开推文）

## Impact

**益处：**
- 每个引擎的行为有明确的 spec 真源，Agent 可基于契约做出引擎选择判断
- 错误分类和 next action 统一，减少调试中的歧义
- 为 Phase 3 策略库提供字段类型和错误码的标准引用
- 为 Phase 4 引擎扩展提供"什么是合格引擎"的契约模板

**影响到的既有文件：**
- `openspec/specs/` 新增 6 个 capability 目录
- `docs/governance-and-capability-plan.md` Phase 2 描述需微调以反映实际交付物
- `sites/` 可能新增 Twitter 公开推文的站点经验文档（fetch smoke check 产物）

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
  - `project_page_ref`: `20_项目/chrome-agent/chrome-agent.md`
  - `writeback_targets`: Obsidian 项目页 + Writeback 记录页
