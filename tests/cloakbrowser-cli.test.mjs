import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const scriptPath = path.resolve(__dirname, "..", "scripts", "cloakbrowser-cli.sh");

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

function parseStatus(stdout) {
  const status = (stdout.match(/^STATUS=(.+)$/m) || [])[1] || "";
  const source = (stdout.match(/^SOURCE=(.+)$/m) || [])[1] || "";
  const resolvedCliPath = (stdout.match(/^RESOLVED_CLI_PATH=(.+)$/m) || [])[1] || "";
  return { status, source, resolvedCliPath };
}

// If cloakbrowser managed venv already exists, these tests verify detection.
// If it doesn't, --no-install mode will exit non-zero with STATUS line still emitted.

test("cloakbrowser-cli.sh preflight emits STATUS= and RESOLVED_CLI_PATH= lines", () => {
  const { stdout } = runPreflight(true);
  const { status, source, resolvedCliPath } = parseStatus(stdout);
  assert.ok(status, "STATUS line should be present");
  // If available: STATUS=available; if missing: script exits non-zero
  // In both cases we verify the output format
  assert.ok(resolvedCliPath, "RESOLVED_CLI_PATH line should be present");
  assert.ok(resolvedCliPath.endsWith("/bin/python"), "RESOLVED_CLI_PATH should point to bin/python");
});

test("cloakbrowser-cli.sh preflight --no-install works without auth/network", () => {
  const { exitCode, stdout, stderr } = runPreflight(true);
  const { status } = parseStatus(stdout);
  // --no-install should never trigger `uv`, so exit 0 or 2 depending on state
  assert.ok([0, 2].includes(exitCode), `exit code should be 0 or 2, got ${exitCode}`);
  // Ensure the script didn't crash
  assert.ok(!stderr.includes("command not found"), "script should not crash with 'command not found'");
});
