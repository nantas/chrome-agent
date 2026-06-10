# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
- [x] 1.2 确认依赖前置条件与外部协作项

## 2. 核心实现任务

### 2.1 链接解析集成（`link-resolution-integration`）

- [x] 2.1.1 测试：在 `tests/lib/` 新增 `test_markdown_link_resolver_integration.py`，验证 `fix_all_links()` 对 `../Pages/Page_*.html` 的解析行为（RED）
- [x] 2.1.2 实现：修改 `scripts/explore/sample_converter.py`，在 `html_to_markdown()` 调用之后、对 `developer.nintendo.com` 域名调用 `fix_all_links()`（GREEN）
- [x] 2.1.3 验证：运行 `python3 scripts/test_runner.py site-samples --domain developer.nintendo.com` 确认 3 个样本全部通过

### 2.2 治理文档更新

- [x] 2.2.1 更新 `docs/architecture/08-tech-stack.md` §4 站点样本回归机制描述，注明链接解析后处理步骤

## 3. 收敛与验证准备

- [x] 3.1 运行 `python3 -m unittest discover -s tests -v` 确认所有测试通过
- [x] 3.2 运行 `python3 scripts/test_runner.py all` 确认全量测试通过

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据
