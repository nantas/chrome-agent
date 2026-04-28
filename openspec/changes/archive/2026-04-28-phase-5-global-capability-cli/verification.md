# Verification

## Summary

- Change: `phase-5-global-capability-cli`
- Verified at: `2026-04-28 22:50:00 CST`
- Result: `done`

Phase 5 implementation is complete across the global launcher, repo-backed dispatch, strategy-gated crawl, output lifecycle, governance docs, and bound writeback targets.

## Spec-to-Implementation

- `global-capability-cli`
  - Implemented in `scripts/chrome-agent-runtime.mjs`
  - Implemented in `scripts/chrome-agent-cli.mjs`
  - Main spec created at `openspec/specs/global-capability-cli/spec.md`
- `install-chain`
  - Implemented in `scripts/install-chrome-agent-cli.sh`
  - Main spec created at `openspec/specs/install-chain/spec.md`
  - Operational guidance updated in `docs/playbooks/chrome-agent-global-install.md`
- `output-lifecycle`
  - Implemented in `scripts/chrome-agent-cli.mjs` via durable/disposable artifact metadata and `clean`
  - Main spec created at `openspec/specs/output-lifecycle/spec.md`
- `strategy-guided-crawl`
  - Implemented in `scripts/chrome-agent-cli.mjs`
  - Main spec created at `openspec/specs/strategy-guided-crawl/spec.md`
- `agents-governance` modified
  - Merged into `openspec/specs/agents-governance/spec.md`
  - Reflected in `AGENTS.md`
- `master-plan` modified
  - Merged into `openspec/specs/master-plan/spec.md`
  - Reflected in `docs/governance-and-capability-plan.md`

## Task-to-Evidence

- `1.1` to `1.6`
  - Verified by merging the new and modified specs into `openspec/specs/`
  - Verified by corresponding governance updates in `AGENTS.md`, `README.md`, and `docs/governance-and-capability-plan.md`
- `2.1`
  - Implemented in `scripts/install-chrome-agent-cli.sh`
  - Verified by installing to `~/.agents/scripts/chrome-agent.mjs` and `~/.local/bin/chrome-agent`
- `2.2`
  - Implemented in `scripts/chrome-agent-runtime.mjs`
  - Verified by registry-first and env-fallback doctor runs
- `2.3`
  - Implemented in `scripts/chrome-agent-runtime.mjs` dispatching into `scripts/chrome-agent-cli.mjs`
  - Verified by repo-shape enforcement on `AGENTS.md`
- `2.4`
  - Implemented in `README.md`, `docs/setup/chrome-tooling.md`, and `docs/playbooks/chrome-agent-global-install.md`
  - Historical skill downgraded in `skills/chrome-agent/SKILL.md`
- `2.5`
  - Implemented in `scripts/chrome-agent-cli.mjs` (`doctor`)
  - Verified by launcher, repo-registry, env fallback, repo-shape, and Scrapling preflight checks
- `3.1` to `3.3`
  - Implemented in `scripts/chrome-agent-cli.mjs` (`crawl`)
  - Verified by refusal without strategy and bounded success with `fanbox.cc` strategy
- `3.4`
  - Implemented in `scripts/chrome-agent-cli.mjs` artifact metadata and per-run `outputs/<run-id>/manifest.json`
- `3.5`
  - Implemented in `scripts/chrome-agent-cli.mjs` (`clean`)
  - Verified by removing `outputs/` run directories while preserving `reports/`
- `4.1` to `4.3`
  - Implemented in `openspec/specs/agents-governance/spec.md`, `openspec/specs/master-plan/spec.md`, `AGENTS.md`, `README.md`, `docs/governance-and-capability-plan.md`, `docs/playbooks/chrome-agent-global-install.md`, and `docs/setup/chrome-tooling.md`
- `5.1`
  - Verified with `./scripts/install-chrome-agent-cli.sh`
  - Verified with `~/.local/bin/chrome-agent doctor --format json`
- `5.2`
  - Verified with `ORBITOS_REPO_REGISTRY="$PWD/.missing-registry.json" CHROME_AGENT_REPO="$PWD" ~/.local/bin/chrome-agent doctor --format json`
  - Result exposed `repo_ref: env:CHROME_AGENT_REPO` and `resolution_mode: env_fallback`
- `5.3`
  - Verified with `~/.local/bin/chrome-agent fetch https://example.com --format json`
  - Verified with `node scripts/chrome-agent-runtime.mjs explore https://example.com --format json`
- `5.4`
  - Verified with `node scripts/chrome-agent-runtime.mjs crawl https://example.com --format json`
  - Verified with `node scripts/chrome-agent-runtime.mjs crawl https://www.fanbox.cc/@atdfb/posts --max-pages 2 --format json`
- `5.5`
  - Verified with `node scripts/chrome-agent-runtime.mjs clean --format json`
- `6.1` to `6.3`
  - Implemented in this `verification.md`, the paired `writeback.md`, and the updated bound project pages under `../obsidian-mind/20_项目/chrome-agent/`

## Validation Checks

- Fresh install
  - `scripts/install-chrome-agent-cli.sh` created `~/.agents/scripts/chrome-agent.mjs` and `~/.local/bin/chrome-agent`
  - `~/.local/bin/chrome-agent doctor --format json` returned `success`
- Registry-first resolution
  - `repo_ref` stayed `repo://chrome-agent`
  - `resolution_mode` stayed `repo_registry`
- Env fallback resolution
  - With a missing registry file and valid `CHROME_AGENT_REPO`, `doctor` returned `partial_success`
  - `repo_ref` switched to `env:CHROME_AGENT_REPO`
  - `resolution_mode` switched to `env_fallback`
- JSON-first result contract
  - `doctor`, `explore`, `fetch`, `crawl`, and `clean` all returned `result`, `command`, `target`, `repo_ref`, `summary`, `artifacts`, and `next_action`
- Artifact lifecycle
  - `fetch` and `crawl` produced durable reports under `reports/`
  - Disposable outputs were grouped under run-scoped directories beneath `outputs/`
  - `clean` removed disposable output directories and preserved the durable `reports/` directory by default
- Strategy-gated crawl
  - `crawl https://example.com` refused execution and returned explore-first remediation
  - `crawl https://www.fanbox.cc/@atdfb/posts --max-pages 2` stayed within declared `entry_points` and `url_parameter` pagination boundaries

## Conclusion

The change is ready for archive from an implementation perspective. The repo-backed global CLI is now the formal external entrypoint, while repository-local AGENTS/spec/strategy authority remains the execution source of truth.
