import fs from "node:fs";
import path from "node:path";
import process from "node:process";

// Resolves the Python interpreter for application-layer spawns.
// Priority:
//   1. CHROME_AGENT_PYTHON env override
//   2. repo-local venv at <repoRoot>/.venv/bin/python
//   3. system python3 (fallback, preserves prior behavior)
export function resolveAppPython(repoRoot) {
  const envPython = process.env.CHROME_AGENT_PYTHON;
  if (envPython) return envPython;
  const venvPython = path.join(repoRoot, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) return venvPython;
  return "python3";
}
