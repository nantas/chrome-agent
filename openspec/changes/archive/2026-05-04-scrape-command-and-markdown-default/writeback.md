# Writeback

## 回写目标

| 文件 | 变更类型 | 内容摘要 |
|------|---------|---------|
| `AGENTS.md` | 修改 | §2 能力框架表格新增 `scrape` 条目，更新 `crawl` 描述 |
| `openspec/specs/global-capability-cli/spec.md` | 修改 | 命令面新增 `scrape`，参数面扩展 `--no-markdown`/`--merge`/`--concurrency` |
| `openspec/specs/strategy-guided-crawl/spec.md` | 修改 | 默认输出从 HTML 改为 Markdown，新增 `--no-markdown`/`--merge`/`--concurrency` |
| `openspec/specs/scrape-command/spec.md` | 新增 | scrape 命令完整行为规范（冻结） |
| `openspec/specs/markdown-conversion-pipeline/spec.md` | 新增 | 共享 Markdown 转换管线规范（冻结） |

## 执行记录

- **执行人**: chrome-agent implementation
- **执行时间**: 2026-05-04
- **执行结果**: 全部完成

## AGENTS.md 变更

在 §2 能力框架表格中：

1. 新增 `scrape` 能力：
   | **scrape** | 策略无关递归爬取，默认输出 Markdown | 已实现 |

2. 更新 `crawl` 描述：
   | **crawl** | 策略引导有界遍历，默认输出 Markdown | 已验证 |

## Spec 冻结

所有 spec 文件从 `openspec/changes/scrape-command-and-markdown-default/specs/` 复制到 `openspec/specs/`：

- `openspec/specs/scrape-command/spec.md` — 新增
- `openspec/specs/markdown-conversion-pipeline/spec.md` — 新增
- `openspec/specs/global-capability-cli/spec.md` — 覆盖更新
- `openspec/specs/strategy-guided-crawl/spec.md` — 覆盖更新

## 归档

本 change 归档至 `openspec/changes/archive/2026-05-04-scrape-command-and-markdown-default/`。
