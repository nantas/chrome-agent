# Proposal

## 问题定义

chrome-agent 仓库目前缺乏系统性的单元测试治理，导致三个具体问题：

1. **测试覆盖不均**：51 个 Python 源模块中仅 6 个有测试文件，名义覆盖率约 2%。新增模块（如 cdp-cache-pipeline-tooling 的 5 个模块）交付时零测试。

2. **测试标准不一致**：现有测试中 5 个使用 `unittest`、1 个使用 `pytest`，无统一 runner 配置，测试文件散落在 `scripts/pipeline/tests/` 无归属约定。AGENTS.md C5 声明"Python 用 unittest"但未强制执行。

3. **站点策略修改无法自动验证**：修改管线代码或站点策略后，无法秒级验证已爬取页面的转换结果未回归。当前依赖手动重跑管线或 ad-hoc 脚本（如 `/tmp/nintendo-rebuild/`），既不可重复也无法纳入 openspec verification 流程。

## 范围边界

**In scope**：
- 统一测试目录结构（`tests/` 顶层目录，按源码模块分组）
- 统一测试框架为 `unittest`（清理 `pytest` 残留）
- 通用测试入口 `scripts/test_runner.py`（stdlib discover + 站点样本回归）
- 站点样本回归机制：从 `.cache/` 读取 → 转换 → golden diff，runner 扫描策略动态生成 TestCase（I2）
- 站点策略 frontmatter 新增 `samples` 字段
- 通用结构断言规则集（`no_raw_html_tags`、`links_resolved`、`valid_md_tables`）
- AGENTS.md 新增 C9 测试义务硬约束
- openspec verification 流程增加测试完备检查（J3 分级：新增模块无测试 = CRITICAL，已有模块修改未更新测试 = WARNING）
- `docs/architecture/08-tech-stack.md` §4 重写
- `docs/architecture/03-strategy-schema.md` 新增 `samples` 字段

**Out of scope**：
- CI/CD 集成（后续 change）
- 覆盖率工具（`coverage.py` 等）接入（后续 change）
- `scripts/explore/` 模块的测试补齐（可按需在后续 change 中进行）
- 全量端到端测试（C 层，手动执行，不在自动化测试体系内）
- 现有 `scripts/pipeline/tests/` 的迁移（新测试统一放 `tests/`，旧测试保留不迁移）

## Capabilities

### New Capabilities
- `test-runner`: 统一测试入口，支持 stdlib discover（通用代码测试）和站点样本回归（I2 动态 TestCase 生成），提供 `site-samples` / `all` 子命令
- `golden-diff`: 站点样本 golden file 对比机制，支持 `--update-golden` 刷新，结构断言规则集作为 baseline 验证
- `sample-discovery`: 从站点策略 frontmatter `samples` 字段提取样本清单，配合 `.cache/` 数据驱动站点级回归测试

### Modified Capabilities
- `explore-scaffold`: scaffold 生成流程新增样本选取步骤——agent 根据页面数据结构特性挑选代表性样本，用户确认后写入 `samples` frontmatter
- `pipeline-fetch`: 新增样本页面 fetch 子流程——按策略 `samples` 清单从 `.cache/` 提取或首次获取样本页面，存入标准缓存路径
- `strategy-schema`: frontmatter 新增 `samples` 字段（page + label），由 explore agent 生成并经用户确认

## Capabilities 待确认项

- [x] 能力清单已确认——来自 grill session 的逐项决策
- [x] 验证标准 E3 分层已确认
- [x] 目录结构 H3 已确认
- [x] 站点测试实现 I2 已确认
- [x] Verification 严重级别 J3 已确认

## Impact

| 影响面 | 说明 |
|--------|------|
| `tests/` | 新建顶层目录，含 `__init__.py`、`lib/`、`pipeline/` 子目录 |
| `scripts/test_runner.py` | 新增统一测试入口 |
| `sites/strategies/<domain>/samples/` | 新增 golden file 目录（按需，explore 时创建） |
| `sites/strategies/<domain>/strategy.md` | frontmatter 新增 `samples` 字段 |
| `AGENTS.md` §0.5 | C5 扩展 + C9 新增 |
| `AGENTS.md` §9 | 新增索引条目 |
| `AGENTS.md` §11 | 新增测试任务必读表 |
| `docs/architecture/08-tech-stack.md` §4 | 重写 |
| `docs/architecture/03-strategy-schema.md` | 新增字段 |
| `scripts/pipeline/tests/test_table_grid.py` | 清理 `pytest` 导入，迁移到 `unittest` |
| openspec verification | 增加测试完备检查逻辑 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 binding.md 回写目标章节
