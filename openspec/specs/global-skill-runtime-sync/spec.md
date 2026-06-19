# Specification Delta

## Capability 对齐（已确认）

- Capability: `global-skill-runtime-sync`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认「仅 New capability `global-skill-runtime-sync`」，不修改任何既有 capability；与 `docs-*` 文档型 change 范式一致，CLI 代码行为不变，仅固化为文档契约。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 本 capability 是文档型：被规范的「系统行为」即「文档 SHALL 表述的内容」。`scripts/chrome-agent-cli.mjs` 中既成的同步代码是输入事实，本 spec 不要求改变其行为，只要求项目文档完整、准确地表述该契约。

## ADDED Requirements

### Requirement: tracked-files-registry-documented

The document `docs/playbooks/chrome-agent-global-install.md` SHALL enumerate the complete set of tracked files that participate in global skill/runtime sync.

The enumerated list SHALL be exactly:

- `scripts/chrome-agent-runtime.mjs`
- `scripts/chrome-agent-cli.mjs`
- `skills/chrome-agent/SKILL.md`

The document SHALL note that a change to `scripts/chrome-agent-cli.mjs` triggers a re-copy of the runtime file (`chrome-agent.mjs`), because the cli is a tracked-file gate, not a copy target itself.

#### Scenario: operator-locates-tracked-files

- **WHEN** an operator needs to know which source files affect the global copies
- **THEN** the playbook SHALL list exactly the three tracked files above in one place
- **AND** SHALL clarify that `chrome-agent-cli.mjs` is a trigger, not a destination

### Requirement: auto-update-behind-origin-documented

The document `docs/playbooks/chrome-agent-global-install.md` SHALL document that `chrome-agent doctor` auto-updates the global runtime (`~/.agents/scripts/chrome-agent.mjs`) and skill (`~/.agents/skills/chrome-agent/SKILL.md`) only when the source repository HEAD is an ancestor of `origin/main` (i.e. behind) AND a tracked file differs between HEAD and `origin/main`.

The document SHALL state that this path returns `partial_success` with a skill-reload hint.

#### Scenario: behind-origin-with-tracked-changes

- **WHEN** the source repo is behind `origin/main` and a tracked file changed
- **THEN** the playbook SHALL state that doctor auto-copies the tracked sources to the global destinations and refreshes the installed-hash to the current HEAD
- **AND** SHALL instruct the operator to reload the skill

#### Scenario: behind-origin-without-tracked-changes

- **WHEN** the source repo is behind `origin/main` but no tracked file changed
- **THEN** the playbook SHALL state that `repo_freshness` is ok and no update is performed

### Requirement: ahead-of-origin-sync-gap-documented

The document `docs/playbooks/chrome-agent-global-install.md` SHALL document that when the source repository HEAD is ahead of `origin/main` (unpushed local commits), `repo_freshness` reports `ahead` and is ok, and doctor does NOT auto-update the global copies.

The document SHALL state that in this state the global copies are stale relative to local HEAD and that the operator must either sync manually (see `manual-sync-procedure-documented`) or `git push` first so the normal behind-path applies on other machines.

#### Scenario: ahead-of-origin-detected

- **WHEN** local HEAD is ahead of `origin/main` with unpushed commits touching a tracked file
- **THEN** the playbook SHALL explicitly state that auto-update does not fire
- **AND** SHALL route the operator to the manual-sync procedure or to `git push`

### Requirement: manual-sync-procedure-documented

The document `docs/playbooks/chrome-agent-global-install.md` SHALL include a procedure (Case 6: Manually sync global copies) for when local HEAD is ahead of `origin/main` or when changes must take effect without waiting for the next doctor run.

The procedure SHALL consist of exactly these steps:

1. Copy `scripts/chrome-agent-runtime.mjs` to `~/.agents/scripts/chrome-agent.mjs` and make it executable.
2. Copy `skills/chrome-agent/SKILL.md` to `~/.agents/skills/chrome-agent/SKILL.md`.
3. Write the current HEAD (`git rev-parse HEAD`) to `~/.agents/scripts/.chrome-agent-installed-hash`.
4. Validate with `chrome-agent doctor --format json` and reload the skill (restart session) because `SKILL.md` may have changed.

#### Scenario: operator-syncs-ahead-of-origin

- **WHEN** an operator has unpushed tracked-file changes and needs them active globally now
- **THEN** the playbook SHALL provide the four-step manual-sync procedure
- **AND** the procedure SHALL include refreshing the installed-hash to the current HEAD

### Requirement: installed-hash-semantics-documented

The document `docs/playbooks/chrome-agent-global-install.md` SHALL include a section describing the semantics of `~/.agents/scripts/.chrome-agent-installed-hash`.

The section SHALL state:

- The file records the commit SHA captured at last sync; its value equals `git rev-parse HEAD`, NOT a hash of file contents.
- The file seeds doctor's incremental freshness check.
- Any manual sync MUST refresh it, otherwise subsequent doctor runs may misjudge freshness.

#### Scenario: operator-misreads-hash-file

- **WHEN** an operator sees global file content sha1 already matching the source but the installed-hash still pointing at an older commit
- **THEN** the section SHALL explain that the hash records a commit, not content
- **AND** SHALL explain that a manual sync must still refresh it to the current HEAD

### Requirement: agents-md-governance-anchor

The document `AGENTS.md` SHALL provide a governance anchor that routes sync obligations to the playbook.

In §0.5 Development Hard Constraints (the constraint table where C4 「引擎版本同步」 lives), `AGENTS.md` SHALL include a new constraint row (ID C10, the next free slot since C1-C9 are taken, appended after C9 to preserve the table's numeric ordering). The row SHALL cross-reference C4 as the analogous 「改 X 后必须同步 Y」 pattern, state that after modifying any tracked file (`scripts/chrome-agent-runtime.mjs`, `scripts/chrome-agent-cli.mjs`, `skills/chrome-agent/SKILL.md`) the operator must sync the changes to the global copies and refresh `~/.agents/scripts/.chrome-agent-installed-hash`, and SHALL link to `docs/playbooks/chrome-agent-global-install.md`.

In §11 Prerequisite Reading, `AGENTS.md` SHALL include a task row for "改 runtime/cli/SKILL.md" whose required reading is `docs/playbooks/chrome-agent-global-install.md`, with focus points covering tracked files, ahead / manual sync, and installed-hash refresh.

#### Scenario: agent-locates-sync-flow-from-governance

- **WHEN** an agent or operator modifies a tracked file and consults `AGENTS.md`
- **THEN** §0.5 Hard Constraints SHALL surface the sync obligation (as the C10 row, cross-referencing C4) with a link to the playbook
- **AND** §11 SHALL list the playbook as required reading for the "改 runtime/cli/SKILL.md" task type
