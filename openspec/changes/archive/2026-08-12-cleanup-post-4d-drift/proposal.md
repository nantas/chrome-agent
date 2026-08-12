# Proposal

## 问题定义

4d 重构（Stage 1-3）完成后残留三处声明与现实漂移：

1. `scripts/pipeline/pipeline/discovery_summary.py`（258L）是死模块：全仓零 import，真实的 `discovery_summary.json` 由 `chrome-agent-cli.mjs:4347` 内联 JS 构建。其测试 `scripts/pipeline/tests/test_discovery_summary.py` 测的是手动复制的 180 行副本，测不到任何运行时代码。
2. `openspec/specs/convert/spec.md` 声明 `tests/test_golden_convert.py` 为 B 轴等价证明，但该测试 (a) 缓存缺失即 skip，多数环境空转；(b) 断言的是内核内部 A/B（wrapper vs class，构造上恒等），不是跨路径镜像等价。真正的镜像等价证明已由 `tests/test_convert_equivalence.py` 提供（commit f03376d/ac08bba）。
3. `CONTEXT.md:43` 仍称 `html_to_markdown.py`「计划消解」，该文件已在 unify-html-converter 中删除。

冻结 spec 中的对应 requirement 描述的是已不存在的现实（zombie requirements）。

## 范围边界

**范围内：**
- 删除 `pipeline/discovery_summary.py` + `pipeline/tests/test_discovery_summary.py`
- 删除 `tests/test_golden_convert.py`
- 修正 `CONTEXT.md:43` 过期表述
- spec 回填：convert（等价证明指针）、pipeline-discovery（移除 3 个 zombie requirements）、pipeline-orchestration（移除 discovery_summary 引用）
- 回写 `docs/architecture/01-overview.md` 目录树

**范围外：**
- cli.mjs 内联 summary 逻辑提取为纯函数（属候选 4 的结构工作）
- converter 双入口合并（类/函数分工另行评估）
- 任何运行时行为变更 —— 纯删除 + 文档对齐

## Capabilities

### Modified Capabilities

- `convert`: 等价证明指针从 test_golden_convert.py 改为 test_convert_equivalence.py
- `pipeline-discovery`: 移除 discovery-summary-module / discovery-summary-imports / unit-test-compatibility 三个 zombie requirements
- `pipeline-orchestration`: orchestrator 依赖清单移除 discovery_summary.py

## 成功标准

- 全量单元测试绿（删除后）
- `grep -r discovery_summary scripts/ tests/` 无代码引用残留
- spec 文本与代码现实一致
