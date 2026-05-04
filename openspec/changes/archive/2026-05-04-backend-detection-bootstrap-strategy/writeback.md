# Writeback Plan — backend-detection-bootstrap-strategy

## Source

- **Change**: `backend-detection-bootstrap-strategy`
- **Verification**: `verification.md`
- **Date**: 2026-05-04

## Writeback Targets

### Target 1: `sites/README.md`

- **Section**: 在 "新增策略流程" 之后新增 "从已有后端派生策略（Bootstrap）" 小节
- **Content**: 说明 `chrome-agent bootstrap-strategy <url> --from <domain> [--profile <name>]` 的用法、前置条件、生成文件位置、review 要求
- **Rationale**: 操作手册需要记录新 CLI 命令的使用方式

### Target 2: `docs/patterns/mediawiki-extraction.md`

- **Section**: 在 "Cross-site Reuse" 中新增后端检测自动化的引用
- **Content**: 说明 `explore` 现在对无策略的 Weird Gloop MediaWiki 站点会自动检测后端并推荐 `bootstrap-strategy` 命令
- **Rationale**: 经验文档应引用自动化能力，减少人工 checklist 步骤
- **Status**: 可选扩展，本次执行

### Target 3: `AGENTS.md` Section 7

- **Section**: 在 "策略库治理" 的 "新增策略需更新 registry.json" 规则后，新增 bootstrap-strategy 相关说明
- **Content**: 说明 `bootstrap-strategy` 命令会自动更新 registry.json；手动创建策略时仍需人工更新；`backend` 字段为可选 advisory 字段
- **Rationale**: 治理文档需要反映新的自动化流程

## Field Mapping

| Change Artifact | Writeback Target | Field/Content |
|-----------------|------------------|---------------|
| `bootstrap-strategy-cli/spec.md` | `sites/README.md` | 命令接口、字段适配规则 |
| `explore-backend-detection/spec.md` | `docs/patterns/mediawiki-extraction.md` | 后端检测自动化、可复用策略推荐 |
| `site-strategy-schema/spec.md` | `AGENTS.md` | `backend` 字段定义、registry 一致性规则 |

## Execution Results

| Target | Status | Notes |
|--------|--------|-------|
| `sites/README.md` | ✅ | 新增 Bootstrap 小节 |
| `docs/patterns/mediawiki-extraction.md` | ✅ | Cross-site Reuse 中引用后端检测 |
| `AGENTS.md` Section 7 | ✅ | 新增 bootstrap-strategy 治理说明 |
