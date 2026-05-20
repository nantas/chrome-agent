# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
  - `redirect-detection`: convert phase 入口 + redirect map 构建
  - `pipeline-converters`: convert phase 的 redirect HTML 检测
  - `link-resolver-fallback`: 两个 LinkResolver 的 fallback return 修改
- [x] 1.2 确认依赖前置条件与外部协作项
  - 无外部依赖，所有修改均在 `scripts/pipeline/` 内部

## 2. 核心实现任务

- [x] 2.1 修改 `ExactTitleLinkResolver.resolve()` fallback
  - 文件: `scripts/pipeline/strategies/link_resolver.py`
  - 覆盖 spec: `specs/link-resolver-fallback/spec.md` → `unresolved-link-fallback-to-wiki-url`
  - 变更: 最后一行 `return f"[{display}]({target.replace(' ', '_')}.md)"` → `return f"[{display}](https://{self._domain}/wiki/{target.replace(' ', '_')})"`
  - 验证: 对不在 manifest 中的 target 调用 resolve()，确认返回 wiki URL

- [x] 2.2 修改 `ShortNameLinkResolver.resolve()` fallback
  - 文件: `scripts/pipeline/strategies/link_resolver.py`
  - 覆盖 spec: `specs/link-resolver-fallback/spec.md` → `unresolved-link-fallback-to-wiki-url`
  - 变更: 同 2.1，最后一行改为 wiki URL fallback
  - 验证: 同 2.1

- [x] 2.3 在 convert phase 实现 redirect 检测
  - 文件: `scripts/pipeline/pipeline/phases/convert.py`
  - 覆盖 spec: `specs/redirect-detection/spec.md` → `redirect-page-detection`, `redirect-page-skip-output`; `specs/pipeline-converters/spec.md` → `redirect-html-detection-before-convert`
  - 变更: 在页面处理循环中，对 `rendered_html` 检测 `redirectMsg`；检测到时标记 `status: "redirect"`，跳过 convert，提取目标标题构建 redirect_map
  - 验证: 对包含 `redirectMsg` 的 HTML 执行 convert phase，确认不生成 .md 文件且 pipeline state 包含 redirect 记录

- [x] 2.4 将 redirect_map 注入 LinkResolver
  - 文件: `scripts/pipeline/strategies/link_resolver.py`, `scripts/pipeline/pipeline/phases/convert.py`
  - 覆盖 spec: `specs/redirect-detection/spec.md` → `redirect-source-link-resolution`
  - 变更: `convert_links()` 和 `resolve()` 方法签名新增 `redirect_map` 参数（默认 `{}`）；resolve 中先查 redirect_map 替换 target，再走正常 manifest 查找
  - 验证: 对 `[[Item]]` 链接（Item redirect 到 Items），确认解析为 Items 的相对路径

## 3. 收敛与验证准备

- [x] 3.1 运行 BOI 100-page baseline 测试
  - 命令: `bash tests/e2e/boi-100-baseline.sh`
  - 预期: empty files 从 7 降至 1（仅剩 Category:Modes）；broken links 因 redirect map 注入减少
- [x] 3.2 检查 redirect 页面未生成文件
  - 验证 `outputs/test-100-extraction/items/Item.md` 等文件不存在
  - 检查 pipeline state 中 redirect 记录

## 4. 验证与回写收敛

- [x] 4.1 基于测试结果生成或更新 verification.md
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md
- [x] 4.3 执行 writeback.md 中定义的回写目标
