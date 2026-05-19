# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-cli-entry`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: `--phase` schema 变更（新增 `fetch`、`convert`，移除 deprecated 值）；新增 `--re-fetch` flag；缓存目录路径从 strategy 配置推导。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: re-fetch-cli-flag
The system SHALL 支持 `--re-fetch` CLI flag。

当与 `--phase fetch` 或 `--phase all` 一起使用时，SHALL 忽略已有缓存，强制重新获取所有页面并覆盖缓存文件。

#### Scenario: re-fetch-flag
- **WHEN** 执行 `--phase fetch --re-fetch`
- **THEN** SHALL 不检查缓存存在性
- **AND** SHALL 对所有页面重新发起 API 请求
- **AND** SHALL 覆盖已有缓存文件

### Requirement: cache-root-resolution
The system SHALL 在 pipeline 入口处解析缓存根目录。

解析逻辑：
1. 读取 strategy 文件
2. 提取 `api.platform`（若存在）或使用 `"scrapling"` 作为 platform
3. 提取 `domain` 字段
4. 构造 `.cache/<platform>/<domain>/` 路径
5. 自动创建目录（如不存在）

#### Scenario: cache-root-resolution-mediawiki
- **WHEN** strategy 的 `api.platform` 为 `"mediawiki"` 且 `domain` 为 `"bindingofisaacrebirth.wiki.gg"`
- **THEN** `cache_root` SHALL 解析为 `<repo_root>/.cache/mediawiki/bindingofisaacrebirth.wiki.gg/`

## MODIFIED Requirements

### Requirement: phase-choices
`--phase` CLI 参数的 choices SHALL 更新为：

```python
choices=["all", "discover", "fetch", "convert", "assemble"]
```

移除的值：`"extract"`、`"A"`、`"B"`、`"C"`、`"homepage"`。

#### Scenario: valid-phase-choices
- **WHEN** 用户传入 `--phase fetch`
- **THEN** argparse SHALL 接受该值

#### Scenario: invalid-phase-choice
- **WHEN** 用户传入 `--phase extract`
- **THEN** argparse SHALL 拒绝，输出 `"invalid choice: 'extract' (choose from 'all', 'discover', 'fetch', 'convert', 'assemble')"`

### Requirement: phase-forwarding-from-cli
`chrome-agent-cli.mjs` 中的 `runCrawl()` SHALL 将 `--phase` 参数传递到 Python pipeline。

当 MediaWiki API 路径被触发时，JS CLI SHALL 在 `apiArgs` 中添加 `"--phase"` + 用户指定的值。

#### Scenario: phase-forwarding
- **WHEN** JS CLI 执行 `runCrawl()` 且用户指定 `--phase fetch`
- **AND** strategy 的 `api.platform` 为 `"mediawiki"`
- **THEN** `apiArgs` SHALL 包含 `["--phase", "fetch"]`

### Requirement: gitignore-update
`.gitignore` SHALL 排除 `.cache/` 目录，使其不进入版本管理。

#### Scenario: cache-gitignored
- **WHEN** `.cache/` 目录存在
- **THEN** `git status` SHALL NOT 显示 `.cache/` 下任何文件
