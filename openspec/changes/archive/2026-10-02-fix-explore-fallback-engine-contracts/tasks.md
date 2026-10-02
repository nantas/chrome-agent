# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 对照两项 capability specs 和 design，确认 probe_chain.py、版本检查脚本、Node doctor 消费端及现有测试入口，建立 requirement→实现→测试映射；保留已有 package-lock 和站点目录修改。
- [x] 1.2 核对引擎配置、真实 Obscura fetch --help、CloakBrowser preflight 输出及 doctor partial_success 消费规则，保存基线证据；不升级引擎、不绕过 workflow Gate。

## 2. 逐引擎版本检查 slice

- [x] 2.1 RED：在 tests/ 增加 complete-per-engine-version-report 回归，覆盖一个可执行文件缺失、另一个仍可检查、超时及版本解析失败；断言完整记录、all_ok 和退出码。
- [x] 2.2 GREEN：修改 scripts/engine-version-check.sh 的逐引擎异常处理，区分 not_installed 与检查异常，保证单引擎故障不吞掉其他记录；运行 2.1 测试通过。

## 3. doctor 检查器契约 slice

- [x] 3.1 RED：使用 node:test 覆盖 doctor-validates-version-check-outcome：脚本缺失、启动失败、超时、空/坏 JSON、遗漏或重复引擎记录、退出码/状态矛盾，以及非零退出但完整合法的非健康报告。
- [x] 3.2 GREEN：修复 scripts/chrome-agent-cli.mjs 的 runEngineVersionCheck 与错误传播，基于配置校验覆盖率，保留合法失败报告；检查异常必须为 blocking version_check_failed，运行 3.1 测试通过。

## 4. 可选引擎 readiness slice

- [x] 4.1 RED：覆盖 explicit-optional-engine-readiness：仅可选 CloakBrowser 缺失、必需检查失败、未知检查异常和全健康四种情形；验证 partial_success、blocking、needs_preflight、下一步及 dispatch Gate。
- [x] 4.2 GREEN：在现有 doctor envelope 中实现显式 readiness 和整体状态汇总，仅所有失败检查明确非阻塞时允许继续；保留 freshness/reload Gate，运行 4.1 测试通过。

## 5. Obscura stdout slice

- [x] 5.1 RED：为 obscura-stdout-acquisition 增加严格 argv 的可执行 fixture，拒绝 --output；覆盖 HTML stdout、独立 stderr、非零退出、空输出、challenge 输出及旧文件残留。
- [x] 5.2 GREEN：修改 Explore Obscura 适配器，以本次成功 stdout 保存 HTML 并运行既有准入；不复用旧文件，运行 5.1 测试通过。
- [x] 5.3 核对真实安装的 Obscura fetch --help；环境支持时用本地受控 HTTP 页面验证 stdout 获取，保存命令、版本、退出码及结果。若受阻，明确记录未完成项，不以 fixture 替代真实契约证据。

## 6. CloakBrowser 懒预检 slice

- [x] 6.1 RED：在临时 managed root 与受控 installer 下覆盖 cloakbrowser-preflight-before-dispatch：已安装不重装、缺失触发安装、自定义根路径、预检非零/无效输出/路径不可执行；断言失败后未启动引擎。
- [x] 6.2 GREEN：Explore 调用既有 shell preflight 并使用返回路径；对齐 Node fetch 的解析和校验规则，移除 Explore 硬编码路径。若引入共享实现文件，同步能力注册；运行 6.1 测试通过，测试不修改真实全局安装。

## 7. Explore 证据与结果 slice

- [x] 7.1 RED：覆盖 explore-attempt-evidence 的 mixed-failure-chain、pending-is-not-executed、recovery-preserves-admission；断言实际 engine_path、各阶段/退出码、诊断文件、next_action，以及 pending 不计为执行。
- [x] 7.2 GREEN：补齐 Explore 失败与恢复路径的证据落盘和返回值，错误摘要限长，保留 handoff Gate；运行 7.1 测试及既有 challenge/正常正文回归通过。

## 8. 收敛与验证准备

- [x] 8.1 运行 python3 -m unittest discover -s tests -v 和仓库标准 Node 测试入口，记录结果；确认 Python 3.9 兼容、ESM 和测试目录符合约束。
- [x] 8.2 按 C10 同步实际修改的 CLI/runtime/skill 全局副本并刷新 installed hash，检查全局入口与仓库实现一致；运行 doctor --check capabilities，确认无引擎版本漂移。
- [x] 8.3 使用 chrome-agent 标准 doctor→explore 工作流复验 https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1；遵守阻塞和 handoff Gate，记录实际执行/未执行引擎、准入结论、诊断路径及剩余外部问题。

## 9. 验证与回写收敛

- [x] 9.1 基于真实实现结果生成 verification.md，逐项关联 spec-to-implementation 与 task-to-evidence；区分稳定回归、真实 CLI 契约及原站点结果。
- [x] 9.2 阅读 binding.md 指定标准，基于验证结论生成 writeback.md，列明架构/CLI/工作流文档及规范回写目标、字段映射和前置条件。
- [x] 9.3 执行获授权的回写并记录链接、时间、执行人及结果；严格校验 change，归档前确认 capabilities doctor 通过与 C10 同步完整，不将无关工作区修改纳入提交。
