#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

const DEFAULT_REPO_REF = "repo://chrome-agent";

function printHelp() {
  const text = `Usage: chrome-agent [--repo <path|repo://id>] [--format json|text] <command> [args]

Commands:
  explore <url>    Analyze strategy coverage and repository-local workflow fit.
  fetch <url>      Run the repository-local content retrieval workflow.
  crawl <url>      Run strategy-guided crawl with bounded traversal.
  doctor           Validate launcher, repo resolution, repo shape, and prerequisites.
  clean            Remove disposable outputs by default.

Global options:
  --repo <value>   Explicit repository override. Accepts absolute path or repo://<id>.
  --format <mode>  Output mode: json or text. Default: text.
  -h, --help       Show this message.
`;
  process.stdout.write(text);
}

function parseArgs(argv) {
  const args = [...argv];
  let format = "text";
  let repoOverride = null;
  const positionals = [];

  for (let i = 0; i < args.length; i += 1) {
    const value = args[i];
    if (value === "--format" && i + 1 < args.length) {
      format = args[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--format=")) {
      format = value.slice("--format=".length);
      continue;
    }
    if (value === "--repo" && i + 1 < args.length) {
      repoOverride = args[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--repo=")) {
      repoOverride = value.slice("--repo=".length);
      continue;
    }
    if (!value.startsWith("-")) {
      positionals.push(value);
    }
  }

  return { format, repoOverride, command: positionals[0] ?? null, target: positionals[1] ?? null };
}

function renderResult(result, format) {
  if (format === "json") {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  const lines = [
    `result: ${result.result}`,
    `command: ${result.command}`,
    `target: ${result.target ?? "none"}`,
    `repo_ref: ${result.repo_ref ?? "none"}`,
    `summary: ${result.summary}`,
    "artifacts:",
  ];
  for (const artifact of result.artifacts ?? []) {
    const lifecycle = artifact.lifecycle ? ` [${artifact.lifecycle}]` : "";
    const action = artifact.action ? ` (${artifact.action})` : "";
    lines.push(`- ${artifact.path}${lifecycle}${action}`);
  }
  if ((result.artifacts ?? []).length === 0) {
    lines.push("- none");
  }
  lines.push(`next_action: ${result.next_action}`);
  process.stdout.write(`${lines.join("\n")}\n`);
}

function readRegistry() {
  const override = process.env.ORBITOS_REPO_REGISTRY;
  const registryPath = override || path.join(os.homedir(), ".config", "orbitos", "repo_registry.json");
  if (!fs.existsSync(registryPath)) {
    return { registryPath, data: null };
  }
  try {
    const parsed = JSON.parse(fs.readFileSync(registryPath, "utf8"));
    return { registryPath, data: parsed };
  } catch (error) {
    return { registryPath, data: null, error };
  }
}

function resolveRepoRef(repoRef, registry) {
  if (!repoRef.startsWith("repo://")) {
    return null;
  }
  const repoId = repoRef.slice("repo://".length);
  const repoPath = registry?.data?.repos?.[repoId]?.path;
  if (!repoPath) {
    return null;
  }
  return path.resolve(repoPath);
}

function isValidRepo(repoPath) {
  if (!repoPath) {
    return false;
  }
  const resolved = path.resolve(repoPath);
  return fs.existsSync(resolved) && fs.existsSync(path.join(resolved, "AGENTS.md"));
}

function resolveRepository(repoOverride) {
  const registry = readRegistry();
  const failures = [];

  if (repoOverride) {
    if (repoOverride.startsWith("repo://")) {
      const repoPath = resolveRepoRef(repoOverride, registry);
      if (isValidRepo(repoPath)) {
        return {
          ok: true,
          repoPath,
          repoRef: repoOverride,
          resolutionMode: "explicit_override",
          registryPath: registry.registryPath,
          fallbackUsed: false,
        };
      }
      failures.push(`Explicit repo override could not resolve: ${repoOverride}`);
    } else if (isValidRepo(repoOverride)) {
      return {
        ok: true,
        repoPath: path.resolve(repoOverride),
        repoRef: `path:${path.resolve(repoOverride)}`,
        resolutionMode: "explicit_override",
        registryPath: registry.registryPath,
        fallbackUsed: false,
      };
    } else {
      failures.push(`Explicit repo override is not a valid chrome-agent repository: ${repoOverride}`);
    }
  }

  const registryRepoPath = resolveRepoRef(DEFAULT_REPO_REF, registry);
  if (isValidRepo(registryRepoPath)) {
    return {
      ok: true,
      repoPath: registryRepoPath,
      repoRef: DEFAULT_REPO_REF,
      resolutionMode: "repo_registry",
      registryPath: registry.registryPath,
      fallbackUsed: false,
    };
  }
  failures.push(`repo-registry did not resolve ${DEFAULT_REPO_REF} to a valid repository`);

  const envRepo = process.env.CHROME_AGENT_REPO;
  if (isValidRepo(envRepo)) {
    return {
      ok: true,
      repoPath: path.resolve(envRepo),
      repoRef: "env:CHROME_AGENT_REPO",
      resolutionMode: "env_fallback",
      registryPath: registry.registryPath,
      fallbackUsed: true,
    };
  }
  failures.push("CHROME_AGENT_REPO is missing or does not point to a valid repository");

  return {
    ok: false,
    failures,
    registryPath: registry.registryPath,
  };
}

function main() {
  const parsed = parseArgs(process.argv.slice(2));

  if (!parsed.command || parsed.command === "help" || process.argv.includes("--help") || process.argv.includes("-h")) {
    printHelp();
    process.exit(0);
  }

  const repoResolution = resolveRepository(parsed.repoOverride);
  if (!repoResolution.ok) {
    renderResult(
      {
        result: "failure",
        command: parsed.command,
        target: parsed.target,
        repo_ref: DEFAULT_REPO_REF,
        summary: `Repository resolution failed before dispatch. ${repoResolution.failures.join("; ")}.`,
        artifacts: [],
        next_action: `Register ${DEFAULT_REPO_REF} in ${repoResolution.registryPath} or set CHROME_AGENT_REPO to a valid repository, then retry.`,
      },
      parsed.format,
    );
    process.exit(1);
  }

  const repoCli = path.join(repoResolution.repoPath, "scripts", "chrome-agent-cli.mjs");
  if (!fs.existsSync(repoCli)) {
    renderResult(
      {
        result: "failure",
        command: parsed.command,
        target: parsed.target,
        repo_ref: repoResolution.repoRef,
        summary: `Resolved repository is missing scripts/chrome-agent-cli.mjs: ${repoResolution.repoPath}.`,
        artifacts: [],
        next_action: "Update the repository to a Phase 5-compatible revision and retry.",
      },
      parsed.format,
    );
    process.exit(1);
  }

  const child = spawnSync(
    process.execPath,
    [
      repoCli,
      "--resolved-repo",
      repoResolution.repoPath,
      "--resolved-repo-ref",
      repoResolution.repoRef,
      "--resolution-mode",
      repoResolution.resolutionMode,
      ...process.argv.slice(2),
    ],
    {
      stdio: "inherit",
      env: {
        ...process.env,
        CHROME_AGENT_DISPATCHED: "1",
      },
    },
  );

  if (child.error) {
    renderResult(
      {
        result: "failure",
        command: parsed.command,
        target: parsed.target,
        repo_ref: repoResolution.repoRef,
        summary: `Runtime dispatch failed: ${child.error.message}`,
        artifacts: [],
        next_action: "Inspect the local Node.js runtime and repository-local CLI implementation, then retry.",
      },
      parsed.format,
    );
    process.exit(1);
  }

  process.exit(child.status ?? 1);
}

main();
