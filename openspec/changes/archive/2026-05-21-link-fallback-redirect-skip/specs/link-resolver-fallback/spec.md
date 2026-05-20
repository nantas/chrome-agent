# Specification Delta

## Capability 对齐（已确认）

- Capability: `link-resolver-fallback`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 涉及实现: `ExactTitleLinkResolver`, `ShortNameLinkResolver`

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源（delta）
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: unresolved-link-fallback-to-wiki-url

`LinkResolver.resolve()` 的 fallback 行为 SHALL 从生成裸 `.md` 相对路径变更为生成原始 wiki URL。当 target 不在 manifest pages 中时（即所有查找策略均未匹配），`resolve()` SHALL 返回 `[display](https://{domain}/wiki/{target_slug})`，其中 `target_slug` 为 target 中空格替换为下划线后的值。

此行为 SHALL 同时应用于 `ExactTitleLinkResolver` 和 `ShortNameLinkResolver`。

#### Scenario: exact-title-resolver-fallback-to-wiki-url

- **WHEN** `ExactTitleLinkResolver.resolve()` 处理 target "Ending 16"
- **AND** "Ending 16" 不在 manifest pages 的 title 集合中
- **THEN** SHALL 返回 `[Ending 16](https://bindingofisaacrebirth.wiki.gg/wiki/Ending_16)`

#### Scenario: short-name-resolver-fallback-to-wiki-url

- **WHEN** `ShortNameLinkResolver.resolve()` 处理 target "SomePage"
- **AND** exact title 查找、short name 查找、namespace suffix 查找均未匹配
- **THEN** SHALL 返回 `[SomePage](https://{domain}/wiki/SomePage)`

#### Scenario: manifest-match-still-produces-relative-path

- **WHEN** target 在 manifest 中找到匹配页面
- **THEN** SHALL 继续返回相对 .md 路径，行为与变更前一致

#### Scenario: namespace-prefixed-target-fallback

- **WHEN** target 以 `File:` 开头
- **THEN** SHALL 继续走已有的 File namespace 处理逻辑，不受本变更影响

#### Scenario: domain-from-constructor

- **WHEN** `LinkResolver.__init__(domain="bindingofisaacrebirth.wiki.gg")` 构造实例
- **AND** 触发 fallback
- **THEN** fallback URL SHALL 使用构造时传入的 domain
