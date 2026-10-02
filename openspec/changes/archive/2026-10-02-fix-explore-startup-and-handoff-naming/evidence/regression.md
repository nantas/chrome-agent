# Regression evidence — 2026-10-02

## Explore entry RED → GREEN

Command: `python3 -m unittest tests.test_explore_startup -v`

Before fix: 1 test failed in 0.186s. The real main.py child raised:

```text
main.py:33 → architecture_gate.py:11
ModuleNotFoundError: No module named 'scripts'
```

After fix: external cwd test passed in 0.118s; adding repository cwd coverage produced 2 passing tests in 0.185s. No PYTHONPATH injection or module-import substitution was used.

## Handoff RED → GREEN

Command: `node --test tests/explore-handoff.test.mjs`

Before fix: real CLI startup test passed; target-slug assertion failed on:

```text
Actual: 20261002T103417-explore-undefined
Expected suffix: explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1
```

After fix: both tests passed; additional no-runDir/empty slug/uppercase punctuation/80-character cases produced 6/6 passing tests. A valid Unicode-host URL (`https://例子/`) covers empty ASCII normalization; malformed targets are correctly rejected by existing URL handling.

## Full regression

`python3 -m unittest discover -s tests -v`: 185 tests passed.

`node --test tests/*.test.mjs`: first run 113/114 passed; existing repo-venv test assumed an available venv but got repaired during first provisioning. Second run after provisioning: 114/114 passed. No repo-venv source or test modifications.

## Real original command

Executed from /tmp with PYTHONPATH removed:

`env -u PYTHONPATH chrome-agent explore https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1 --format json`

Exit 1, result failure. The entry reached main() and scaffold generate(); original scripts import failure is absent. Handoff uses the correct target slug. New independent error:

```text
ValueError: extraction_schema:
extraction.cleanup[0] = strip_edit_sections (unsupported operation name)
extraction.cleanup[1] = strip_toc (unsupported operation name)
```

New handoff: `outputs/handoffs/20261002T103634-explore-darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1/handoff.md`.

No further website workflow dispatch or extraction performed. Website Explore completion is not claimed.

## Global synchronization and doctor

Runtime and skill copied according to C10/Case 6; cmp confirmed both source/destination pairs identical. Installed hash equals current HEAD: f86c49339249542c4d95d4c65bb299e5c81e8318. CLI itself remains repo-backed.

`chrome-agent doctor --format json`: success.

`chrome-agent doctor --check capabilities --format json`: success; registry consistent with code, specs, AGENTS.md.

`git diff --check`: pass. No `[DEBUG-` instrumentation in changed source/tests. Temporary CLI fixtures cleaned by test teardown. Existing package-lock.json user change preserved.

OpenSpec strict validation: pass. All 15 apply tasks complete; archive-time frozen spec merges completed on 2026-10-02 and are recorded in writeback.md.
