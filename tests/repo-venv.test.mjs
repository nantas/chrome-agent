import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const scriptPath = path.resolve(__dirname, "..", "scripts", "repo-venv.sh");

function runPreflight(noInstall = false) {
  const args = [scriptPath, "preflight"];
  if (noInstall) args.push("--no-install");
  const result = spawnSync("bash", args, {
    encoding: "utf8",
    timeout: 30000,
  });
  const stdout = result.stdout || "";
  const stderr = result.stderr || "";
  return { exitCode: result.status, stdout, stderr };
}

// Parse STATUS= and SOURCE= lines from output
function parseStatus(stdout) {
  const status = (stdout.match(/^STATUS=(.+)$/m) || [])[1] || "";
  const source = (stdout.match(/^SOURCE=(.+)$/m) || [])[1] || "";
  return { status, source };
}

test("repo-venv.sh preflight with venv available returns STATUS=available", () => {
  const { exitCode, stdout } = runPreflight(false);
  assert.equal(exitCode, 0, `exit code should be 0, got ${exitCode}`);
  const { status, source } = parseStatus(stdout);
  assert.equal(status, "available", `STATUS should be available, got ${status}`);
  assert.equal(source, "managed", `SOURCE should be managed, got ${source}`);
});

test("repo-venv.sh preflight --no-install with venv available returns STATUS=available", () => {
  const { exitCode, stdout } = runPreflight(true);
  assert.equal(exitCode, 0, `exit code should be 0, got ${exitCode}`);
  const { status, source } = parseStatus(stdout);
  assert.equal(status, "available", `STATUS should be available, got ${status}`);
  assert.equal(source, "managed", `SOURCE should be managed, got ${source}`);
});

test("repo-venv.sh preflight --no-install emit STATUS= and SOURCE= lines", () => {
  const { stdout } = runPreflight(true);
  const { status, source } = parseStatus(stdout);
  assert.ok(status, "STATUS line should be present");
  assert.ok(source, "SOURCE line should be present");
  // Verify VENV_PYTHON and REQUIREMENTS lines are also present
  assert.ok(stdout.includes("VENV_PYTHON="), "VENV_PYTHON line should be present");
  assert.ok(stdout.includes("REQUIREMENTS="), "REQUIREMENTS line should be present");
});
