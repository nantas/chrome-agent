# Proposal

## 问题定义

当前 chrome-agent 的引擎管线中，`scrapling-get`（纯 HTTP）和 `scrapling-fetch`（Playwright）之间存在明显的效率断层：

- `scrapling-get` 极快（~1s）但无法处理 JS 渲染页面
- `scrapling-fetch` 功能完整但需要启动完整 Chromium（~200MB 内存，4-8s 启动+加载）
- 大量「需要 JS 渲染但不需要完整浏览器功能」的中间场景（动态列表、搜索页、轻度 SPA）缺乏适合的引擎

**Obscura**（`h4ckf0r0day/obscura`）是一个用 Rust 编写的轻量级 headless 浏览器引擎，内置 V8 JavaScript 运行时，通过 CDP 协议提供 Puppeteer/Playwright 兼容接口。端到端对比测试表明：

- **性能**：动态页面加载速度比 Scrapling fetch 快 2-3.5x（HN: 1.38s vs 4.79s）
- **内存**：空闲 RSS ~8MB，远低于 Playwright 的 200MB+
- **JS 渲染**：V8 引擎支持 ES 模块、async/await、fetch API、事件循环
- **Stealth**：内置 TLS 指纹伪装（wreq Chrome 145）和 3,520 域名 tracker 拦截
- **CDP 兼容**：直接兼容 Puppeteer/Playwright 连接
- **特色能力**：内置 DOM→Markdown 转换（`LP.getMarkdown`）、robots.txt 合规、并行抓取框架

将其作为正式引擎接入 chrome-agent，可填补效率断层并降低常见动态页面的抓取成本。

## 范围边界

**范围内：**

- 创建 `obscura-fetch-contract` 引擎契约 spec
- 在 `configs/engine-registry.json` 注册 `obscura-fetch` 引擎条目
- 更新 `engine-registry` spec 新增 `cdp_lightweight` 引擎类型
- 更新 `engine-contracts` spec 反映 obscura-fetch 在引擎选择策略中的定位
- 端到端 smoke-check 证据：执行并记录对比测试结果
- 决策记录：`docs/decisions/2026-05-02-obscura-engine-addition.md`
- 安装脚本或 preflight playbook 更新（优先复用预编译二进制）

**范围外（v1）：**

- 不替代 `scrapling-get`：静态页面仍由纯 HTTP 引擎处理
- 不替代 `scrapling-stealthy-fetch`：Obscura stealth 是 TLS 层伪装，高保护页面仍需完整 Playwright stealth
- 不替代 `chrome-devtools-mcp` / `chrome-cdp`：诊断和实时会话能力不在 obscura-fetch 范围
- 不实现 `obscura scrape` 并行模式集成（需额外 worker binary 构建，延后考虑）
- 不在本 change 中修改站点策略库的 `engine_priority`（待引擎验证后单独处理）

## Capabilities

### New Capabilities

- `obscura-fetch-contract`: 定义 obscura-fetch 引擎的输入/输出/错误契约、适用场景与 smoke-check 验证标准

### Modified Capabilities

- `engine-registry`: 新增 `cdp_lightweight` 引擎类型定义；新增 `obscura-fetch` 引擎条目及其特性评分
- `engine-contracts`: 更新引擎选择策略，在 scrapling-get 和 scrapling-fetch 之间加入 obscura-fetch 作为轻量 JS 渲染中间层

## Capabilities 待确认项

- [x] 能力清单已与用户确认（基于对比测试报告协商一致）
- [x] 引擎 ID 命名 `obscura-fetch` 已确认，符合 `<tool-prefix>-<capability>` 规范
- [ ] `cdp_lightweight` 类型名称是否准确描述 obscura-fetch 定位（备选：`headless_rust`、`v8_browser`）— 待 design 阶段确认

## Impact

**正面影响：**

- 动态页面抓取效率提升 2-3.5x，内存占用降低 10x+
- 新增内置能力：robots.txt 合规、CDP native 的 DOM→MD 转换
- 扩展引擎类型体系，为后续类似轻量引擎接入提供 precedent

**风险：**

- Obscura v0.1.0 成熟度较低，需跟踪上游 stability
- CDP 实现是子集，特定 Playwright API 可能不兼容
- Stealth 模式的实际反检测广度待更多站点验证
- 预编译二进制版本固定与安装链需明确策略

**对现有引擎的影响：**

- `scrapling-fetch` 和 `scrapling-stealthy-fetch` 的 default_rank 向后顺移
- 引擎选择映射中新增中间层路由逻辑

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
  - `project_page_ref`: `repo://chrome-agent/AGENTS.md`
  - `writeback_targets`: `AGENTS.md`, `docs/governance-and-capability-plan.md`, `docs/decisions/`
