# Specification Delta

## Capability 对齐（已确认）

- Capability: `doctor-repo-freshness`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: doctor 检查项新增 `explore_deps`，检查 `bs4` 和 `yaml` 的 Python 导入可用性

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: explore-python-deps-check

`chrome-agent doctor` SHALL include an `explore_deps` check item that verifies the Python packages required by `scripts/explore/main.py` are importable.

The check SHALL execute `python3 -c "import bs4, yaml; print('ok')"` and evaluate the exit code.

#### Scenario: explore-deps-available

- **WHEN** both `bs4` and `yaml` are importable (exit code 0)
- **THEN** the `explore_deps` check item SHALL be marked `ok: true`
- **THEN** `detail` SHALL read `"bs4, yaml available"`

#### Scenario: explore-deps-missing

- **WHEN** either `bs4` or `yaml` is not importable (non-zero exit code)
- **THEN** the `explore_deps` check item SHALL be marked `ok: false`
- **THEN** `detail` SHALL read `"missing: bs4 or yaml. Install: pip3 install beautifulsoup4 pyyaml"`

#### Scenario: doctor-result-with-explore-deps-failure

- **WHEN** `explore_deps` is `ok: false` and no other checks are broken
- **THEN** doctor's overall `result` SHALL be `"partial_success"`
- **THEN** `summary` SHALL include `explore_deps` in the list of failed checks
- **THEN** `next_action` SHALL include the installation command for the missing packages

#### Scenario: python3-not-found

- **WHEN** the `python3` binary is not available or the spawn fails for any reason other than import error
- **THEN** the `explore_deps` check item SHALL be marked `ok: false`
- **THEN** `detail` SHALL include the spawn error reason
