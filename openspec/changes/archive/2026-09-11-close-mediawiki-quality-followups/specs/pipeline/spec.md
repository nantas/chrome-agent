# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline`
- 来源: `proposal.md` / 用户确认 4-capability 划分（本会话交互确认）。
- 变更类型: modified
- 用户确认摘要: 按清单生成 4 个 spec delta（extract-kernel / pipeline-convert-phase / pipeline / strategy）。

## 规范真源声明

本文件是该 capability 在本次 change 中的行为规范真源；design/tasks/verification 必须引用本文件，页面回写不得替代 spec delta。

## ADDED Requirements

### Requirement: l6-image-filename-parsing
`validate_images`（L6 图片可用性校验）从 Markdown 输出中的图片 URL 提取待核验的 `File:` 名时，SHALL 按以下规则解析，保证查询的是真实文件名而非 CDN 变换参数：

1. 含 `Special:Redirect/file/` 的 URL：取该前缀之后、`?` 之前的部分。
2. 含 `/revision/` 的 Fandom CDN URL（`static.wikia.nocookie.net/.../<name>/revision/latest/...`）：取 `/revision/` 之前路径的最后一段。
3. 含 `/thumb/` 的 MediaWiki 缩略图 URL（`.../images/thumb/<h1>/<h2>/<name>.png/150px-<name>.png?...`）：取尺寸变体段（`NNNpx-` 前缀）之前的一段。
4. 其余 URL：取路径最后一段（现状行为）。

对 `/revision/` 与 `/thumb/` 两类变换后缀形态，解析结果 SHALL 是真实文件名而非尺寸变体；若仍解析出尺寸/查询参数，视为解析缺陷并在测试中失败，而非产出 `api_missing` 误报。

#### Scenario: revision-url-resolves-real-filename
- **WHEN** Markdown 含 `https://static.wikia.nocookie.net/growagarden/images/0/08/DivineIcon.png/revision/latest/scale-to-width-down/111?cb=20260427163904`
- **THEN** 待核验名 SHALL 为 `File:DivineIcon.png`
- **AND** 核验通过后该 URL SHALL NOT 出现在 unavailable 列表

#### Scenario: mediawiki-thumb-url-resolves-real-filename
- **WHEN** Markdown 含 `https://slaythespire.wiki.gg/images/thumb/5/5c/Red-Bash.png/150px-Red-Bash.png?57867c`
- **THEN** 待核验名 SHALL 为 `File:Red-Bash.png`

#### Scenario: plain-url-behavior-unchanged
- **WHEN** Markdown 含不以 `/revision/` 或 `Special:Redirect` 结尾形式的普通图片 URL
- **THEN** 解析行为 SHALL 与既有逻辑一致（取路径最后一段）

#### Scenario: special-redirect-branch-preserved
- **WHEN** Markdown 含 `https://{domain}/Special:Redirect/file/Beee.png`
- **THEN** 待核验名 SHALL 为 `File:Beee.png`（既有分支行为不变）
