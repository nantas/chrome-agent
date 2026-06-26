import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { resolveAppPython } from "../scripts/lib/python-resolver.mjs";

// Resolves the Python interpreter for application-layer spawns.
// Priority: CHROME_AGENT_PYTHON env > .venv/bin/python > python3.

function makeTempRepo() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "ca-py-"));
}

function cleanup(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

test("resolveAppPython falls back to python3 when no venv and no env override", () => {
  const repoRoot = makeTempRepo();
  const saved = process.env.CHROME_AGENT_PYTHON;
  delete process.env.CHROME_AGENT_PYTHON;
  try {
    assert.equal(resolveAppPython(repoRoot), "python3");
  } finally {
    if (saved !== undefined) process.env.CHROME_AGENT_PYTHON = saved;
    cleanup(repoRoot);
  }
});

test("resolveAppPython uses .venv/bin/python when venv exists", () => {
  const repoRoot = makeTempRepo();
  const venvPython = path.join(repoRoot, ".venv", "bin", "python");
  fs.mkdirSync(path.dirname(venvPython), { recursive: true });
  fs.writeFileSync(venvPython, "#!/usr/bin/env python3\n");
  const saved = process.env.CHROME_AGENT_PYTHON;
  delete process.env.CHROME_AGENT_PYTHON;
  try {
    assert.equal(resolveAppPython(repoRoot), venvPython);
  } finally {
    if (saved !== undefined) process.env.CHROME_AGENT_PYTHON = saved;
    cleanup(repoRoot);
  }
});

test("resolveAppPython prefers CHROME_AGENT_PYTHON env over venv and python3", () => {
  const repoRoot = makeTempRepo();
  const venvPython = path.join(repoRoot, ".venv", "bin", "python");
  fs.mkdirSync(path.dirname(venvPython), { recursive: true });
  fs.writeFileSync(venvPython, "#!/usr/bin/env python3\n");
  const saved = process.env.CHROME_AGENT_PYTHON;
  process.env.CHROME_AGENT_PYTHON = "/custom/python3";
  try {
    assert.equal(resolveAppPython(repoRoot), "/custom/python3");
  } finally {
    if (saved === undefined) delete process.env.CHROME_AGENT_PYTHON;
    else process.env.CHROME_AGENT_PYTHON = saved;
    cleanup(repoRoot);
  }
});

// Regression guard: verify resolveAppPython maintains the same 3-priority
// resolution behavior (CHROME_AGENT_PYTHON > .venv/bin/python > python3)
// as the renamed resolveExplorePython.
test("resolveAppPython regression guard: same resolution priorities as resolveExplorePython", () => {
  const repoRoot = makeTempRepo();
  const saved = process.env.CHROME_AGENT_PYTHON;
  delete process.env.CHROME_AGENT_PYTHON;
  try {
    // 1. No venv, no env → python3 fallback
    assert.equal(resolveAppPython(repoRoot), "python3");

    // 2. Create venv → resolves to .venv/bin/python
    const venvPython = path.join(repoRoot, ".venv", "bin", "python");
    fs.mkdirSync(path.dirname(venvPython), { recursive: true });
    fs.writeFileSync(venvPython, "#!/usr/bin/env python3\n");
    assert.equal(resolveAppPython(repoRoot), venvPython);

    // 3. Set env override → env wins over venv
    process.env.CHROME_AGENT_PYTHON = "/opt/custom/python3";
    assert.equal(resolveAppPython(repoRoot), "/opt/custom/python3");

    // 4. Remove venv, keep env → env still wins
    fs.rmSync(venvPython);
    assert.equal(resolveAppPython(repoRoot), "/opt/custom/python3");

    // 5. Remove env → back to python3
    delete process.env.CHROME_AGENT_PYTHON;
    assert.equal(resolveAppPython(repoRoot), "python3");
  } finally {
    if (saved !== undefined) process.env.CHROME_AGENT_PYTHON = saved;
    else delete process.env.CHROME_AGENT_PYTHON;
    cleanup(repoRoot);
  }
});

// Verify the single root requirements.txt exists with all 4 app-layer dependencies.
test("root requirements.txt exists and contains all 4 app-layer dependencies", () => {
  const reqPath = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..", "requirements.txt");
  const content = fs.readFileSync(reqPath, "utf8");
  assert.ok(content.includes("beautifulsoup4"), "missing beautifulsoup4");
  assert.ok(content.includes("pyyaml"), "missing pyyaml");
  assert.ok(content.includes("selectolax"), "missing selectolax");
  assert.ok(content.includes("markdownify"), "missing markdownify");
  assert.ok(!fs.existsSync(path.join(path.dirname(reqPath), "scripts", "explore", "requirements.txt")), 
    "scripts/explore/requirements.txt should not exist");
});
