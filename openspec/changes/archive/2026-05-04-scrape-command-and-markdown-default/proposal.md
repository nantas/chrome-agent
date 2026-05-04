# Proposal

## 问题定义

当前 `chrome-agent crawl` 有两个结构性问题：

1. **Crawl 的默认输出是原始 HTML**。用户需要额外转换才能得到 Markdown，而 `fetch` 已验证通过 `--ai-targeted` 直接产出高质量 Markdown。Crawl 和 fetch 的产出格式不统一，造成工作流断裂。

2. **Crawl 强制依赖站点策略（site-strategy）**。对于结构简单的站点（如 MediaWiki wiki、静态文档站），策略引导的遍历是过度设计——用户只需要"给一个 URL，帮我递归抓取所有同域页面"。当前"无策略就拒绝执行"的行为与 `crawl` 这个词暗示的"自发现式爬取"心智模型不符，造成认知落差和使用门槛。

这两个问题的交集是：用户需要一个**开箱即用、默认输出 Markdown、无需策略**的递归爬取命令。`crawl` 应保持其策略引导的精准遍历定位，新增一个独立命令来填补"无脑式爬取"的空位。

## 范围边界

**范围内：**
- 新增 `scrape` 命令（策略无关递归爬取）
- 将 `crawl` 默认输出从 HTML 改为 Markdown
- 提取可复用的 Markdown 转换管线（供 `crawl` 和 `scrape` 共享）
- CLI 参数面扩展（`--no-markdown`、`--merge`、`--concurrency`）
- 并发 Phase 2 Markdown 转换（`Promise.all` + limit pool）

**范围外：**
- 修改 Scrapling 本身（仅复用现有 `--ai-targeted` 能力）
- 新增 HTML→Markdown 本地转换工具（不使用 pandoc/turndown 等）
- 修改站点策略 schema 或策略引导逻辑
- 认证会话复用（保持现有规则不变）

## Capabilities

### New Capabilities
- `scrape-command`: 无需站点策略的递归网页爬取能力，通过全量 `<a href>` 提取 + `same-domain` / URL pattern 过滤实现自发现式遍历，默认输出 Markdown
- `markdown-conversion-pipeline`: 共享的 HTML 中间产物到 Markdown 最终产物的转换管线，支持并发 re-fetch（`--ai-targeted`）、失败隔离、可选 merge、HTML 中间产物自动清理

### Modified Capabilities
- `strategy-guided-crawl`: 默认输出格式从原始 HTML 改为 Markdown；新增 `--no-markdown` 回退开关、`--merge` 合并开关、`--concurrency` 并发数控制
- `global-capability-cli`: CLI 命令面新增 `scrape` 命令；`crawl` 命令参数面扩展（`--no-markdown`、`--merge`、`--concurrency`）

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

| 层面 | 影响 |
|------|------|
| CLI 命令面 | 新增 `scrape`；`crawl` 默认输出格式变化（Breaking Change，但 HTML 可通过 `--no-markdown` 恢复） |
| 用户工作流 | `chrome-agent crawl` 用户无需额外转换即可获得 Markdown；新用户可通过 `scrape` 零配置批量抓取 |
| 产物生命周期 | `outputs/` 下的 `crawl` / `scrape` 运行目录中不再保留 `.html` 文件（中间产物自动清理），仅保留 `.md` |
| 引擎调用 | `crawl` / `scrape` 均变为两阶段：Phase 1（HTML traversal）+ Phase 2（Markdown conversion），Phase 2 并发调用 Scrapling |
| 规范层面 | 新增 `scrape-command` 和 `markdown-conversion-pipeline` spec；修改 `strategy-guided-crawl` 和 `global-capability-cli` spec |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos`
  - `project_page_ref`: `repo://chrome-agent/AGENTS.md`
  - `writeback_targets`: `AGENTS.md`、`openspec/specs/global-capability-cli/spec.md`、`openspec/specs/strategy-guided-crawl/spec.md`、新增 `openspec/specs/scrape-command/spec.md`、新增 `openspec/specs/markdown-conversion-pipeline/spec.md`
