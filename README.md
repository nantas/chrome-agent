# chrome-agent

跨仓库网页抓取服务（cross-repo web scraping service）—— 提供标准化、可复用的网页内容获取流程。

## 身份定位

chrome-agent 是一个专注于网页抓取与内容获取的工作仓库，区别于通用的浏览器调试工具仓库。其核心职责是：

- 通过 Scrapling-first 流程获取静态/动态/受保护页面的内容
- 在需要结构化诊断证据时 fallback 到浏览器 DevTools
- 在已验证的实时会话上做延续性操作
- 积累可复用的站点经验、操作手册和抓取报告

## 能力总览

| 能力 | 说明 | 场景 |
|------|------|------|
| **explore** | 分析目标页面结构、交互模式、反爬机制 | 抓取前调研 |
| **fetch** | 获取页面内容（静态/动态/受保护） | 内容获取 |
| **crawl** | 基于 strategy 的受边界多页面遍历与批量抓取 | 批量采集 |
| **doctor** | 检查全局 launcher、repo 解析、运行前依赖 | 安装/自检 |
| **clean** | 清理 disposable outputs，默认保留 durable reports | 产物维护 |

详见[总体规划文档](docs/governance-and-capability-plan.md#3-能力全景图)的能力全景图。

## 目录结构

```
.
├── AGENTS.md           # [本文件] 治理文档——服务身份、能力契约框架、治理规则
├── openspec/           # 规范驱动的变更管理
│   ├── changes/        #   进行中的变更
│   └── specs/          #   已冻结的规范
├── docs/
│   ├── decisions/      # 技术决策记录
│   ├── playbooks/      # 操作手册
│   ├── plans/          # 实现规划
│   └── setup/          # 环境配置
├── reports/            # 执行报告与证据
├── skills/             # 全局 skill 源码
├── sites/              # 站点特定经验
├── configs/            # 工具与运行配置
├── scripts/            # 辅助脚本
└── outputs/            # 抓取产出暂存（.gitignore）
```

## Quick Start

```bash
# 1. 安装全局 chrome-agent launcher（runtime -> ~/.agents/scripts, shim -> ~/.local/bin）
./scripts/install-chrome-agent-cli.sh

# 2. 检查 launcher、repo 解析与 Scrapling readiness
chrome-agent doctor

# 3. 获取网页内容
chrome-agent fetch https://example.com --format json

# 4. 策略覆盖与有界 crawl
chrome-agent explore https://example.com
chrome-agent crawl https://www.fanbox.cc/@atdfb/posts --max-pages 2
```

默认契约：

- `chrome-agent` 是正式的全局外部入口
- repo 解析优先级是 `--repo` override → `repo://chrome-agent` → `CHROME_AGENT_REPO` fallback
- CLI 返回 JSON-first 结果；文本模式只是同一语义结果的渲染层
- `SCRAPLING_CLI_PATH` 是本仓库识别 Scrapling CLI 的唯一环境变量
- 默认受管安装位置是 `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`
- 不需要修改受 git 跟踪文件来适配本机用户名
- `explore` 默认产出 durable `reports/`；`fetch`/`crawl` 默认不产出 durable report，可通过 `--report` 显式开启

## 工作流

本仓库定义了两种操作路径：

- **Content Retrieval（默认）**: 快速获取页面内容，Scrapling-first，轻量验证
- **Platform Analysis（按需）**: 深度页面分析，fallback 到 DevTools，完整证据收集

无论走哪条以 Scrapling 为起点的路径，都先执行 Scrapling CLI preflight；CLI 不可用时先安装保障，再继续 fetcher 选择。

路由规则和切换条件详见 `AGENTS.md`。

## 全局 CLI

`chrome-agent` 是一个 thin launcher：

- runtime script 安装到 `~/.agents/scripts/chrome-agent.mjs`
- user-facing shim 安装到 PATH 可见目录，默认 `~/.local/bin/chrome-agent`
- 真实行为仍在仓库内 `scripts/chrome-agent-cli.mjs` 执行
- `doctor` 负责 launcher、repo 解析、仓库形态与 Scrapling readiness 检查
- `clean` 默认只清理 `outputs/` 下的 disposable run artifacts

安装、迁移与常见 remediation 见 `docs/playbooks/chrome-agent-global-install.md`。

## 路线图

项目规划了 5 个阶段来从当前状态演进到完整服务架构：

```
Phase 1: 治理基础重建  →  Phase 2: 契约冻结  →  Phase 4: 引擎扩展治理  →  Phase 5: 全局 Capability CLI
                                          ↘  Phase 3: 策略库标准化 ↗
```

详见[总体规划文档](docs/governance-and-capability-plan.md#4-阶段划分)。

## 相关资源

- [总体规划文档](docs/governance-and-capability-plan.md)
- [治理文档（AGENTS.md）](AGENTS.md)
- [决策记录](docs/decisions/)
- [操作手册](docs/playbooks/)
