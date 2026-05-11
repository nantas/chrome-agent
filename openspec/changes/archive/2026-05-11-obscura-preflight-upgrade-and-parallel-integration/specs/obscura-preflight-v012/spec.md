# Specification Delta

## Capability 对齐（已确认）

- Capability: `obscura-preflight-v012`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 确认所有 6 项 capability

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: obcura-version-update

The system SHALL upgrade the pinned Obscura version from v0.1.0 to v0.1.2, and SHALL ensure both `obscura` and `obscura-worker` binaries are installed and verifiable.

#### Scenario: preflight-download-macos-arm64
- **WHEN** preflight runs on macOS ARM64 and neither `OBSCURA_CLI_PATH` nor managed install is valid
- **THEN** the system SHALL download `obscura-aarch64-macos.tar.gz` from `https://github.com/h4ckf0r0day/obscura/releases/download/v0.1.2/obscura-aarch64-macos.tar.gz`, extract both `obscura` and `obscura-worker` to `$HOME/.cache/chrome-agent-obscura/bin/`, and verify both are executable

#### Scenario: preflight-download-linux-x86_64
- **WHEN** preflight runs on Linux x86_64 and neither `OBSCURA_CLI_PATH` nor managed install is valid
- **THEN** the system SHALL download the `obscura-x86_64-linux.tar.gz` variant and follow the same extraction/verification steps

#### Scenario: preflight-verify-worker
- **WHEN** Obscura binaries are installed or resolved from `OBSCURA_CLI_PATH`
- **THEN** the system SHALL verify that `obscura-worker` exists in the same directory as `obscura`, and SHALL run `obscura-worker --help` (or equivalent) to confirm it is executable

#### Scenario: preflight-fallback
- **WHEN** download fails or platform has no precompiled release
- **THEN** the system SHALL offer source compilation from local clone or GitHub, following existing Obscura CLI preflight procedures

### Requirement: obcura-persistent-env-confirmation

The system SHALL NOT silently overwrite `OBSCURA_CLI_PATH` in persistent shell config.

#### Scenario: env-path-conflict
- **WHEN** `OBSCURA_CLI_PATH` exists in `/Users/nantas-agent/.zshenv` with a different value than the managed install path
- **THEN** the system SHALL treat this as a conflict, report it, and require explicit user approval before replacing
