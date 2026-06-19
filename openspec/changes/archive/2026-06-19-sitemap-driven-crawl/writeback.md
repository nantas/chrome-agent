# Writeback

## 执行状态

所有回写目标已完成。

## 回写清单

| 目标 | 状态 | 详情 |
|---|---|---|
| `sites/strategies/docs.gameanalytics.com/strategy.md` | ✅ | `discovery: { method: sitemap }` 替换 `api:` 块 |
| `sites/strategies/registry.json` | ✅ | 无需修改 (registry 不含 api/discovery 字段) |
| `docs/architecture/02-pipeline-flow.md` | ✅ | 新增 Sitemap 发现路径描述 |
| `docs/architecture/03-strategy-schema.md` | ✅ | 新增 `discovery` 块 schema 文档 |
| `docs/architecture/04-cli-reference.md` | ✅ | crawl 路由图新增 sitemap 分支 |
| `docs/architecture/06-engine-selection.md` | ✅ | 决策树新增 sitemap discovery 规则 |
| `openspec/changes/crawl-scrapling-pages-scope/` | ✅ | 已删除 (内容吸收进本 change) |

## 验证

- 23/23 JS 单元测试全绿
- Live E2E: discovery 193 pages, extraction 5/5 converted
- Python 测试无新增回归
- 架构文档新增 43 行，删除 11 行 (仅 re-indent)，无语义内容丢失
