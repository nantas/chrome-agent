# Proposal

## 问题定义

`runCrawl()`、`runCrawlMediawikiApi()`、`runCrawlScrapling()`、`runScrape()` 中 `maxPages` 参数有三层硬编码默认值（3 或 10），导致外部调用方无法表达"不限制页面数"的语义。Python pipeline 端已支持 `--max-pages` 缺省时不限制（`default=None`, `if max_pages > 0`），但 JavaScript 端的默认值堵死了这一路径。

具体问题：
- `runCrawl()` L1979: `maxPages = 3`
- `runCrawlMediawikiApi()` L2071: `maxPages = 3`
- `runCrawlScrapling()` L2315: `maxPages = 3`
- `runScrape()` L2753: `maxPages = 10`
- `main()` L3717: `parsed.maxPages ?? 3`，L3739: `parsed.maxPages ?? 10`
- Scrapling while 循环条件 `visited.size < maxPages` 在 maxPages 为 null 时会 NaN 比较失败

## 范围边界

- **范围内**：移除所有 JS 层 `maxPages` 硬编码默认值，统一为 `null` = 不限制；修正所有使用 `maxPages` 的条件判断以正确处理 null 语义
- **范围内**：更新 `cli-interface.md` 规范中关于 `maxPages` 的行为声明
- **范围外**：Python pipeline 侧代码（已正确，无需改动）
- **范围外**：`parseArgs()` 解析逻辑（L88 已是 `null`，无需改动）
- **范围外**：新增 `--max-pages=unlimited` 等新语法（不需要，null 语义已够用）

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `cli`: 移除 `maxPages` 硬编码默认值，统一 `null` = 不限制语义，修正所有条件判断

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

| 调用方式 | 现在 | 改后 |
|----------|------|------|
| CLI `crawl` 不传 `--max-pages` | 限制 3 页 | 不限制 |
| CLI `crawl --max-pages 50` | 限制 50 页 | 不变 |
| CLI `scrape` 不传 `--max-pages` | 限制 10 页 | 不限制 |
| 外部代码不传 `maxPages` | 限制 3 页 | 不限制 |
| 外部代码传 `maxPages: 50` | 限制 50 页 | 不变 |

默认 3/10 是无意义的随机值，移除后行为更合理。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：`openspec/specs/cli/cli-interface.md`
- 已确认项目页：`docs/architecture/04-cli-reference.md`
- 回写目标：上述两文件实现完成后一次性回写
