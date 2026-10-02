# Specification Delta

## Capability 对齐（已确认）

- Capability: `governance`
- 来源: `proposal.md` → Modified Capabilities
- 变更类型: modified
- 用户确认摘要: 2026-10-02 用户回复“能力确认”，确认 Explore 入口修复和交接命名修复。

## 规范真源声明

- 本文件为本次 change 的行为规范真源；design / tasks / verification 必须引用本文件。
- 项目页面回写不得替代本文件。

## MODIFIED Requirements

### Requirement: handoff-storage-path

Handoff documents SHALL be stored under `outputs/handoffs/<run-tag>/handoff.md` within the chrome-agent repository.

The `<run-tag>` SHALL follow the same naming convention as existing run directories: `<timestamp>-<command>-<slug>`. The slug SHALL be derived from the target using the same normalization and 80-character maximum as existing run-directory slugification, with `target` as the fallback when normalization yields an empty string. Timestamp generation SHALL NOT be treated as a source of target slug.

The `outputs/handoffs/` directory SHALL inherit the same .gitignore treatment as `outputs/` (excluded from version control).

#### Scenario: handoff-with-run-dir

- **WHEN** a handoff is generated for a command that already has a run directory
- **THEN** the handoff SHALL be created under `outputs/handoffs/<run-tag>/`
- **THEN** the handoff SHALL reference the run directory path in its Context section
- **THEN** the handoff SHALL NOT duplicate files already in the run directory

#### Scenario: handoff-without-run-dir

- **WHEN** a handoff is generated for a command that exited before creating a run directory (e.g., preflight failure)
- **THEN** the handoff SHALL still be written to `outputs/handoffs/<run-tag>/`
- **THEN** the run-tag SHALL still use the standard timestamp-command-slug format

#### Scenario: target-derived-slug
- **WHEN** an internal failure generates a handoff for `https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1`
- **THEN** its run-tag SHALL end with `<command>-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1`
- **AND** the JSON handoff_path SHALL point to the written Markdown document with the original target and error details.

#### Scenario: empty-normalized-slug
- **WHEN** a handoff target normalizes to an empty slug
- **THEN** its run-tag SHALL end with `<command>-target`, with or without a run directory.

#### Scenario: bounded-normalized-slug
- **WHEN** a target includes uppercase letters, punctuation, or a normalized slug longer than 80 characters
- **THEN** the handoff slug SHALL use lowercase ASCII letters/digits with hyphen separators and SHALL contain at most 80 characters.

## 冻结规范合并定位

归档时替换 `openspec/specs/governance/handoff.md` 的 handoff-storage-path 完整块，保留其余要求，不新建平行的 `governance/spec.md` 真源。
