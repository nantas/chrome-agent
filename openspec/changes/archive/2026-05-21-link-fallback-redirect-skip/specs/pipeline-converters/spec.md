# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-converters`
- 来源: `proposal.md` — Modified Capability（新增 redirect 检测逻辑）
- 变更类型: `modified`
- 既有 spec: `openspec/specs/pipeline-converters/spec.md`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源（delta）
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: redirect-html-detection-before-convert

`HtmlToMarkdownConverter` 或 convert phase SHALL 在执行 HTML→Markdown 转换前检测 `rendered_html` 中的重定向标记。当检测到 `<div class="redirectMsg">` 时，SHALL 跳过该页面的 convert 步骤，不产生 Markdown 内容。

#### Scenario: redirect-page-produces-no-content

- **WHEN** convert phase 处理一个页面，其 `rendered_html` 包含 `<div class="redirectMsg">`
- **THEN** SHALL NOT 调用 `convert_single_page()` 或等价转换方法
- **AND** SHALL 将该页面在 pipeline state 中标记为 `status: "redirect"`
- **AND** SHALL NOT 在 output 目录中生成对应的 .md 文件
- **AND** SHALL 提取重定向目标标题并存储在 pipeline state 中

#### Scenario: normal-page-unaffected-by-redirect-check

- **WHEN** convert phase 处理一个页面，其 `rendered_html` 不包含重定向标记
- **THEN** SHALL 正常执行 HTML→Markdown 转换，行为与变更前完全一致
