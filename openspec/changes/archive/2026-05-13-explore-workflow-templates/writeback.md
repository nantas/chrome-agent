# Writeback Plan

## Targets

| Target | Action | Evidence |
|--------|--------|----------|
| `AGENTS.md` | Update §3 workflow routing rules to describe deep discovery path | File diff showing new paragraph in "工作流路由规则" |
| `docs/playbooks/explore-workflow-conduct.md` | Create new playbook documenting the explore workflow | New file with operational guidance |

## Field Mapping

| Source (implementation) | Target (AGENTS.md) | Field |
|------------------------|--------------------|-------|
| `scripts/explore/` module list | §3 路由规则 | Engine chain order, fallback logic |
| `sites/templates/` | §7 策略库治理 | Template directory structure |
| `specs/explore-workflow/spec.md` | docs/playbooks/ | Behavior reference |

## Preconditions

- [x] All core modules implemented and verified
- [x] `verification.md` generated
- [x] No uncommitted blocking changes in working tree

## Execution Log

| Step | Time | Result |
|------|------|--------|
| Update AGENTS.md | 2026-05-12 | ✓ Added Explore Deep Discovery path description in §3 工作流路由规则 |
| Create docs/playbooks/explore-workflow-conduct.md | 2026-05-12 | ✓ Complete playbook with all 8 phases documented |
