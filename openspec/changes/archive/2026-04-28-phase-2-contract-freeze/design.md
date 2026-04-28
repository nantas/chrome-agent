# Design

## Context

Phase 1 完成了治理基础重建——AGENTS.md 转为纯治理文档，`capability-contracts` 元模型定义了引擎契约的三维结构（input/output/error）和命名规则（`openspec/specs/<engine-id>-contract/spec.md`）。Phase 2 基于此元模型，为仓库 5 个已验证引擎逐一建立契约规范。

现有的 5 个引擎中，Scrapling get（微信文章）、stealthy-fetch（Cloudflare）、chrome-cdp（fanbox.cc）有丰富的站点证据；Scrapling fetch 证据较弱，需要在 Phase 2 中补 smoke check；chrome-devtools-mcp 是诊断引擎，契约结构与内容抓取引擎有本质区别。

## Goals / Non-Goals

**Goals:**
1. 创建 5 个引擎契约 spec + 1 个聚合索引 spec（共 6 个 capability）
2. 每个引擎契约包含完整的 input/output/error 三维 requirements
3. 每个引擎契约包含已知 target URL 的 smoke-check scenario
4. 对 Scrapling fetch 补充 Twitter 公开推文的 smoke check 证据
5. `engine-contracts` 聚合索引提供引擎类型映射、错误归类矩阵、smoke-check 清单
6. 更新 `docs/governance-and-capability-plan.md` Phase 2 描述

**Non-Goals:**
- 不创建独立的 `error-handling` spec（error 维度融入各引擎契约）
- 不修改任何引擎实现
- 不添加新引擎
- 不涉及 Phase 3 策略库或 Phase 4 引擎注册

## Decisions

### Decision 1: Spec 文件结构

```
openspec/specs/  (Phase 2 新增)
├── scrapling-get-contract/spec.md              # Scrapling get 契约
├── scrapling-fetch-contract/spec.md            # Scrapling fetch 契约
├── scrapling-stealthy-fetch-contract/spec.md   # Scrapling stealthy-fetch 契约
├── chrome-devtools-mcp-contract/spec.md        # CDP 诊断引擎契约
├── chrome-cdp-contract/spec.md                 # CDP 实时会话引擎契约
└── engine-contracts/spec.md                    # 聚合索引
```

按 Phase 1 `capability-contracts` 元模型规定，每个引擎独立目录存放。`engine-contracts` 是聚合索引 spec，不替代任何引擎的行为规范真源。

### Decision 2: error-handling 处置

不创建独立的 `error-handling` spec。通用错误分类（network/timeout/block/auth/parse）在 `capability-contracts` 元模型中已定义。

每个引擎契约在各自的 Error Contract 中定义引擎特定的错误类别和推荐 next action。`engine-contracts` 聚合索引提供跨引擎的错误类别对比矩阵（见 spec: engine-contracts, Cross-engine error contract consistency requirement）。

规划原文中 `error-handling` spec 的需求被各引擎契约的 error 维度 + engine-contracts 的 error matrix 覆盖。

### Decision 3: Smoke-check 策略

每个引擎契约的 smoke-check scenario 引用真实站点验证目标：

| Engine | Target | 验证重点 |
|--------|--------|---------|
| get | mp.weixin.qq.com 公开文章 | DOM 顺序 + 图片保留 + `#js_content` 提取 |
| fetch | x.com/<user>/status/<id> | SPA 渲染 + 动态内容 + wait_selector 行为 |
| stealthy-fetch | wiki.supercombo.gg/w/Street_Fighter_6 | CF Turnstile 突破 + `solve_cloudflare` 效能 |
| chrome-devtools-mcp | x.com/hashtag/StreetFighter6 | snapshot + network + 登录门检测 |
| chrome-cdp | fanbox.cc/@.../posts | 认证 session + 帖子列表 + cookie 提取 |

Smoke check 不作为自动化测试脚本实施（Phase 2 排他边界："不修改引擎实现"），而是作为 spec 内的验证场景，在 apply 阶段手动执行并记录结果。

### Decision 4: chrome-devtools-mcp 契约的差异化

chrome-devtools-mcp 是诊断引擎，不是内容抓取引擎。其契约与 Scrapling 引擎有本质区别：

- **Input**: 侧重页面导航 + 诊断动作（snapshot/screenshot/network/console/performance/evaluate），不关注 extraction_type/content_only 等抓取参数
- **Output**: 产出结构化证据（a11y snapshot、截图、网络请求列表、console 日志），不产出"正文提取"等价物
- **Error**: 侧重 connection/navigation/selector 诊断特定错误，没有 block/parse 等抓取错误

### Decision 5: 契约的版本标识

所有 5 个引擎契约 spec 使用 `version: 1.0.0` 作为初始版本。`engine-contracts` 聚合索引使用相同版本。后续修改通过 openspec change 流程进行，每个引擎契约独立版本演进。

### Decision 6: 总体规划文档的 Phase 2 描述更新

`docs/governance-and-capability-plan.md` 中 Phase 2 当前描述：
- 需要的 specs: `engine-contracts`、`error-handling`

更新为：
- 需要的 specs: `scrapling-get-contract`、`scrapling-fetch-contract`、`scrapling-stealthy-fetch-contract`、`chrome-devtools-mcp-contract`、`chrome-cdp-contract`、`engine-contracts`（聚合索引）
- 排他边界增加：不创建独立的 error-handling spec（融入各引擎契约）

## Risks / Migration

- **风险 1**: Scrapling fetch 的 Twitter smoke check 可能受 x.com 登录门影响（已知 x.com 会重定向到 /i/flow/login）。缓解措施：如果公开推文页面在 fetch 测试中被重定向到登录页，在 contract 中记录为 known limitation，测试结果仍然作为有效证据（证明了 "fetch 无法绕过该域的 auth gate"）。
- **风险 2**: 契约 spec 中的参数描述和实际工具 API 可能存在微小偏差。缓解措施：在 apply 阶段通过 smoke check 验证关键参数的行为正确性，发现偏差时更新 spec。
- **风险 3**: Phase 3 的策略库可能发现 Engine Contract 需要额外字段。缓解措施：这是一个预期内的迭代——contract 支持通过 openspec Modified Capabilities 流程扩展，版本号递增。
