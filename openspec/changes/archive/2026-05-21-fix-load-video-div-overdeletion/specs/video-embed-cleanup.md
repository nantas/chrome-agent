# Specification Delta

## Capability 对齐（已确认）

- Capability: `html-clean-video-embeds`（converter 内部行为）
- 来源: `proposal.md`
- 变更类型: modified
- 用户确认摘要: 纯 bug fix，用户确认无能力变更

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件

## MODIFIED Requirements

### Requirement: video-embed-div-cleanup-scope

The system SHALL only decompose YouTube oEmbed fallback divs that are **direct or near-leaf containers** of the "Load video" text, and SHALL NOT decompose ancestor containers (such as `mw-parser-output`) whose deep text includes "Load video" only because of nested child nodes.

#### Scenario: page-with-top-level-video-embed
- **WHEN** a wiki page's root content div (`mw-parser-output`) contains nested YouTube embed components with "Load video" text
- **THEN** only the leaf-level video UI containers (`embedvideo-wrapper`, `embedvideo-consent`, `embedvideo-overlay`, `embedvideo-loader`) are removed; the root content div and all non-video sibling elements remain intact

#### Scenario: page-without-video-embed
- **WHEN** a wiki page has no YouTube embed components
- **THEN** the cleanup loop does not decompose any nodes; behavior is unchanged from current
