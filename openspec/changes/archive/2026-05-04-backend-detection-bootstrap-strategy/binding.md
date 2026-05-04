# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `repo://chrome-agent/openspec/specs/site-strategy-schema/spec.md` — 站点策略文件 schema 与受控词汇表
  - `repo://chrome-agent/openspec/specs/strategy-guided-crawl/spec.md` — crawl 能力的行为规范
- `project_page_ref`:
  - `repo://chrome-agent/docs/patterns/mediawiki-extraction.md` — MediaWiki 跨站点提取模式与复用经验
- `additional_context_refs`:
  - `repo://chrome-agent/sites/README.md` — 策略库目录与格式规范
  - `repo://chrome-agent/AGENTS.md` — 仓库治理规则（策略库治理 section 7、引擎扩展治理 section 8）
  - `repo://chrome-agent/scripts/chrome-agent-cli.mjs` — CLI 实现与策略匹配逻辑
  - `repo://chrome-agent/configs/engine-registry.json` — 引擎注册表

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  1. `docs/patterns/mediawiki-extraction.md` — 更新：加入后端检测相关章节（可选扩展）
  2. `sites/README.md` — 更新：新增"从已有后端派生策略"操作说明
  3. `scripts/chrome-agent-cli.mjs` — 修改：增强 explore + 新增 bootstrap-strategy 命令路由
  4. `configs/backend-signatures.json` — 新建：后端指纹库
  5. `AGENTS.md`（section 7 Strategy Library Governance）— 更新：策略库操作说明
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 变更归档时同步到 AGENTS.md 与 README，CLI 与配置文件在实现阶段立即写入

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- `registry.json` 为索引摘要，与 frontmatter 不一致时以 frontmatter 为准
- 新增站点策略通过 bootstrap-strategy 命令生成后，必须同步更新 `registry.json`

## 待确认项

- [x] 已确认标准页引用（site-strategy-schema, strategy-guided-crawl）
- [x] 已确认项目页引用（mediawiki-extraction 经验文档）
- [x] 已确认回写目标与权限（仓库内文件，无需外部权限）
- [x] 已确认异常处理与冲突策略（explore 后端检测误判时 fallback 到现有策略缺口报告）
