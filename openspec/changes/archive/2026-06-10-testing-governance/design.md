# Design

## Context

chrome-agent 的测试现状是碎片化的：51 个 Python 源模块中仅 6 个有测试，使用了 `unittest` 和 `pytest` 两种框架，无统一目录约定或运行入口。最近一次交付（cdp-cache-pipeline-tooling，5 个新模块）交付了零测试，且 openspec verification 未将其标记为问题。

本次 change 建立测试治理体系：统一目录结构和框架，新增站点样本回归机制，将测试义务嵌入 AGENTS.md 硬约束和 openspec verification 流程。

## Goals / Non-Goals

**Goals:**
- 建立顶层 `tests/` 目录结构，统一使用 `unittest`
- 实现 `scripts/test_runner.py` 统一入口，支持 stdlib discover 和站点样本回归
- 实现站点样本回归机制（I2 动态 TestCase 生成 + golden diff + 结构断言）
- 在 `strategy.md` frontmatter 中新增 `samples` 字段
- 将测试义务写入 AGENTS.md C9 硬约束
- 将测试完备检查嵌入 openspec verification（J3 分级）

**Non-Goals:**
- 不做 CI/CD 集成（后续 change）
- 不接入覆盖率工具（后续 change）
- 不迁移旧测试文件（`scripts/pipeline/tests/` 保留原位）
- 不补齐 `scripts/explore/` 的全部测试（按需后续）
- 不设计断言 DSL 或策略级自定义断言

## Decisions

### D1: 顶层 `tests/` 目录 + 站点数据跟策略走

**决策**: 通用代码测试放 `tests/`（Python 社区标准），站点 golden files 放 `sites/strategies/<domain>/samples/`（跟策略绑定）。

**理由**: 删策略时 golden files 一起删；测试逻辑是通用的，不需要每个站点一份 test code。

### D2: 纯 `unittest`，I2 动态 TestCase

**决策**: 所有测试用 `unittest.TestCase`。站点样本回归通过 `scripts/test_runner.py` 扫描策略目录，为每个 `(domain, page)` 动态生成独立的 `TestCase` 类。

**理由**: AGENTS.md C5 禁止第三方测试依赖。I2 比 `subTest` 报告更清晰（每个样本独立 pass/fail）。

### D3: E3 分层验证

**决策**: 日常跑结构断言守底线（`no_raw_html_tags`、`links_resolved`、`valid_md_tables`）；有意改动输出时用 `--update-golden` 刷新 golden file，golden diff 确认变更范围。

**理由**: golden exact match 太脆弱（格式微调全 fail），纯断言太宽松（漏内容不 catch）。分层兼顾稳定性和灵敏度。

### D4: 样本清单在 frontmatter，断言在测试代码

**决策**: `strategy.md` frontmatter 只声明 `samples`（page + label），不含断言规则。断言由测试代码内置。

**理由**: 策略管"测什么"，测试代码管"怎么验证"。90% 站点用同一套断言，不需要策略级自定义。

### D5: J3 分级嵌入 verification

**决策**: openspec verification 增加测试完备检查：
- 新增模块无测试 → CRITICAL（阻塞归档）
- 已有模块修改未更新测试 → WARNING（建议修复）

**理由**: 新代码无测试不可接受；但已有模块的微小修改（日志格式等）强求更新测试碍事。

### D6: 旧测试保留不迁移

**决策**: `scripts/pipeline/tests/` 下的 6 个现有测试保留原位，不迁移到 `tests/`。仅清理 `pytest` 导入（迁移到 `unittest`）。

**理由**: 避免一次性大迁移带来的回归风险。新测试统一放 `tests/`，旧测试自然淘汰。

## Risks / Migration

| 风险 | 影响 | 缓解 |
|------|------|------|
| golden file 膨胀 | 大型站点可能有大量 golden files | 每个站点 3-5 个样本即可覆盖结构性差异；golden file 是 MD 文本，git 友好 |
| I2 动态 TestCase 调试困难 | 堆栈不指向具体文件 | runner 输出 `(domain, page)` 标识，golden diff 提供精确变更上下文 |
| `pytest` 清理引入回归 | `test_table_grid.py` 使用 pytest fixture | 转换为 `unittest.TestCase` + `setUp` 方法，逐个断言验证 |
| verification 检查误报 | 修改 5 行注释被标记为 WARNING | J3 分级：WARNING 不阻塞归档，只提醒 |
