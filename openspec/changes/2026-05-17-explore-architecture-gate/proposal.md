# Proposal: Explore Architecture Gate

## 问题定义

在 2026-05-17 对 `bindingofisaacrebirth.wiki.gg` 的站点策略配置过程中，第一次提交（`55ac8d4`）被立即 revert（`d301cd0`），根因如下：

### Architecture Violation 具体案例

**Commit 55ac8d4 中的违规：**

| 违规类型 | 具体内容 | 后果 |
|---------|---------|------|
| **死配置 (Dead Config)** | strategy.md 新增 `wiki_gg_specific` block（`strip_portable_infobox_aside`、`strip_nav_div_boxes`、`convert_relative_urls`、`clean_youtube_embeds` 四个布尔标志）——但 pipeline 代码无任何消费者读取这些字段 | 配置看起来完整，实际不生效 |
| **站点硬编码 (Orphaned Logic)** | pipeline 代码中 `_extract_portable_infobox()` 硬编码了 `"aside.portable-infobox"` 选择器；nav 清理硬编码了 `"nav-box"`、`"nav-main"` 类名；YouTube 清理和 URL 转换无条件在所有站点执行 | 代码声称"通用"实则站点特化，复用给其他站点时行为异常 |

**根因：** 在样本质量自检通过后、用户确认前，工作流缺少一个强制性的 **Architecture Gate**——验证策略配置（strategy.md）与管线实现（sample_converter.py）之间的双向对齐。

### 两类必须校验的对齐

```
┌─────────────┐         ┌──────────────────┐
│ strategy.md │ ──────> │ sample_converter │   策略→管线：配置必有消费者
│  (配置源)    │         │   (配置解释器)    │
└─────────────┘ <────── └──────────────────┘   管线→策略：操作必有配置源
```

- **策略→管线 (Strategy → Pipeline)**：strategy.md 中的每个 `extraction.*` 字段，必须在 pipeline 代码中有对应的 `if cfg.get("field"): ...` 消费逻辑。无消费者的字段 = 死配置。
- **管线→策略 (Pipeline → Strategy)**：pipeline 代码中每个站点相关的值（HTML 选择器、类名、正则模式、文件名），必须从 strategy 配置中读入。硬编码值 = 孤儿逻辑。

## 范围边界

### 范围内

- 定义 Architecture Gate 作为 explore 工作流的独立 Phase，插入在样本自检通过后、用户确认前
- 策略→管线的 schema 校验：可编程执行的字段消费者检查
- 管线→策略的审计检查：agent 执行的手动代码扫描清单
- Architecture Gate 的输出格式（pass/fail + violation 列表）
- Agent 行为规则：违规时必须修复才能继续到用户确认阶段

### 范围外

- 不修改现有策略 schema（`extraction.*` 字段结构）
- 不重构 converter 代码架构
- 不新增工具或 CLI 命令
- 不处理其他 workfow（fetch/crawl/scrape）

## Capabilities

### New Capabilities

- `explore-architecture-gate`: Architecture Gate——策略与管线双向对齐校验，确保零死配置、零站点硬编码

### Modified Capabilities

- `explore-workflow`: 工作流增加 Architecture Gate Phase（在 sample self-check 与 user confirmation 之间）
- `explore-skill-gates`: Agent Gate 规则增加架构校验行为要求

## Impact

- **Explore 工作流**: 新增 Phase 2 (Architecture Gate)，含程序化 schema check + agent 审计清单
- **Agent 行为**: 修复 commit 55ac8d4 型违规将被 Gate 拦截，不再需要人工 revert
- **向下兼容**: 不影响已有策略文件和 converter 代码的正常执行
