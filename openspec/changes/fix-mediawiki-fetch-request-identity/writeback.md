# 回写

- 已更新 `docs/architecture/04-cli-reference.md` 的 fetch：历史/旧版/显式 parse 的参数边界、输出、身份与续页方式。
- CLI 是现有基础设施编排，仅委托共享 ApiClient，不新增引擎或能力实现文件，因此能力注册表不变。
- C10 全局 runtime/skill 已按现有授权同步，installed-hash 为当前 HEAD；不改 shell 配置。
- 本 change 保持 active，归档时需将 delta 回填 fetch-kernel，不在本次交接中移动。
- 2026-10-19 用户要求整理当前修改并提交，关联修复在chrome-agent仓独立提交；45项相关测试、语法与差异检查通过。无关的developer.taptap.cn策略草稿留在工作区。提交后按C10将installed-hash刷新到新HEAD，不推送。
