# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: Orbitos Spec Standard v0.3（`openspec/specs/` 下现有冻结能力规范）
- `project_page_ref`:
  - `AGENTS.md` §0.5 Development Hard Constraints（C5 测试框架 + C9 测试义务新增）
  - `AGENTS.md` §9 Reference Index（新增 `tests/` 目录条目 + `test_runner.py` 条目）
  - `AGENTS.md` §11 Prerequisite Reading（新增测试相关任务必读表）
  - `docs/architecture/08-tech-stack.md` §4 Test Infrastructure（重写测试基础设施章节）
  - `docs/architecture/03-strategy-schema.md`（新增 `samples` frontmatter 字段）
- `additional_context_refs`:
  - `scripts/pipeline/tests/`（现有测试文件，作为迁移参考）
  - `tests/chrome-agent-runtime.test.mjs`（Node.js 测试参考）
  - `openspec/changes/cdp-cache-pipeline-tooling/`（最新一次无测试交付的 change，作为 known gap 参考）

## Source of Truth

- 行为规范真源：`openspec/changes/testing-governance/specs/` 下的能力规范文件
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` §0.5：新增 C9 测试义务硬约束，扩展 C5 描述
  - `AGENTS.md` §9：新增 `tests/` 目录、`scripts/test_runner.py`、通用断言模块的索引条目
  - `AGENTS.md` §11：新增"测试相关任务"必读表
  - `docs/architecture/08-tech-stack.md` §4：重写为完整测试基础设施文档（目录结构、运行命令、站点样本机制）
  - `docs/architecture/03-strategy-schema.md`：新增 `samples` frontmatter 字段定义
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: implement 阶段完成后，verification 通过后回写

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（Orbitos Spec Standard v0.3）
- [x] 已确认项目页引用（AGENTS.md + 08-tech-stack + 03-strategy-schema）
- [x] 已确认回写目标与权限（三份文档 + AGENTS.md 多处扩展）
- [x] 已确认异常处理与冲突策略（verification 内测试完备检查，J3 分级）
