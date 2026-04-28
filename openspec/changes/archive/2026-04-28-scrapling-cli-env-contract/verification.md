# Verification

> Generated: 2026-04-28
> Status: verified

## 验证结论

本 change 已实现 `SCRAPLING_CLI_PATH` 契约、Scrapling-first 工作流前置 preflight、受管安装保障、`.zshenv` 冲突确认边界，以及项目级 MCP 配置与文档迁移。验证覆盖 spec-to-implementation、task-to-evidence、真实安装恢复、冲突处理和 smoke checks。

## Spec-to-Implementation Coverage

| Capability / Requirement | Implementation | Status |
| --- | --- | --- |
| `scrapling-cli-environment` / `SCRAPLING_CLI_PATH` canonical contract | `scripts/scrapling-cli.sh`, `.codex/config.toml`, `opencode.json`, `README.md`, `docs/setup/scrapling-first-workflow.md` | ✓ |
| `scrapling-cli-environment` / default managed install | `scripts/scrapling-cli.sh` uses `$HOME/.cache/chrome-agent-scrapling/bin/scrapling` and `uv venv` + `uv pip install` + `scrapling install` | ✓ |
| `scrapling-cli-environment` / install assurance before workflow execution | `scripts/scrapling-cli.sh preflight` and `mcp` subcommand | ✓ |
| `scrapling-cli-environment` / `.zshenv` confirmation boundary | `scripts/scrapling-cli.sh persist-zshenv` and conflict detection logic | ✓ |
| `agents-governance` / mandatory preflight before Scrapling-first paths | `AGENTS.md`, `docs/playbooks/scrapling-cli-preflight.md`, `docs/playbooks/scrapling-fetchers.md` | ✓ |
| `agents-governance` / stop on unresolved preflight failure | `scripts/scrapling-cli.sh` non-zero exit and launcher error messages | ✓ |
| `scrapling-first-browser-workflow` / env-based MCP launch | `.codex/config.toml`, `opencode.json` shell launchers | ✓ |
| `scrapling-first-browser-workflow` / docs updated away from host absolute paths | `README.md`, `docs/setup/scrapling-first-workflow.md`, historical docs cleanup | ✓ |

## Task-to-Evidence Coverage

| Task | Evidence | Status |
| --- | --- | --- |
| 1.1 Confirm `scrapling-cli-environment` spec coverage | Read `openspec/changes/scrapling-cli-env-contract/specs/scrapling-cli-environment/spec.md`; implementation matches `SCRAPLING_CLI_PATH`, managed install root, preflight, `.zshenv` confirmation | ✓ |
| 1.2 Confirm `agents-governance` spec coverage | Read `openspec/changes/scrapling-cli-env-contract/specs/agents-governance/spec.md`; `AGENTS.md` and playbooks now require preflight before Scrapling-first execution | ✓ |
| 1.3 Confirm `scrapling-first-browser-workflow` spec coverage | Read `openspec/changes/scrapling-cli-env-contract/specs/scrapling-first-browser-workflow/spec.md`; setup/MCP docs migrated to env-based contract | ✓ |
| 2.1 Audit tracked absolute paths | `git ls-files -z | xargs -0 rg ...` plus targeted `rg` audit on `.codex/config.toml`, `opencode.json`, `docs/setup/scrapling-first-workflow.md`, `README.md`, historical docs | ✓ |
| 2.2 Update Codex MCP config | `.codex/config.toml` now launches `/bin/sh -lc ... scripts/scrapling-cli.sh mcp` | ✓ |
| 2.3 Update Opencode MCP config | `opencode.json` now launches the same shell-based helper | ✓ |
| 2.4 Update Scrapling setup doc | `docs/setup/scrapling-first-workflow.md` documents `SCRAPLING_CLI_PATH`, managed install, `uv` flow, no tracked-file editing | ✓ |
| 2.5 Add workflow-entry preflight rule | `AGENTS.md`, `docs/playbooks/scrapling-cli-preflight.md`, `docs/playbooks/scrapling-fetchers.md`, `docs/playbooks/fallback-escalation.md` | ✓ |
| 2.6 Implement reusable preflight/install flow | `scripts/scrapling-cli.sh` with `preflight`, `shellenv`, `persist-zshenv`, `mcp` commands | ✓ |
| 2.7 Add `.zshenv` confirmation logic | `scripts/scrapling-cli.sh` reports `ZSHENV_STATUS=correct|missing|conflict` and blocks conflict replacement without explicit flag | ✓ |
| 2.8 Update README and setup entry points | `README.md` Quick Start and workflow notes migrated to preflight + managed install contract | ✓ |
| 3.1 Verify no tracked host-specific Scrapling paths remain | `git ls-files -z | xargs -0 rg ...` returned no matches for user-specific Scrapling paths or `uv run scrapling` | ✓ |
| 3.2 Verify missing `SCRAPLING_CLI_PATH` path | Real run: `./scripts/scrapling-cli.sh preflight` returned `STATUS=repaired`, `SOURCE=installed` after installing managed CLI | ✓ |
| 3.3 Verify correctly configured path | Simulated run with temp `.zshenv`: `SCRAPLING_CLI_PATH=... ./scripts/scrapling-cli.sh preflight --no-install` returned `STATUS=available`, `SOURCE=env`, `ZSHENV_STATUS=correct` | ✓ |
| 3.4 Verify conflict handling | Simulated run with temp `.zshenv` conflict returned `ZSHENV_STATUS=conflict`; `persist-zshenv` exited `3` without modifying the file | ✓ |
| 3.5 Smoke checks | `scrapling --help`, `scrapling extract get https://example.com outputs/example.md`, `codex -C /Users/nantas-agent/projects/chrome-agent mcp list` | ✓ |
| 4.1 Generate verification.md | This file | ✓ |
| 4.2 Generate writeback.md | `openspec/changes/scrapling-cli-env-contract/writeback.md` | ✓ |
| 4.3 Execute writeback targets | Updated Obsidian project page and writeback record under `/Users/nantas-agent/projects/obsidian-mind/20_项目/chrome-agent/` | ✓ |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| Preflight/install helper | `scripts/scrapling-cli.sh` | 2.6, 2.7, 3.2, 3.3, 3.4 |
| Codex MCP config | `.codex/config.toml` | 2.2 |
| Opencode MCP config | `opencode.json` | 2.3 |
| Setup docs | `README.md`, `docs/setup/scrapling-first-workflow.md` | 2.4, 2.8 |
| Workflow governance docs | `AGENTS.md`, `docs/playbooks/scrapling-cli-preflight.md`, `docs/playbooks/scrapling-fetchers.md`, `docs/playbooks/fallback-escalation.md` | 2.5 |
| Smoke output artifact | `outputs/example.md` | 3.5 |
| Obsidian writeback targets | `/Users/nantas-agent/projects/obsidian-mind/20_项目/chrome-agent/chrome-agent.md`, `/Users/nantas-agent/projects/obsidian-mind/20_项目/chrome-agent/Writeback记录.md` | 4.3 |

## 缺口与阻塞项

- 无实现阻塞项。
- `/Users/nantas-agent/.zshenv` 未被自动改写；当前状态是 `ZSHENV_STATUS=missing`，符合“未获确认不持久化”的约束。
