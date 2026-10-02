import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TARGET = "https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1";
const TARGET_SLUG = "darkestdungeon-wiki-gg-wiki-darkest-dungeon-wiki-1";

function writeExecutable(filename, source) {
  fs.writeFileSync(filename, source);
  fs.chmodSync(filename, 0o755);
}

function runExplore(t, target = TARGET, missingDeps = false) {
  const temporary = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "explore-handoff-")));
  t.after(() => fs.rmSync(temporary, { recursive: true, force: true }));
  const root = path.join(temporary, "repo");
  fs.mkdirSync(root);
  fs.cpSync(path.join(REPO_ROOT, "scripts"), path.join(root, "scripts"), {
    recursive: true, filter: (source) => !source.includes("__pycache__"),
  });
  fs.symlinkSync(path.join(REPO_ROOT, "node_modules"), path.join(root, "node_modules"));
  fs.writeFileSync(path.join(root, "AGENTS.md"), "# Offline fixture\n");
  fs.mkdirSync(path.join(root, "sites", "strategies"), { recursive: true });
  fs.writeFileSync(path.join(root, "sites", "strategies", "registry.json"), '{"strategies":[]}');
  writeExecutable(path.join(root, "scripts", "scrapling-cli.sh"),
    '#!/bin/bash\nset -euo pipefail\nprintf "%s\\n" "STATUS=ready"\n');
  // Replace only the engine/network boundary. main.py and its package imports stay real.
  fs.writeFileSync(path.join(root, "scripts", "explore", "probe_chain.py"),
    'def probe(*args):\n    raise RuntimeError("OFFLINE_PROBE_REACHED")\n');
  const env = { ...process.env };
  delete env.PYTHONPATH;
  env.CHROME_AGENT_PYTHON = process.env.CHROME_AGENT_PYTHON || "python3";
  if (missingDeps) {
    const fakePython = path.join(temporary, "missing-python");
    writeExecutable(fakePython,
      '#!/bin/bash\nset -euo pipefail\nprintf "%s\\n" "ModuleNotFoundError: No module named bs4" >&2\nexit 1\n');
    env.CHROME_AGENT_PYTHON = fakePython;
  }
  const child = spawnSync(process.execPath, [path.join(root, "scripts", "chrome-agent-cli.mjs"),
    "explore", target, "--format", "json"], {
    cwd: temporary, env, encoding: "utf8", timeout: 15000,
  });
  assert.equal(child.error, undefined);
  assert.equal(child.status, 1, child.stderr || child.stdout);
  const result = JSON.parse(child.stdout);
  assert.equal(result.result, "failure");
  assert.ok(path.isAbsolute(result.handoff_path));
  assert.ok(result.handoff_path.startsWith(path.join(root, "outputs", "handoffs") + path.sep));
  const document = fs.readFileSync(result.handoff_path, "utf8");
  assert.ok(document.includes(target));
  assert.ok(result.next_action.includes(result.handoff_path));
  return { result, document, root };
}

test("real strategy-gap CLI starts the real Explore entry without PYTHONPATH", (t) => {
  const { result, document } = runExplore(t);
  assert.match(document, /OFFLINE_PROBE_REACHED/);
  assert.doesNotMatch(document, /No module named 'scripts'/);
  assert.equal(result.command, "explore");
});

test("handoff with run directory uses target slug and preserves error context", (t) => {
  const { result, document } = runExplore(t);
  assert.match(path.basename(path.dirname(result.handoff_path)),
    new RegExp(`^\\d{8}T\\d{6}-explore-${TARGET_SLUG}$`));
  assert.match(document, /OFFLINE_PROBE_REACHED/);
  assert.match(document, /\*\*Exit code\*\*: 1/);
  assert.match(document, new RegExp(`outputs/\\d{8}T\\d{6}-explore-${TARGET_SLUG}`));
});

test("handoff before a run directory exists still uses target slug", (t) => {
  const { result, document, root } = runExplore(t, TARGET, true);
  assert.match(path.basename(path.dirname(result.handoff_path)),
    new RegExp(`^\\d{8}T\\d{6}-explore-${TARGET_SLUG}$`));
  assert.match(document, /missing: bs4/);
  assert.doesNotMatch(document, /\| Run directory \|/);
  assert.deepEqual(fs.readdirSync(path.join(root, "outputs")), ["handoffs"]);
});

test("handoff falls back to target when slug normalization is empty", (t) => {
  const { result } = runExplore(t, "https://例子/", true);
  assert.match(path.basename(path.dirname(result.handoff_path)), /^\d{8}T\d{6}-explore-target$/);
});

test("handoff normalizes uppercase and punctuation", (t) => {
  const { result } = runExplore(t, "https://EXAMPLE.org/A_B?C=1", true);
  assert.match(path.basename(path.dirname(result.handoff_path)),
    /^\d{8}T\d{6}-explore-example-org-a-b-c-1$/);
});

test("handoff bounds the target slug to 80 characters", (t) => {
  const { result } = runExplore(t, `https://${"A".repeat(100)}.org/`, true);
  assert.match(path.basename(path.dirname(result.handoff_path)),
    new RegExp(`^\\d{8}T\\d{6}-explore-${"a".repeat(80)}$`));
});
