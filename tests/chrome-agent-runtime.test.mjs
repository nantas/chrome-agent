import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const repoRoot = process.cwd();
const runtimeScript = path.join(repoRoot, "scripts", "chrome-agent-runtime.mjs");
const repoCliScript = path.join(repoRoot, "scripts", "chrome-agent-cli.mjs");

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeExecutable(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, "utf8");
  fs.chmodSync(filePath, 0o755);
}

function makeMockRepo(name = "mock-chrome-agent") {
  const root = makeTempDir(`${name}-`);
  fs.writeFileSync(path.join(root, "AGENTS.md"), "# mock\n", "utf8");
  writeExecutable(
    path.join(root, "scripts", "chrome-agent-cli.mjs"),
    `#!/usr/bin/env node
const args = process.argv.slice(2);
const take = (flag) => {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] ?? null : null;
};
const internalFlags = new Set(["--resolved-repo", "--resolved-repo-ref", "--resolution-mode", "--format", "--repo"]);
const positionals = [];
for (let i = 0; i < args.length; i += 1) {
  const value = args[i];
  if (internalFlags.has(value)) {
    i += 1;
    continue;
  }
  if (value.startsWith("--")) {
    continue;
  }
  positionals.push(value);
}
const result = {
  result: "success",
  command: positionals[0] ?? "doctor",
  target: positionals[1] ?? "runtime",
  repo_ref: take("--resolved-repo-ref"),
  summary: "mock repo cli invoked",
  artifacts: [],
  next_action: "none",
  workflow: "runtime_support",
  engine_path: \`mock:\${take("--resolution-mode")}\`,
  resolution_mode: take("--resolution-mode"),
};
process.stdout.write(JSON.stringify(result));
`,
  );
  return root;
}

function makeRepoRegistry(targetRepo) {
  const root = makeTempDir("repo-registry-");
  const registryPath = path.join(root, "repo_registry.json");
  fs.writeFileSync(
    registryPath,
    JSON.stringify({ repos: { "chrome-agent": { path: targetRepo } } }, null, 2),
    "utf8",
  );
  return registryPath;
}

function runNode(scriptPath, args, env = {}) {
  return spawnSync(process.execPath, [scriptPath, ...args], {
    cwd: repoRoot,
    env: { ...process.env, ...env },
    encoding: "utf8",
  });
}

test("runtime prefers CHROME_AGENT_REPO over default repo-registry lookup", () => {
  const envRepo = makeMockRepo("env-repo");
  const registryRepo = makeMockRepo("registry-repo");
  const registryPath = makeRepoRegistry(registryRepo);

  const result = runNode(runtimeScript, ["doctor", "--format", "json"], {
    CHROME_AGENT_REPO: envRepo,
    ORBITOS_REPO_REGISTRY: registryPath,
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.repo_ref, "env:CHROME_AGENT_REPO");
  assert.equal(payload.resolution_mode, "env_default");
  assert.equal(payload.engine_path, "mock:env_default");
});

test("runtime dispatches fetch, explore, and crawl through env_default without --repo", () => {
  const envRepo = makeMockRepo("env-repo");

  for (const [command, target] of [
    ["fetch", "https://example.com/article"],
    ["explore", "https://example.com/debug"],
    ["crawl", "https://example.com/list"],
  ]) {
    const result = runNode(runtimeScript, [command, target, "--format", "json"], {
      CHROME_AGENT_REPO: envRepo,
    });

    assert.equal(result.status, 0, `${command} failed: ${result.stderr}`);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.command, command);
    assert.equal(payload.repo_ref, "env:CHROME_AGENT_REPO");
    assert.equal(payload.resolution_mode, "env_default");
    assert.equal(payload.engine_path, "mock:env_default");
  }
});

test("runtime fails with env-first remediation when no override and env is invalid", () => {
  const registryRepo = makeMockRepo("registry-repo");
  const registryPath = makeRepoRegistry(registryRepo);
  const invalidRepo = path.join(os.tmpdir(), "missing-chrome-agent-repo");

  const result = runNode(runtimeScript, ["doctor", "--format", "json"], {
    CHROME_AGENT_REPO: invalidRepo,
    ORBITOS_REPO_REGISTRY: registryPath,
  });

  assert.equal(result.status, 1);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.result, "failure");
  assert.match(payload.summary, /CHROME_AGENT_REPO is missing or does not point to a valid repository/);
  assert.doesNotMatch(payload.summary, /repo-registry did not resolve/);
  assert.match(payload.next_action, /Set CHROME_AGENT_REPO to a valid chrome-agent repository or supply --repo <path\|repo:\/\/id>/);
});

test("runtime keeps explicit repo:// override working", () => {
  const registryRepo = makeMockRepo("registry-repo");
  const registryPath = makeRepoRegistry(registryRepo);

  const result = runNode(runtimeScript, ["--repo", "repo://chrome-agent", "doctor", "--format", "json"], {
    ORBITOS_REPO_REGISTRY: registryPath,
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.repo_ref, "repo://chrome-agent");
  assert.equal(payload.resolution_mode, "explicit_override");
  assert.equal(payload.engine_path, "mock:explicit_override");
});

test("repo cli doctor reports env_default instead of env_fallback", () => {
  const result = runNode(
    repoCliScript,
    [
      "--resolved-repo",
      repoRoot,
      "--resolved-repo-ref",
      "env:CHROME_AGENT_REPO",
      "--resolution-mode",
      "env_default",
      "doctor",
      "--format",
      "json",
    ],
    {
      CHROME_AGENT_REPO: repoRoot,
    },
  );

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.resolution_mode, "env_default");
  assert.match(payload.summary, /Resolved via CHROME_AGENT_REPO default/);
  assert.ok(payload.checks.some((check) => check.name === "env_default"));
  assert.ok(payload.checks.every((check) => check.name !== "env_fallback"));
  assert.equal(payload.next_action, "none");
});
