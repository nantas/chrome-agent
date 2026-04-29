# Verification

## Summary

- Change: `skill-first-entry-reframe`
- Verified at: `2026-04-29 11:58:46 CST`
- Result: `done`

This change is complete across the workflow skill contract, CLI/backend JSON contract, governance/install docs, decision logging, and bound writeback targets.

## Spec-to-Implementation

- `global-workflow-skill`
  - Implemented in `skills/chrome-agent/SKILL.md`
  - Verified against `chrome-agent doctor --format json` and the CLI result envelope
- `global-capability-cli`
  - Implemented in `scripts/chrome-agent-runtime.mjs`
  - Implemented in `scripts/chrome-agent-cli.mjs`
  - Reflected in CLI help text, `workflow`, and `engine_path` output fields
- `agents-governance`
  - Reflected in `AGENTS.md`
  - Service identity and routing language updated to skill-first / CLI-backed
- `install-chain`
  - Reflected in `docs/playbooks/chrome-agent-global-install.md`
  - Verified by refreshing the installed launcher and workflow skill under `~/.agents/`
- `master-plan`
  - Reflected in `README.md`
  - Reflected in `docs/governance-and-capability-plan.md`

## Task-to-Evidence

- `1.1`
  - Verified by reading all five delta specs under `openspec/changes/skill-first-entry-reframe/specs/`
- `1.2`
  - Verified by auditing `skills/chrome-agent/SKILL.md`, `scripts/chrome-agent-runtime.mjs`, `scripts/chrome-agent-cli.mjs`, `README.md`, and `docs/playbooks/chrome-agent-global-install.md`
- `2.1` and `2.2`
  - Implemented in `skills/chrome-agent/SKILL.md`
  - Legacy dispatcher wording removed; CLI-backed doctor-first routing documented
- `2.3`
  - Implemented in `skills/chrome-agent/SKILL.md`
  - Verified against CLI JSON outputs from `doctor`, `fetch`, `explore`, and `crawl`
- `3.1`
  - Implemented in `scripts/chrome-agent-runtime.mjs` and `scripts/chrome-agent-cli.mjs`
  - Verified by `chrome-agent --help`
- `3.2`
  - Implemented in `scripts/chrome-agent-cli.mjs` (`buildExploreReport`, `runExplore`)
  - Verified by `chrome-agent --format json explore https://www.fanbox.cc/@atdfb/posts`
- `3.3`
  - Implemented in `scripts/chrome-agent-runtime.mjs` and `scripts/chrome-agent-cli.mjs`
  - Verified by JSON outputs including `workflow` and `engine_path`
- `4.1` and `4.2`
  - Implemented in `AGENTS.md`, `README.md`, `docs/playbooks/chrome-agent-global-install.md`, and `docs/governance-and-capability-plan.md`
- `4.3`
  - Implemented in `docs/decisions/2026-04-29-skill-first-entry-reframe.md`
  - Indexed in `docs/decisions/README.md`
- `5.1`
  - Verified with `ORBITOS_REPO_REGISTRY=/tmp/chrome-agent-missing-registry.json CHROME_AGENT_REPO= chrome-agent --format json doctor`
  - Result returned `failure` plus doctor remediation and full runtime envelope
- `5.2`
  - Content retrieval verified with `chrome-agent --format json fetch https://example.com`
  - Platform analysis verified with `chrome-agent --format json explore https://www.fanbox.cc/@atdfb/posts`
  - Bounded traversal verified with `chrome-agent --format json crawl https://www.fanbox.cc/@atdfb/posts --max-pages 1`
  - Explore-first remediation verified with `node scripts/chrome-agent-cli.mjs --format json explore https://example.com`
- `5.3`
  - Verified by matching the skill's documented final shape to live CLI fields: `result`, `command`, `target`, `repo_ref`, `summary`, `artifacts`, `next_action`, `workflow`, `engine_path`
- `6.1`
  - Implemented in this `verification.md`
- `6.2`
  - Implemented in `openspec/changes/skill-first-entry-reframe/writeback.md`
- `6.3`
  - Implemented in `repo://orbitos/20_项目/chrome-agent/chrome-agent.md`
  - Implemented in `repo://orbitos/20_项目/chrome-agent/Writeback记录.md`

## Validation Checks

- Installed launcher refresh
  - `./scripts/install-chrome-agent-cli.sh`
  - Result: refreshed `~/.agents/scripts/chrome-agent.mjs` and `~/.local/bin/chrome-agent`
- Installed workflow skill refresh
  - `mkdir -p ~/.agents/skills/chrome-agent && cp skills/chrome-agent/SKILL.md ~/.agents/skills/chrome-agent/SKILL.md`
  - Result: global skill matches repository source
- Backend healthy
  - `chrome-agent --format json doctor`
  - Result: `success`
- Backend unhealthy
  - `ORBITOS_REPO_REGISTRY=/tmp/chrome-agent-missing-registry.json CHROME_AGENT_REPO= chrome-agent --format json doctor`
  - Result: `failure`
  - Evidence: `workflow: runtime_support`, `engine_path: doctor -> repo_resolution:unresolved`
- Content retrieval route
  - `chrome-agent --format json fetch https://example.com`
  - Result: `success`
  - Evidence: `workflow: content_retrieval`, `engine_path: scrapling:get -> preflight:available`
- Platform analysis route
  - `chrome-agent --format json explore https://www.fanbox.cc/@atdfb/posts`
  - Result: `success`
  - Evidence: `workflow: platform_analysis`, `engine_path: strategy_registry -> analysis_report -> recommended:fetch -> scrapling_preflight:available`
- Strategy-gap analysis route
  - `node scripts/chrome-agent-cli.mjs --format json explore https://example.com`
  - Result: `partial_success`
  - Evidence: explore-first remediation and durable analysis report
- Bounded crawl route
  - `chrome-agent --format json crawl https://www.fanbox.cc/@atdfb/posts --max-pages 1`
  - Result: `success`
  - Evidence: `workflow: content_retrieval`, `engine_path: strategy_registry -> bounded_crawl -> scrapling_preflight:available`

## Conclusion

The change is ready for archive from an implementation perspective. The recommended external model is now skill-first / CLI-backed, and the old Phase 5 assumption that the workflow skill should remain retired has been superseded in code, docs, and writeback targets.
