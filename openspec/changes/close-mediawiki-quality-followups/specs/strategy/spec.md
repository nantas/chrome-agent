# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy`
- 来源: `proposal.md` / 用户确认 4-capability 划分（本会话交互确认）。
- 变更类型: modified
- 用户确认摘要: 按清单生成 4 个 spec delta（extract-kernel / pipeline-convert-phase / pipeline / strategy）。

## 规范真源声明

本文件是该 capability 在本次 change 中的行为规范真源；design/tasks/verification 必须引用本文件，页面回写不得替代 spec delta。

## MODIFIED Requirements

### Requirement: growagarden-strategy-frozen-artifacts
`sites/strategies/growagarden.fandom.com/` 的冻结产物 SHALL 进版本管理并保持自洽：`strategy.md`（`content_acquisition: html_rendered`、tabber 去重 `cleanup_selectors`、`infobox.enabled`）、`samples/Crops.{html.gz,md,source.json}` golden 三件套、`freeze-report.json`，以及 `registry.json` 中对应条目。策略 extraction 块 SHALL 通过 `validate_extraction`（无 dead key、无形状错误）。

golden 更新 SHALL 是有意变更的产物：tabber 面板收敛为首个含表面板（`All` 超集），无实体行丢失，且其余域 site-samples 回归通过。

#### Scenario: strategy-passes-schema
- **WHEN** 对冻结后的 growagarden `strategy.md` 运行 extraction schema 校验
- **THEN** 结果 SHALL 为空（无 dead config、无形状错误）

#### Scenario: golden-regression-green
- **WHEN** 运行 `python3 scripts/test_runner.py site-samples --domain growagarden.fandom.com`
- **THEN** 全部 sample SHALL 通过（golden 与结构断言）

## ADDED Requirements

### Requirement: mobalytics-strategy-intake
`sites/strategies/mobalytics.gg/`（`strategy.md` + `freeze-report.json`）与 `registry.json` 中对应条目 SHALL 一并进版本管理，registry 引用不得指向未跟踪目录。该策略为外部任务的冻结产物，本 change 只做收编，不修改其内容。

#### Scenario: registry-reference-resolved
- **WHEN** `registry.json` 含 `"domain": "mobalytics.gg"` 条目
- **THEN** 其 `file` 字段指向的 `sites/strategies/mobalytics.gg/strategy.md` SHALL 存在于版本管理中

#### Scenario: strategy-content-untouched
- **WHEN** 收编提交落地
- **THEN** mobalytics 策略与 freeze-report 内容 SHALL 与工作区冻结时逐字节一致
