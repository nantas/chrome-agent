# Verification

## 验证结论

本次变更的 39 项任务全部完成。重构后的 `scripts/mediawiki-api-extract/` 多文件包通过 balatro 全站回归验证：468 页面、17 目录的输出与重构前单体脚本逐文件一致（`diff -r --exclude='*.json'` 零差异）。

## Spec-to-Implementation Coverage

| Requirement | Spec 文件 | 实现位置 | 验证方式 |
|-------------|-----------|----------|----------|
| Capabilities 受控词汇表 | `specs/mediawiki-api-extraction/spec.md` | `pipeline.py`: `validate_api_config` 使用策略 `required_capabilities` 并集 | 代码审查 + 回归测试 |
| DiscoveryStrategy 接口契约 | `specs/mediawiki-api-extraction/spec.md` | `strategies.py`: `DiscoveryStrategy` Protocol + `AllPagesDiscoveryStrategy` | 代码审查 + 回归测试 |
| ContentAcquisitionStrategy 接口契约 | `specs/mediawiki-api-extraction/spec.md` | `strategies.py`: `ContentAcquisitionStrategy` Protocol + `WikitextOnlyAcquisitionStrategy` | 代码审查 + 回归测试 |
| LinkResolver 接口契约 | `specs/mediawiki-api-extraction/spec.md` | `strategies.py`: `LinkResolver` Protocol + `ExactTitleLinkResolver` | 代码审查 + 回归测试 |
| TemplateProcessor 接口契约 | `specs/mediawiki-api-extraction/spec.md` | `strategies.py`: `TemplateProcessor` Protocol + `SimpleSubstitutionTemplateProcessor` | 代码审查 + 回归测试 |
| ListPageAssembler 接口契约 | `specs/mediawiki-api-extraction/spec.md` | `strategies.py`: `ListPageAssembler` Protocol + `FrontmatterDrivenListPageAssembler` | 代码审查 + 回归测试 |
| Pipeline 策略注入 | `specs/mediawiki-api-extraction/spec.md` | `pipeline.py`: `build_pipeline()` + `PipelineStrategies` dataclass | 代码审查 + 回归测试 |
| Namespace 策略化 | `specs/mediawiki-api-extraction/spec.md` | `strategies.py`: `AllPagesDiscoveryStrategy.discover_pages()` 读取 `strategy.api.namespace` | 代码审查 + 回归测试 |
| 管线核心流程与策略挂载点 | `specs/mediawiki-api-extraction/spec.md` | `phase_a.py`, `phase_b.py`, `phase_c.py`: 每 Phase 接受策略对象参数 | 代码审查 + 回归测试 |
| content_profile 字段定义 | `specs/mediawiki-site-strategy/spec.md` | `pipeline.py`: `build_pipeline()` 解析 `api.content_profile` | 代码审查 + 回归测试 |
| capabilities 字段引用 | `specs/mediawiki-site-strategy/spec.md` | `pipeline.py`: `validate_api_config()` 对比策略并集与声明 capabilities | 代码审查 + 回归测试 |

## Task-to-Evidence Coverage

| 任务阶段 | 关键证据 | 结果 |
|----------|----------|------|
| 1.1–1.3 基线建立 | `/tmp/mw-baseline/`（已清理）| 468 页面，17 目录，0 失败 |
| 2.1–2.8 模块拆分 | `scripts/mediawiki-api-extract/*.py`（7 个文件）| 全部创建，无语法错误 |
| 3.1 策略文件更新 | `sites/strategies/balatrowiki.org/strategy.md` | 已追加 `api.content_profile` |
| 4.1–4.3 回归验证 | `/tmp/mw-refactored2/`（已清理）| `diff -r --exclude='*.json'` 零差异 |
| 5.1–5.3 清理收尾 | `--help` 输出、原文件删除确认 | 全部通过 |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
|----------|--------------|----------------------|
| 重构后源码 | `scripts/mediawiki-api-extract/` | 全部 implementation tasks |
| 回归 diff | `diff -r /tmp/mw-baseline /tmp/mw-refactored2 --exclude='*.json'` 零差异 | Task 4.1–4.3 |
| 策略文件更新 | `sites/strategies/balatrowiki.org/strategy.md` | Task 3.1 |
| CLI 验证 | `python -m scripts.mediawiki-api-extract --help` 输出完整 | Task 5.1 |

## 缺口与阻塞项

无。所有 spec requirement 均有实现覆盖，所有 task 均有执行证据，回归验证通过。
