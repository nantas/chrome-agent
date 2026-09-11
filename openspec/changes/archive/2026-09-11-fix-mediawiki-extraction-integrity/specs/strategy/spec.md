# Specification Delta

## Capability 对齐（已确认）

- Capability: `strategy`
- 来源: `proposal.md` / 用户授权“按照你建议的方案创建 change”。
- 变更类型: modified
- 用户确认摘要: 落实已讨论的抽取完整性修复范围；不自动恢复全站抓取。

## 规范真源声明

本文件是该 capability 在本 change 中的行为规范真源；design/tasks/verification SHALL 以此为依据，页面回写不得替代 spec delta。

## ADDED Requirements

### Requirement: stable-registry-publication-format
Freeze SHALL preserve the existing registry indentation, trailing newline convention, top-level/member key order and relative order of unrelated entries. Updating an existing domain SHALL retain its entry position; new domains SHALL append. A newly created registry SHALL use four-space indentation. Only the target domain's metadata SHALL change semantically. Existing validation, atomic publication and rollback behavior SHALL remain in force.

#### Scenario: four-space-existing-registry
- **WHEN** a domain is frozen into a registry using four-space indentation
- **THEN** the result SHALL retain four-space indentation and unrelated entries SHALL NOT be reordered or changed.

#### Scenario: repeated-freeze
- **WHEN** the same unchanged strategy is frozen twice
- **THEN** the second registry publication SHALL be byte-identical to the first.

#### Scenario: failed-publication
- **WHEN** freeze validation or publication fails
- **THEN** the prior strategy and registry SHALL be restored according to the existing lifecycle contract.
