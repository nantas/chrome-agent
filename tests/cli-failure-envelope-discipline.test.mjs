/** Static discipline check: failure-envelope-single-implementation.
 *
 * Spec: cleanup-cli-and-converter-dead-code / failure-envelope-single-implementation,
 *       scenario all-internal-failure-sites-delegate-to-builder.
 *
 * cli.mjs command handlers SHALL route internal-failure construction through a
 * single internalFailure builder, not inline the generateHandoff(...) +
 * makeResult("failure", {...}) envelope per call site. This test greps cli.mjs
 * for inline envelope residues (a generateHandoff( followed within ~12 lines by
 * a makeResult(..., "failure", ...)) and fails if any remain (the crawl-prefixed
 * crawlInternalError thin wrapper is exempt — it calls internalFailure, not
 * generateHandoff directly).
 *
 * ponytail: ceiling — the 12-line window is heuristic; a pathological split
 * (handoff at line N, makeResult at line N+15) would evade detection. No such
 * split exists currently; refine if one appears.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const CLI_PATH = new URL("../scripts/chrome-agent-cli.mjs", import.meta.url);
const SRC = fs.readFileSync(CLI_PATH, "utf8");
const LINES = SRC.split("\n");

/** Find generateHandoff( call sites (not the function definition). */
function findHandoffCallLines() {
  const sites = [];
  LINES.forEach((line, i) => {
    if (line.includes("generateHandoff(") && !line.trim().startsWith("function generateHandoff")) {
      sites.push(i + 1); // 1-indexed
    }
  });
  return sites;
}

/** For a given handoff call line (1-indexed), check if a makeResult(...,"failure")
 *  follows within WINDOW lines. The makeResult call is often multi-line, so we
 *  scan a chunk from the handoff line forward for a makeResult( whose argument
 *  list (possibly spanning several lines) contains "failure". */
function followingFailureResult(handoffLine1, WINDOW = 15) {
  // Look for makeResult( in the window; when found, grab a chunk covering its
  // likely multi-line argument list and test for the "failure" literal.
  for (let i = handoffLine1; i < Math.min(handoffLine1 + WINDOW, LINES.length); i++) {
    const line = LINES[i]; // 0-indexed
    if (/makeResult\(/.test(line)) {
      // Grab this line + up to 8 following (the makeResult arg list span)
      const chunk = LINES.slice(i, i + 9).join("\n");
      if (/"failure"|'failure'/.test(chunk)) return line.trim();
    }
  }
  return null;
}

test("no inline failure-envelope residues — all internal-failure sites delegate to internalFailure", () => {
  const handoffSites = findHandoffCallLines();
  // Exempt the internalFailure builder's own body — it legitimately contains
  // generateHandoff(...) + makeResult("failure", {...}) because it IS the builder.
  const ifStart = LINES.findIndex((l) => l.startsWith("function internalFailure("));
  const ifEnd = ifStart >= 0 ? LINES.indexOf("}", ifStart) : -1;
  const residues = [];
  for (const ln of handoffSites) {
    if (ifStart >= 0 && ln > ifStart + 1 && ln <= ifEnd + 1) continue; // skip builder body
    const failureLine = followingFailureResult(ln);
    if (failureLine !== null) {
      residues.push({ handoffLine: ln, failureLine });
    }
  }
  assert.deepEqual(residues, [],
    "cli.mjs must route internal-failure construction through internalFailure builder. " +
    "Inline generateHandoff(...) + makeResult('failure', {...}) blocks are FORBIDDEN. " +
    "Spec: failure-envelope-single-implementation. Residues:\\n" +
    residues.map((r) => `  handoff@L${r.handoffLine} → failure@${r.failureLine}`).join("\\n"));
});
