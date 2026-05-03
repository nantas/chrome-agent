# Specification Delta

## Capability 对齐（已确认）

- Capability: `verification-only`（本 change 为 pure verification change）
- 来源: `proposal.md`
- 变更类型: N/A（不新增/修改任何 capability）
- 用户确认摘要: 并行抓取验证 + 强 stealth 对比测试，不涉及能力变更

## 规范真源声明

- 本 change 不创建或修改任何 capability spec
- 验证目标参考的具体 spec：`openspec/specs/obscura-fetch-contract/spec.md`（其 stealth 描述边界和 smoke-check 范围）
- 本文件仅作占位，表示本 change 无 capability delta

## 验证范围参考

验证聚焦于 `obscura-fetch-contract` spec 中以下尚未充分验证的维度：

- Performance characteristics: 并行场景下的 `obscura scrape` 性能表现
- Stealth mode: `--stealth` 参数在强反爬站点（Cloudflare Turnstile 类）中的实际有效性
- 这些验证不修改 spec 中的 requirements，仅验证其描述边界的正确性
