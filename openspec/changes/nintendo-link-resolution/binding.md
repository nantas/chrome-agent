# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: Orbitos Spec Standard v0.3（`openspec/specs/` 下现有冻结能力规范）
- `project_page_ref`:
  - `scripts/lib/markdown_link_resolver.py`（现有链接解析器，未被 pipeline 集成）
  - `scripts/lib/test_assertions.py` §`assert_links_resolved`（检测 `../Pages/Page_*.html` 未解析链接）
  - `scripts/test_runner.py`（site sample 回归测试入口）
  - `docs/architecture/08-tech-stack.md` §4（测试基础设施描述）
- `additional_context_refs`:
  - `scripts/lib/extraction/converter.py`（html_to_markdown 转换器）
  - `scripts/pipeline/strategies/link_resolver.py`（pipeline 的链接解析策略，与 markdown_link_resolver 不同）

## Source of Truth

- 行为规范真源：`openspec/changes/nintendo-link-resolution/specs/` 下的能力规范文件
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `docs/architecture/08-tech-stack.md` §4：更新站点样本回归机制描述，注明链接解析断言依赖
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: implement 阶段完成后，verification 通过后回写

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（Orbitos Spec Standard v0.3）
- [x] 已确认项目页引用（markdown_link_resolver + test_assertions + test_runner）
- [x] 已确认回写目标与权限（08-tech-stack.md 段落更新）
- [x] 已确认异常处理与冲突策略（仅影响 nintendo 站点样本，不影响 pipeline）
