# Specification Delta

## Capability 对齐（已确认）

- Capability: `redirect-detection`
- 来源: `proposal.md` — New Capability
- 变更类型: `new`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: redirect-page-detection

convert 阶段 SHALL 检测 fetched HTML 中的 wiki 重定向标记。当 `rendered_html` 包含 `<div class="redirectMsg">` 或等价重定向标记时，SHALL 将该页面标记为 redirect 页面。

#### Scenario: detect-mw-redirect

- **WHEN** 页面的 `rendered_html` 包含 `redirectMsg` class 或 "Redirect to:" 文本
- **THEN** convert 阶段 SHALL 提取重定向目标页面标题
- **AND** SHALL 标记该页面状态为 `redirect`

### Requirement: redirect-page-skip-output

被标记为 redirect 的页面 SHALL NOT 生成 .md 输出文件。

#### Scenario: skip-redirect-page-file

- **WHEN** 页面被标记为 redirect，重定向目标为 `Items`
- **THEN** 系统 SHALL NOT 在 output 目录中为该页面创建 .md 文件
- **AND** SHALL 在 pipeline state 中记录 redirect 映射：`{source_title, target_title, status: "redirect"}`

#### Scenario: redirect-stats-reported

- **WHEN** convert 阶段完成
- **THEN** 日志 SHALL 报告 redirect 跳过数量
- **AND** `extraction_results.json` 中 SHALL 包含 `redirect_count` 统计字段

### Requirement: redirect-source-link-resolution

其他页面中指向 redirect 源页面的链接 SHALL 被解析为指向 redirect 目标页面（如果目标在 manifest 中）或原始 wiki URL（如果目标不在 manifest 中）。

#### Scenario: link-to-redirect-page-resolved-to-target

- **WHEN** 页面 A 包含 `[[Item]]` 链接，且 `Item` 是重定向到 `Items` 的 redirect 页面
- **AND** `Items` 在 manifest 中存在
- **THEN** 链接 SHALL 解析为 `[Item](../items/index.md)`（指向 Items 的相对路径）

#### Scenario: link-to-redirect-page-target-not-in-manifest

- **WHEN** 页面 A 包含 `[[Item]]` 链接，且 `Item` 是重定向到 `Items` 的 redirect 页面
- **AND** `Items` 不在 manifest 中
- **THEN** 链接 SHALL 解析为 `[Item](https://domain/wiki/Items)`（原始 wiki URL）
