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
| **diagnose** | Chrome DevTools 结构化诊断 | 调试/证据收集 |
| **crawl** (规划中) | 多页面遍历与批量抓取 | 批量采集 |

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
# 1. 先做 Scrapling CLI preflight（必要时会安装受管环境）
./scripts/scrapling-cli.sh preflight

# 2. 当前 shell 需要变量时，应用 export 语句
eval "$(./scripts/scrapling-cli.sh shellenv)"

# 3. 获取网页内容
"$SCRAPLING_CLI_PATH" extract get https://example.com outputs/example.md

# 4. 查看完整工作流
cat AGENTS.md
```

默认契约：

- `SCRAPLING_CLI_PATH` 是本仓库识别 Scrapling CLI 的唯一环境变量
- 默认受管安装位置是 `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`
- 不需要修改受 git 跟踪文件来适配本机用户名

如需把环境变量持久化到 `/Users/nantas-agent/.zshenv`，必须先显式确认，再运行：

```bash
./scripts/scrapling-cli.sh persist-zshenv
```

## 工作流

本仓库定义了两种操作路径：

- **Content Retrieval（默认）**: 快速获取页面内容，Scrapling-first，轻量验证
- **Platform Analysis（按需）**: 深度页面分析，fallback 到 DevTools，完整证据收集

无论走哪条以 Scrapling 为起点的路径，都先执行 Scrapling CLI preflight；CLI 不可用时先安装保障，再继续 fetcher 选择。

路由规则和切换条件详见 `AGENTS.md`。

## 路线图

项目规划了 5 个阶段来从当前状态演进到完整服务架构：

```
Phase 1: 治理基础重建  →  Phase 2: 契约冻结  →  Phase 4: 引擎扩展治理  →  Phase 5: 安装链与清理闭环
                                          ↘  Phase 3: 策略库标准化 ↗
```

详见[总体规划文档](docs/governance-and-capability-plan.md#4-阶段划分)。

## 相关资源

- [总体规划文档](docs/governance-and-capability-plan.md)
- [治理文档（AGENTS.md）](AGENTS.md)
- [决策记录](docs/decisions/)
- [操作手册](docs/playbooks/)
