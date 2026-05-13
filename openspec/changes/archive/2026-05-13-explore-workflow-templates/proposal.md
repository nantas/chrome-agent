# Proposal

## 问题定义

当前 `chrome-agent explore` 遇到未覆盖站点（strategy gap）时，仅返回一句"strategy gap"和极简报告，不执行任何实际页面内容分析。用户需要手动完成引擎探测、API 发现、结构映射、样本转换验证等全部工作，才能产出站点策略。这套流程高度依赖 agent 经验，无法标准化。

本次变更解决以下断层：

1. **explore 产出过浅**：未命中策略时不做 deep discovery，用户需要自行爬取分析
2. **策略创建无模板**：策略文件需要从零手工创建，无平台模板可用
3. **样本验证无体系**：转换后缺乏质量标准，问题需要用户肉眼发现
4. **用户确认环节缺失**：爬取范围、样本种类、输出格式等决策无系统性交互流程

## 范围边界

**范围内（v1）：**

- 新增 `explore` deep discovery 管线（引擎链 / API / 结构 / 保护机制）
- 新增平台策略模板系统（`sites/templates/` 目录 + 按平台类型选择）
- 新增 agent 样本自检体系（S1-S7，pass/fail）
- 新增用户交互确认流程（ask_user 多轮对话 + 范围/粒度/样本确认）
- 回写：`AGENTS.md` 更新路由规则、新建操作手册
- 支持策略模板类型：`mediawiki`、`mediawiki-fandom`、`static-site`、`custom`
- 自动修复 loop（最多 2 轮，仅处理已知可自动修复问题）

**范围外（v1）：**

- 不涉及 `fetch` / `crawl` 命令本身的修改
- 不包含身份验证/认证页面探测（如有，向用户反馈）
- 不包含 WordPress / GraphQL 模板（骨架保留，实现在后续迭代）
- 不修改引擎注册表（engine-registry）
- 不修改反爬策略库（anti-crawl）

## Capabilities

### New Capabilities

- `explore-workflow`: 完整的 explore 工作流，覆盖 deep discovery、策略模板选择、用户交互确认、样本转换与自检、迭代至策略冻结
- `strategy-templates`: 平台类型驱动的策略模板系统，支持 mediawiki / mediawiki-fandom / static-site / custom 等平台模板
- `sample-self-check`: 样本转换后、向用户呈现前的 agent 自检体系，包含 S1-S7 检查项目和自动修复机制

### Modified Capabilities

- `explore`: 增强现有 `explore` 命令的后端，从"仅返回 strategy gap"升级为"执行完整探索工作流"，向后兼容已有策略命中场景

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

| 影响范围 | 类型 | 说明 |
|---------|------|------|
| CLI `explore` 命令 | 修改 | 后端逻辑从"查 registry 无匹配→返回 gap"改为"查 registry 无匹配→执行 deep discovery 管线" |
| `AGENTS.md` | 更新 | 工作流路由规则中补充 explore deep discovery 路径说明 |
| `docs/playbooks/` | 新增 | 新建操作手册 `explore-workflow-conduct.md` |
| `sites/templates/` | 新增 | 新建策略模板目录 + 首批 4 个模板文件 |
| `sites/strategies/` | 无直接影响 | 现有策略文件无需修改，新策略通过更新后的 explore 流程生成 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `repo://orbitos` (Orbitos Spec Standard v0.3)
  - `repo://chrome-agent/AGENTS.md` — 工作流路由规则
  - `docs/playbooks/explore-workflow-conduct.md` — 新建操作手册
  - `sites/templates/` — 新建策略模板
