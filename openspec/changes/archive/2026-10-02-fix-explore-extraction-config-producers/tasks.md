# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 读取 binding/proposal、`specs/explore-scaffold/spec.md`、design 及 AGENTS 对 Explore/策略/测试的必读文档；确认已有 auto_remediate 调用者与非 MediaWiki 适用边界，建立 scenario→实现/测试映射。
- [x] 1.2 运行本地离线 scaffold 复现并记录两个旧模板的原始错误；确认依赖可用、工作区已有改动保持；确定规划报告接线 seam 不新增能力模块、不放宽 schema。

## 2. 核心实现任务（每个 slice 完成 GREEN 后进入下一项）

- [x] 2.1 RED：将复现转为 tests 下 registry 驱动的 MediaWiki 模板 schema/真实 generate 测试，以 generic 模板及编辑/TOC/body fixture 先记录失败；fixture 不修改生产注册表。
- [x] 2.2 GREEN：迁移 mediawiki.yaml 为 strip_edit_links + .toc/#toc selectors，立即通过对应真实生成与共享预处理效果测试。
- [x] 2.3 RED：增加 wiki.gg 真实生成与保留原 selectors/image rules 的行为测试，记录未知旧 cleanup 的失败。
- [x] 2.4 GREEN：迁移 mediawiki-wiki-gg.yaml，运行全部已注册 MediaWiki 模板用例（包括 Fandom 控制样本），确认均输出合法草稿、不冻结/发布。
- [x] 2.5 RED：在 self_check 对全部既有 fixable_type 的输出准入/支持报告、输入嵌套不变、批量确定性测试中逐项捕获 unsupported 操作；先从 base64 无证据场景开始，记录 RED。
- [x] 2.6 GREEN：在现有 self_check.py 引入配置规划/独立诊断，auto_remediate 保持 extraction dict 返回；unsupported/no-evidence 不注入未知操作或猜字段，支持的 wrapper/table/space 动作保持有效。逐个测试→实现→通过，更新旧虚构映射字符串测试，不以删测试替代覆盖。
- [x] 2.7 RED→GREEN：补齐完整已有/显式证据 lazyload 规划及真实 preprocessing 测试，实现结构化字段更新，断言 placeholder 被正确替换、原输入不变、无 fix_lazyload_images；缺证据场景返回 missing_evidence。
- [x] 2.8 RED：以临时 MediaWiki 草稿驱动真实 iterate，覆盖 edit/TOC 反馈落盘 round-trip 与非法既有/候选配置（原文件字节不变，convert 0 次），仅 mock 网络转换边界，记录失败。
- [x] 2.9 GREEN：iterate 复用已验证规划逻辑，在写入/转换前完成 MediaWiki schema 准入；结构化返回字段错误或 unresolved。立即运行 2.8，并补充 image wrapper+缺 lazyload 证据和非 MediaWiki 描述性规则边界测试。
- [x] 2.10 RED：main 自动修复循环集成测试保留真实 planner/schema，以控制 self-check/convert 结果捕获 unsupported-only 重试和原因丢失问题；检查原 failure 身份保留。
- [x] 2.11 GREEN：main.py 薄层接线 changed/unresolved 报告，无有效更新停止重转换；有合法更新继续转换/重检且遵守原次数上限，质量状态由重检决定，原失败仍供 KI 消费。

## 3. 收敛与验证准备

- [x] 3.1 运行受影响 unittest，然后 `python3 -m unittest discover -s tests -v` 与适用 Node 全量测试；每个修改代码模块有对应测试；若实际修改共享库，补 C9 对应覆盖；清理临时 debug 日志/fixture。
- [x] 3.2 重跑最初离线 scaffold 环并记录 GREEN，验证 generic/wiki.gg/Fandom 模板、全部修复分支以及非法文件保留场景，逐项补齐 spec scenario 证据，保留静态站点边界。
- [x] 3.3 按 chrome-agent 预检与 Gate 在外部 cwd 重跑原始 Explore URL，验证本次 schema 错误已解除；若出现其它错误单独记录，禁止宣称网站成功或自动进入 extraction。
- [x] 3.4 运行 doctor 和 `doctor --check capabilities`，能力检查必须通过；若实施新增能力文件执行 C11 注册同步；若触及 runtime/CLI/skill 执行 C10 全局同步，否则记录不适用。

## 4. 验证与回写收敛

- [x] 4.1 根据实际结果生成 verification.md，覆盖 spec-to-implementation、task-to-evidence、各 scenario evidence_map、RED/GREEN、consumer 效果与原目标结果；列明未覆盖/独立故障。
- [x] 4.2 回写前读取 binding 指向标准，基于 verification 生成 writeback.md，列明 capability/spec 增量、目标区块与实际执行证据。
- [x] 4.3 完成三份已绑定架构文档的结论回写，记录时间/执行人/结果；归档时将三个 MODIFIED 与一个 ADDED requirement 合并到 `openspec/specs/explore/explore-scaffold.md`，保留其它内容与样本推荐规范，避免平行真源。
- [x] 4.4 运行 OpenSpec strict validate、核对 task/verification/writeback 闭环与准入检查证据后声明具备归档条件；本次实施不自动提交/归档其它 change。
