# Proposal

## 问题定义

2026-10-02 真实 doctor→explore 验证：Scrapling 成功拒绝 Cloudflare 页面后，Obscura 因不支持 --output 退出 2；CloakBrowser 因托管 Python 不存在未执行。doctor 却返回 success：版本检查脚本遇到 FileNotFoundError 崩溃，Node 将无 stdout 降为 all_ok=true/engines=[]。最终 Explore 的 engine_path=null、artifacts=[]，诊断未充分呈现。

归因为 P-line 的引擎接口、懒预检接线及错误传播缺陷，并伴随缺失的引擎环境；不是站点策略问题。前轮模拟引擎输出的回归未验证真实 CLI 参数或安装生命周期。

## 范围边界

- Obscura 使用支持的参数，从 stdout 获取 HTML，保存后执行既有正文准入。
- Explore 的 CloakBrowser 走既有可安装 preflight，使用返回路径，与 fetch 共享解析规则。
- 版本检查逐引擎报告缺失/异常，doctor 不再把检查失败或空结果当健康；显式区分按需安装的可选引擎与必需检查故障。
- Explore 输出完整引擎链、故障阶段、退出码、诊断文件与下一步；pending 不冒充执行。
- 补真实 CLI 契约测试、临时环境生命周期测试，并在实施后通过标准 doctor→explore 重跑原 URL。
- 不降低内容准入，不升级引擎，不新增独立 API 恢复，不发布站点策略，不接管用户浏览器，不改变 handoff/授权 Gate。

## Capabilities

### New Capabilities
- `engine-execution-contracts`: 明确 Obscura stdout、CloakBrowser preflight 和 Explore 尝试证据的执行契约。
- `engine-health-reporting`: 明确逐引擎版本检查、doctor 异常传播与可选引擎 readiness 的健康报告契约。

### Modified Capabilities

无既有 requirement 替换；以上为已有实现补充缺失的行为要求，不重复定义 engine-registry 的安装方式、doctor-repo-freshness 或 fetch-content-admission。

## Capabilities 待确认项

用户在完整四项方案后要求用 propose 创建 change；两项命名为已授权范围的规范拆分，无额外范围。执行适配属于 A=fetch/B=explore 与 CLI/C=generic/D=HTML；health reporting 属运行时基础设施，不注册为抓取引擎。

## Impact

预计修改 scripts/explore/probe_chain.py、scripts/chrome-agent-cli.mjs、scripts/engine-version-check.sh，以及共享 preflight 解析接线和 tests。维持 Python 3.9、Node ESM、unittest/node:test 和 C9 vertical slice TDD。版本检查的静默健康结果将改为明确异常；可选 fallback 缺失允许通过明确 non-blocking 元数据继续到懒预检，不把缺失声称为健康。

## 关联绑定

标准、项目页与回写目标见 binding.md；行为以本 change specs 为准。历史诊断和原站点复验是证据输入，不承诺真实站点一定能通关。
