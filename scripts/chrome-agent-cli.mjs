#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import YAML from "yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const inferredRepoRoot = path.resolve(__dirname, "..");
const DEFAULT_REPO_REF = "repo://chrome-agent";

function printHelp() {
  const text = `Usage: chrome-agent [--format json|text] [--repo <path|repo://id>] <command> [args]

Commands:
  explore <url>          Run the explicit platform-analysis backend workflow.
  fetch <url>            Run the explicit content-retrieval backend workflow.
  crawl <url>            Run the explicit bounded-crawl backend workflow.
  doctor                 Validate launcher, repo resolution, repo shape, and Scrapling readiness.
  clean [--scope all]    Remove disposable outputs by default.

Command options:
  --entry-point <id>     Crawl from a specific declared entry point.
  --max-pages <n>        Maximum pages to traverse in crawl. Default: 3.
  --report               Force durable report emission to reports/.
  --no-report            Disable durable report emission for this run.
  --scope <scope>        Clean scope: disposable (default) or all.
  --format <mode>        Output mode: json or text. Default: text.
  -h, --help             Show this message.
`;
  process.stdout.write(text);
}

function parseArgs(argv) {
  const args = [...argv];
  const internal = {
    resolvedRepo: null,
    resolvedRepoRef: null,
    resolutionMode: null,
  };
  const passthrough = [];

  for (let i = 0; i < args.length; i += 1) {
    const value = args[i];
    if (value === "--resolved-repo" || value === "--resolved-repo-ref" || value === "--resolution-mode") {
      const key =
        value === "--resolved-repo"
          ? "resolvedRepo"
          : value === "--resolved-repo-ref"
            ? "resolvedRepoRef"
            : "resolutionMode";
      internal[key] = args[i + 1] ?? null;
      i += 1;
      continue;
    }
    passthrough.push(value);
  }

  let format = "text";
  let repoOverride = null;
  let scope = "disposable";
  let entryPoint = null;
  let maxPages = 3;
  let report = null;
  const positionals = [];

  for (let i = 0; i < passthrough.length; i += 1) {
    const value = passthrough[i];
    if (value === "--format" && i + 1 < passthrough.length) {
      format = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--format=")) {
      format = value.slice("--format=".length);
      continue;
    }
    if (value === "--repo" && i + 1 < passthrough.length) {
      repoOverride = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--repo=")) {
      repoOverride = value.slice("--repo=".length);
      continue;
    }
    if (value === "--scope" && i + 1 < passthrough.length) {
      scope = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--scope=")) {
      scope = value.slice("--scope=".length);
      continue;
    }
    if (value === "--entry-point" && i + 1 < passthrough.length) {
      entryPoint = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--entry-point=")) {
      entryPoint = value.slice("--entry-point=".length);
      continue;
    }
    if (value === "--max-pages" && i + 1 < passthrough.length) {
      maxPages = Number.parseInt(passthrough[i + 1], 10);
      i += 1;
      continue;
    }
    if (value.startsWith("--max-pages=")) {
      maxPages = Number.parseInt(value.slice("--max-pages=".length), 10);
      continue;
    }
    if (value === "--report") {
      report = true;
      continue;
    }
    if (value === "--no-report") {
      report = false;
      continue;
    }
    if (!value.startsWith("-")) {
      positionals.push(value);
    }
  }

  return {
    format,
    repoOverride,
    scope,
    entryPoint,
    maxPages: Number.isFinite(maxPages) && maxPages > 0 ? maxPages : 3,
    report,
    command: positionals[0] ?? null,
    target: positionals[1] ?? null,
    internal,
  };
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
  lines.push(`workflow: ${result.workflow ?? "none"}`);
  lines.push(`engine_path: ${result.engine_path ?? "none"}`);
  process.stdout.write(`${lines.join("\n")}\n`);
}

function absoluteArtifact(filePath, lifecycle, description, action = null) {
  return {
    path: path.resolve(filePath),
    lifecycle,
    description,
    ...(action ? { action } : {}),
  };
}

function slugify(input) {
  return input
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "target";
}

function nowParts() {
  const now = new Date();
  const iso = now.toISOString();
  const date = iso.slice(0, 10);
  const stamp = iso.replace(/[-:]/g, "").replace(/\..+/, "");
  return { date, stamp };
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function writeTextFile(filePath, content) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content, "utf8");
}

function readFrontmatter(strategyPath) {
  const raw = fs.readFileSync(strategyPath, "utf8");
  const match = raw.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!match) {
    throw new Error(`Strategy file is missing YAML frontmatter: ${strategyPath}`);
  }
  return YAML.parse(match[1]);
}

function readRegistry(repoRoot) {
  const registryPath = path.join(repoRoot, "sites", "strategies", "registry.json");
  const parsed = JSON.parse(fs.readFileSync(registryPath, "utf8"));
  return { registryPath, entries: parsed.entries ?? [] };
}

function findStrategy(repoRoot, targetUrl) {
  const registry = readRegistry(repoRoot);
  const url = new URL(targetUrl);
  const host = url.hostname;
  const matches = registry.entries
    .filter((entry) => host === entry.domain || host.endsWith(`.${entry.domain}`))
    .sort((a, b) => b.domain.length - a.domain.length);
  if (matches.length === 0) {
    return { registry, strategy: null };
  }
  const strategyMeta = matches[0];
  const strategyPath = path.join(repoRoot, "sites", "strategies", strategyMeta.file);
  const strategy = readFrontmatter(strategyPath);
  return { registry, strategy: { ...strategyMeta, path: strategyPath, document: strategy } };
}

function pagePatternMatches(page, targetUrl) {
  if (!page?.url_pattern) {
    return false;
  }
  const url = new URL(targetUrl);
  const isAbsolute = /^https?:\/\//.test(page.url_pattern);
  const candidate = isAbsolute ? `${url.origin}${url.pathname}` : url.pathname;
  const pattern = page.url_pattern.replace(/:[A-Za-z_][A-Za-z0-9_]*/g, "__PARAM__");
  const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/__PARAM__/g, "[^/?#]+");
  const regex = new RegExp(`^${escaped}$`);
  return regex.test(candidate);
}

function findMatchingPage(strategyDoc, targetUrl) {
  return (strategyDoc?.structure?.pages ?? []).find((page) => pagePatternMatches(page, targetUrl)) ?? null;
}

function selectFetcher(strategy, page) {
  const preferred = page?.engine_preference?.preferred ?? strategy?.document?.engine_preference?.preferred ?? null;
  if (preferred === "scrapling-get") {
    return "get";
  }
  if (preferred === "scrapling-fetch") {
    return "fetch";
  }
  if (preferred === "scrapling-stealthy-fetch") {
    return "stealthy-fetch";
  }

  const protection = strategy?.protection_level ?? strategy?.document?.protection_level;
  const antiCrawlRefs = new Set([...(strategy?.anti_crawl_refs ?? []), ...(page?.anti_crawl_refs ?? [])]);
  const pageType = page?.type ?? null;

  if (antiCrawlRefs.has("cloudflare-turnstile") || protection === "high") {
    return "stealthy-fetch";
  }
  if (
    protection === "authenticated" ||
    pageType === "dynamic_list" ||
    pageType === "dynamic_content" ||
    pageType === "search_results"
  ) {
    return "fetch";
  }
  return "get";
}

function runScraplingPreflight(repoRoot, allowInstall) {
  const args = ["./scripts/scrapling-cli.sh", "preflight"];
  if (!allowInstall) {
    args.push("--no-install");
  }
  const result = spawnSync(args[0], args.slice(1), {
    cwd: repoRoot,
    encoding: "utf8",
  });
  const lines = `${result.stdout ?? ""}${result.stderr ?? ""}`.split("\n");
  const statusMap = {};
  for (const line of lines) {
    const match = line.match(/^([A-Z_]+)=(.*)$/);
    if (match) {
      statusMap[match[1]] = match[2];
    }
  }
  return {
    ok: result.status === 0,
    status: statusMap.STATUS ?? null,
    resolvedCliPath: statusMap.RESOLVED_CLI_PATH ?? null,
    source: statusMap.SOURCE ?? null,
    zshenvStatus: statusMap.ZSHENV_STATUS ?? null,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
  };
}

function runScraplingFetch(repoRoot, fetcher, targetUrl, outputPath, extraArgs = []) {
  const preflight = runScraplingPreflight(repoRoot, true);
  if (!preflight.ok || !preflight.resolvedCliPath) {
    return {
      ok: false,
      preflight,
      summary: "Scrapling CLI preflight failed.",
      stderr: `${preflight.stdout}${preflight.stderr}`.trim(),
    };
  }

  const args = ["extract", fetcher, targetUrl, outputPath, ...extraArgs];
  const result = spawnSync(preflight.resolvedCliPath, args, {
    cwd: repoRoot,
    encoding: "utf8",
  });
  return {
    ok: result.status === 0,
    preflight,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
    command: [preflight.resolvedCliPath, ...args].join(" "),
  };
}

function summarizeContent(outputPath) {
  if (!fs.existsSync(outputPath)) {
    return null;
  }
  const content = fs.readFileSync(outputPath, "utf8");
  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const firstHeading = lines.find((line) => line.startsWith("# "));
  return firstHeading ? firstHeading.slice(2).trim() : lines[0] ?? null;
}

function repoShapeIsValid(repoRoot) {
  return fs.existsSync(path.join(repoRoot, "AGENTS.md"));
}

function resolutionSummary(repoRef, resolutionMode) {
  if (resolutionMode === "env_default") {
    return `Resolved via CHROME_AGENT_REPO default (${repoRef}).`;
  }
  if (resolutionMode === "explicit_override") {
    return `Resolved via explicit override (${repoRef}).`;
  }
  if (resolutionMode === "repo_local") {
    return `Resolved via repository-local invocation (${repoRef}).`;
  }
  return `Resolved via repo-registry (${repoRef}).`;
}

function buildRunPaths(repoRoot, command, targetUrl) {
  const { date, stamp } = nowParts();
  const slug = slugify(targetUrl);
  const runDir = path.join(repoRoot, "outputs", `${stamp}-${command}-${slug}`);
  const reportPath = path.join(repoRoot, "reports", `${date}-${command}-${slug}.md`);
  return { runDir, reportPath, stamp, date, slug };
}

function shouldEmitReport(command, reportOverride) {
  if (reportOverride === true) {
    return true;
  }
  if (reportOverride === false) {
    return false;
  }
  return command === "explore";
}

function buildExploreReport({ targetUrl, strategy, matchingPage, repoRef, resolutionMode, preflight, recommendedFetcher }) {
  const lines = [
    `# Explore Report`,
    "",
    `- Target: ${targetUrl}`,
    `- Repo ref: ${repoRef}`,
    `- Resolution: ${resolutionSummary(repoRef, resolutionMode)}`,
    `- Workflow: platform_analysis`,
    `- Strategy matched: ${strategy ? "yes" : "no"}`,
    `- Scrapling preflight: ${preflight.ok ? `${preflight.status} (${preflight.source})` : "unavailable"}`,
  ];
  if (strategy) {
    lines.push(`- Strategy file: ${path.relative(process.cwd(), strategy.path)}`);
    lines.push(`- Protection level: ${strategy.protection_level}`);
    lines.push(`- Entry points: ${(strategy.document?.structure?.entry_points ?? []).join(", ") || "none"}`);
    lines.push(`- Matched page type: ${matchingPage?.id ?? "none"}`);
    lines.push(`- Recommended fetcher: ${recommendedFetcher ?? "unknown"}`);
    lines.push(`- Anti-crawl refs: ${[...(strategy.anti_crawl_refs ?? []), ...(matchingPage?.anti_crawl_refs ?? [])].join(", ") || "none"}`);
  } else {
    lines.push("- Strategy file: none");
    lines.push("- Gap: no site strategy currently covers this target.");
    lines.push("- Recommended fetcher: unknown until strategy coverage exists.");
  }
  lines.push("");
  lines.push("## Structure Clues");
  if (strategy) {
    lines.push(`- Domain: ${strategy.domain}`);
    lines.push(`- Declared pages: ${(strategy.document?.structure?.pages ?? []).map((page) => page.id).join(", ") || "none"}`);
    lines.push(`- Matched URL pattern: ${matchingPage?.url_pattern ?? "none"}`);
  } else {
    lines.push(`- Host: ${new URL(targetUrl).hostname}`);
    lines.push("- Strategy gap prevents deeper bounded workflow guidance.");
  }
  lines.push("");
  lines.push("## Next Action");
  if (strategy) {
    lines.push("- Use `chrome-agent fetch <url>` for content retrieval, or `chrome-agent crawl <url>` when bounded traversal is needed.");
  } else {
    lines.push("- Run `chrome-agent explore <url>` as the first step for strategy authoring evidence, then add or refine a `sites/strategies/<domain>/strategy.md` entry.");
  }
  return `${lines.join("\n")}\n`;
}

function makeResult(command, target, repoRef, summary, artifacts, nextAction, result = "success", extra = {}) {
  return {
    result,
    command,
    target,
    repo_ref: repoRef ?? DEFAULT_REPO_REF,
    summary,
    artifacts,
    next_action: nextAction,
    workflow: extra.workflow ?? null,
    engine_path: extra.engine_path ?? null,
    ...extra,
  };
}

function runExplore(repoRoot, repoRef, resolutionMode, targetUrl, reportOverride) {
  const { reportPath } = buildRunPaths(repoRoot, "explore", targetUrl);
  const { strategy } = findStrategy(repoRoot, targetUrl);
  const matchingPage = strategy ? findMatchingPage(strategy.document, targetUrl) : null;
  const preflight = runScraplingPreflight(repoRoot, false);
  const recommendedFetcher = strategy ? selectFetcher(strategy, matchingPage) : null;
  const report = buildExploreReport({
    targetUrl,
    strategy,
    matchingPage,
    repoRef,
    resolutionMode,
    preflight,
    recommendedFetcher,
  });
  const emitReport = shouldEmitReport("explore", reportOverride);
  const artifacts = [];
  if (emitReport) {
    writeTextFile(reportPath, report);
    artifacts.push(absoluteArtifact(reportPath, "durable", "Explore report"));
  }
  if (!strategy) {
    return makeResult(
      "explore",
      targetUrl,
      repoRef,
      emitReport
        ? "No matching site strategy exists yet; explore identified a strategy gap and saved a durable report."
        : "No matching site strategy exists yet; explore identified a strategy gap.",
      artifacts,
      `Create or refine a site strategy for ${new URL(targetUrl).hostname}, then retry fetch or crawl.`,
      "partial_success",
      {
        workflow: "platform_analysis",
        engine_path: `strategy_registry -> strategy_gap -> scrapling_preflight:${preflight.status ?? "unavailable"}`,
      },
    );
  }

  return makeResult(
    "explore",
    targetUrl,
    repoRef,
    `Matched strategy ${path.relative(repoRoot, strategy.path)}, documented the repository-local analysis route, and prepared backend guidance for ${recommendedFetcher ?? "unknown"} follow-up.`,
    artifacts,
    `Use chrome-agent fetch ${targetUrl} for content retrieval or crawl from one of: ${(strategy.document?.structure?.entry_points ?? []).join(", ") || "the declared entry points"}.`,
    "success",
    {
      workflow: "platform_analysis",
      engine_path: `strategy_registry -> analysis_report -> recommended:${recommendedFetcher ?? "unknown"} -> scrapling_preflight:${preflight.status ?? "unavailable"}`,
    },
  );
}

function buildFetchReport({
  targetUrl,
  repoRef,
  resolutionMode,
  strategy,
  matchingPage,
  fetcher,
  fetchResult,
  outputPath,
}) {
  const lines = [
    `# Fetch Report`,
    "",
    `- Target: ${targetUrl}`,
    `- Repo ref: ${repoRef}`,
    `- Resolution: ${resolutionSummary(repoRef, resolutionMode)}`,
    `- Fetcher: ${fetcher}`,
    `- Strategy file: ${strategy ? path.relative(process.cwd(), strategy.path) : "none"}`,
    `- Matched page: ${matchingPage?.id ?? "none"}`,
    `- Scrapling preflight: ${fetchResult.preflight?.status ?? "unknown"} (${fetchResult.preflight?.source ?? "unknown"})`,
    `- Output: ${outputPath}`,
  ];

  if (fetchResult.ok) {
    lines.push(`- Status: success`);
  } else {
    lines.push(`- Status: failure`);
    lines.push(`- Error: ${fetchResult.stderr.trim() || "Scrapling command failed without stderr output."}`);
  }

  if (fetchResult.command) {
    lines.push(`- Command: \`${fetchResult.command}\``);
  }

  return `${lines.join("\n")}\n`;
}

function runFetch(repoRoot, repoRef, resolutionMode, targetUrl, reportOverride) {
  const { runDir, reportPath } = buildRunPaths(repoRoot, "fetch", targetUrl);
  ensureDir(runDir);
  const outputPath = path.join(runDir, "content.md");
  const logPath = path.join(runDir, "scrapling.stderr.log");
  const manifestPath = path.join(runDir, "manifest.json");
  const { strategy } = findStrategy(repoRoot, targetUrl);
  const matchingPage = strategy ? findMatchingPage(strategy.document, targetUrl) : null;
  const fetcher = selectFetcher(strategy, matchingPage);
  const fetchResult = runScraplingFetch(repoRoot, fetcher, targetUrl, outputPath, ["--ai-targeted"]);

  if (fetchResult.stderr) {
    writeTextFile(logPath, fetchResult.stderr);
  }

  const emitReport = shouldEmitReport("fetch", reportOverride);
  if (emitReport) {
    const report = buildFetchReport({
      targetUrl,
      repoRef,
      resolutionMode,
      strategy,
      matchingPage,
      fetcher,
      fetchResult,
      outputPath,
    });
    writeTextFile(reportPath, report);
  }

  const manifest = {
    command: "fetch",
    target: targetUrl,
    fetcher,
    repo_ref: repoRef,
    resolution_mode: resolutionMode,
    strategy_file: strategy ? path.relative(repoRoot, strategy.path) : null,
    page_id: matchingPage?.id ?? null,
    preflight_status: fetchResult.preflight?.status ?? null,
    output: path.resolve(outputPath),
  };
  writeTextFile(manifestPath, JSON.stringify(manifest, null, 2));

  const artifacts = [absoluteArtifact(manifestPath, "disposable", "Run manifest")];
  if (emitReport) {
    artifacts.unshift(absoluteArtifact(reportPath, "durable", "Fetch report"));
  }
  if (fs.existsSync(outputPath)) {
    artifacts.push(absoluteArtifact(outputPath, "disposable", "Extracted content"));
  }
  if (fs.existsSync(logPath)) {
    artifacts.push(absoluteArtifact(logPath, "disposable", "Scrapling stderr log"));
  }

  if (!fetchResult.ok) {
    return makeResult(
      "fetch",
      targetUrl,
      repoRef,
      `Fetch failed after ${fetcher} dispatch.`,
      artifacts,
      emitReport
        ? "Inspect the durable fetch report, adjust strategy or fetcher selection, then retry."
        : "Inspect disposable artifacts (manifest/stderr), adjust strategy or fetcher selection, then retry.",
      "failure",
      {
        workflow: "content_retrieval",
        engine_path: `scrapling:${fetcher} -> preflight:${fetchResult.preflight?.status ?? "unknown"} -> failed`,
      },
    );
  }

  const title = summarizeContent(outputPath);
  return makeResult(
    "fetch",
    targetUrl,
    repoRef,
    `Fetched content with scrapling ${fetcher}${title ? ` and identified "${title}"` : ""}.`,
    artifacts,
    strategy ? "Review the extracted content or continue to crawl if bounded traversal is required." : "Consider running explore to add a site strategy if this domain should support bounded crawl later.",
    "success",
    {
      workflow: "content_retrieval",
      engine_path: `scrapling:${fetcher} -> preflight:${fetchResult.preflight?.status ?? "unknown"}`,
    },
  );
}

function extractHrefFilter(selector) {
  const contains = selector?.match(/href\*="([^"]+)"/);
  if (contains) {
    return { type: "contains", value: contains[1] };
  }
  const exact = selector?.match(/href="([^"]+)"/);
  if (exact) {
    return { type: "exact", value: exact[1] };
  }
  return null;
}

function collectLinksFromHtml(htmlPath, baseUrl, selector) {
  if (!fs.existsSync(htmlPath)) {
    return [];
  }
  const filter = extractHrefFilter(selector);
  const html = fs.readFileSync(htmlPath, "utf8");
  const matches = [...html.matchAll(/href="([^"#]+)"/g)];
  const urls = new Set();
  for (const match of matches) {
    const href = match[1];
    if (filter?.type === "contains" && !href.includes(filter.value)) {
      continue;
    }
    if (filter?.type === "exact" && href !== filter.value) {
      continue;
    }
    urls.add(new URL(href, baseUrl).toString());
  }
  return [...urls];
}

function nextPaginationUrl(currentUrl, pagination, pageNumber) {
  if (!pagination || pagination === "none") {
    return null;
  }
  if (pagination.mechanism === "url_parameter") {
    const url = new URL(currentUrl);
    url.searchParams.set(pagination.parameter, String(pageNumber));
    return url.toString();
  }
  return null;
}

function buildCrawlReport({ targetUrl, repoRef, resolutionMode, strategy, events, result }) {
  const lines = [
    `# Crawl Report`,
    "",
    `- Target: ${targetUrl}`,
    `- Repo ref: ${repoRef}`,
    `- Resolution: ${resolutionSummary(repoRef, resolutionMode)}`,
    `- Strategy file: ${strategy ? path.relative(process.cwd(), strategy.path) : "none"}`,
    `- Result: ${result}`,
    "",
    "## Traversal",
  ];
  for (const event of events) {
    lines.push(`- ${event}`);
  }
  return `${lines.join("\n")}\n`;
}

function runCrawl(repoRoot, repoRef, resolutionMode, targetUrl, entryPointOverride, maxPages, reportOverride) {
  const { runDir, reportPath } = buildRunPaths(repoRoot, "crawl", targetUrl);
  ensureDir(runDir);
  const manifestPath = path.join(runDir, "manifest.json");
  const emitReport = shouldEmitReport("crawl", reportOverride);
  const { strategy } = findStrategy(repoRoot, targetUrl);

  if (!strategy) {
    if (emitReport) {
      const report = buildCrawlReport({
        targetUrl,
        repoRef,
        resolutionMode,
        strategy: null,
        events: ["No matching site strategy exists, so crawl was refused before traversal started."],
        result: "failure",
      });
      writeTextFile(reportPath, report);
    }
    const artifacts = [];
    if (emitReport) {
      artifacts.push(absoluteArtifact(reportPath, "durable", "Crawl refusal report"));
    }
    return makeResult(
      "crawl",
      targetUrl,
      repoRef,
      "Crawl refused because no matching site strategy exists.",
      artifacts,
      `Run chrome-agent explore ${targetUrl} first to create or refine a site strategy.`,
      "failure",
      {
        workflow: "content_retrieval",
        engine_path: "strategy_registry -> strategy_gap",
      },
    );
  }

  const doc = strategy.document;
  const pages = doc?.structure?.pages ?? [];
  const entryPoints = doc?.structure?.entry_points ?? [];
  const matchingPage = findMatchingPage(doc, targetUrl);
  const startPage =
    (entryPointOverride ? pages.find((page) => page.id === entryPointOverride) : null) ||
    (matchingPage && entryPoints.includes(matchingPage.id) ? matchingPage : null) ||
    pages.find((page) => page.id === entryPoints[0]) ||
    null;

  if (!startPage) {
    if (emitReport) {
      const report = buildCrawlReport({
        targetUrl,
        repoRef,
        resolutionMode,
        strategy,
        events: ["Strategy exists but no usable entry point could be resolved."],
        result: "failure",
      });
      writeTextFile(reportPath, report);
    }
    const artifacts = [];
    if (emitReport) {
      artifacts.push(absoluteArtifact(reportPath, "durable", "Crawl failure report"));
    }
    return makeResult(
      "crawl",
      targetUrl,
      repoRef,
      "Crawl could not resolve a declared entry point.",
      artifacts,
      `Update ${path.relative(repoRoot, strategy.path)} so the crawl can start from a declared entry point.`,
      "failure",
      {
        workflow: "content_retrieval",
        engine_path: `strategy_registry -> ${path.relative(repoRoot, strategy.path)} -> missing_entry_point`,
      },
    );
  }

  const preflight = runScraplingPreflight(repoRoot, true);
  if (!preflight.ok) {
    if (emitReport) {
      const report = buildCrawlReport({
        targetUrl,
        repoRef,
        resolutionMode,
        strategy,
        events: ["Scrapling CLI preflight failed before crawl traversal."],
        result: "failure",
      });
      writeTextFile(reportPath, report);
    }
    const artifacts = [];
    if (emitReport) {
      artifacts.push(absoluteArtifact(reportPath, "durable", "Crawl preflight report"));
    }
    return makeResult(
      "crawl",
      targetUrl,
      repoRef,
      "Crawl stopped because Scrapling CLI preflight failed.",
      artifacts,
      "Repair the Scrapling CLI environment, then retry crawl.",
      "failure",
      {
        workflow: "content_retrieval",
        engine_path: `strategy_registry -> scrapling_preflight:${preflight.status ?? "unavailable"} -> blocked`,
      },
    );
  }

  const queue = [];
  const startUrl = matchingPage && matchingPage.id === startPage.id ? targetUrl : startPage.url_example;
  queue.push({ url: startUrl, page: startPage, paginationIndex: 1 });
  const visited = new Set();
  const artifacts = [];
  const events = [];
  let failures = 0;

  while (queue.length > 0 && visited.size < maxPages) {
    const item = queue.shift();
    if (!item || visited.has(item.url)) {
      continue;
    }
    visited.add(item.url);
    const fetcher = selectFetcher(strategy, item.page);
    const pageSlug = `${String(visited.size).padStart(2, "0")}-${item.page.id}`;
    const outputPath = path.join(runDir, `${pageSlug}.html`);
    const fetchResult = runScraplingFetch(repoRoot, fetcher, item.url, outputPath);

    if (fetchResult.ok) {
      artifacts.push(absoluteArtifact(outputPath, "disposable", `Crawled page ${item.page.id}`));
      events.push(`Fetched ${item.url} via ${fetcher} for page ${item.page.id}.`);
    } else {
      failures += 1;
      const errorPath = path.join(runDir, `${pageSlug}.stderr.log`);
      writeTextFile(errorPath, fetchResult.stderr || "Scrapling crawl fetch failed.");
      artifacts.push(absoluteArtifact(errorPath, "disposable", `Crawl error for ${item.page.id}`));
      events.push(`Failed ${item.url} via ${fetcher} for page ${item.page.id}.`);
      continue;
    }

    for (const link of item.page.links_to ?? []) {
      const nextPage = pages.find((page) => page.id === link.target);
      if (!nextPage) {
        events.push(`Skipped undeclared target page ${link.target} from ${item.page.id}.`);
        continue;
      }
      const discovered = collectLinksFromHtml(outputPath, item.url, link.selector);
      for (const url of discovered) {
        if (pagePatternMatches(nextPage, url) && !visited.has(url)) {
          queue.push({ url, page: nextPage, paginationIndex: 1 });
        }
      }
      if (discovered.length === 0) {
        events.push(`No bounded links matched selector ${link.selector} from ${item.page.id}.`);
      }
    }

    if (item.page.pagination && item.page.pagination !== "none" && queue.length + visited.size < maxPages) {
      if (item.page.pagination.mechanism === "url_parameter") {
        const nextPageNumber = item.paginationIndex + 1;
        const nextUrl = nextPaginationUrl(item.url, item.page.pagination, nextPageNumber);
        if (nextUrl && !visited.has(nextUrl) && queue.length + visited.size < maxPages) {
          queue.push({ url: nextUrl, page: item.page, paginationIndex: nextPageNumber });
          events.push(`Queued bounded pagination URL ${nextUrl} from ${item.page.id}.`);
        }
      } else {
        events.push(`Pagination mechanism ${item.page.pagination.mechanism} is bounded but not auto-followed in this implementation.`);
      }
    }
  }

  const manifest = {
    command: "crawl",
    target: targetUrl,
    repo_ref: repoRef,
    resolution_mode: resolutionMode,
    strategy_file: path.relative(repoRoot, strategy.path),
    visited: [...visited],
    max_pages: maxPages,
    start_page: startPage.id,
    bounded_by: {
      entry_points: entryPoints,
      links_to: true,
      pagination: true,
      unrestricted_recursive_spider: false,
    },
  };
  writeTextFile(manifestPath, JSON.stringify(manifest, null, 2));
  artifacts.push(absoluteArtifact(manifestPath, "disposable", "Crawl manifest"));

  const resultState = failures > 0 && visited.size > failures ? "partial_success" : failures > 0 ? "failure" : "success";
  if (emitReport) {
    const report = buildCrawlReport({
      targetUrl,
      repoRef,
      resolutionMode,
      strategy,
      events,
      result: resultState,
    });
    writeTextFile(reportPath, report);
    artifacts.unshift(absoluteArtifact(reportPath, "durable", "Crawl report"));
  }

  const summary =
    resultState === "success"
      ? `Crawl completed within declared strategy boundaries and visited ${visited.size} page(s).`
      : resultState === "partial_success"
        ? `Crawl visited ${visited.size} page(s) with some bounded failures.`
        : "Crawl failed before any page completed successfully.";
  const nextAction =
    resultState === "failure"
      ? "Review the crawl report, strategy selectors, or authentication requirements before retrying."
      : "Inspect the crawl report and outputs. Extend the site strategy if more bounded traversal is needed.";

  return makeResult("crawl", targetUrl, repoRef, summary, artifacts, nextAction, resultState, {
    workflow: "content_retrieval",
    engine_path: `strategy_registry -> bounded_crawl -> scrapling_preflight:${preflight.status ?? "unknown"}`,
  });
}

function runDoctor(repoRoot, repoRef, resolutionMode) {
  const runtimeDir = process.env.CHROME_AGENT_RUNTIME_DIR || path.join(os.homedir(), ".agents", "scripts");
  const binDir = process.env.CHROME_AGENT_BIN_DIR || path.join(os.homedir(), ".local", "bin");
  const runtimePath = path.join(runtimeDir, "chrome-agent.mjs");
  const shimPath = path.join(binDir, "chrome-agent");
  const preflight = runScraplingPreflight(repoRoot, false);
  const envDefaultPath = process.env.CHROME_AGENT_REPO ? path.resolve(process.env.CHROME_AGENT_REPO) : null;

  const checks = [
    { name: "runtime_script", ok: fs.existsSync(runtimePath), detail: runtimePath },
    { name: "user_shim", ok: fs.existsSync(shimPath), detail: shimPath },
    {
      name: "env_default",
      ok: resolutionMode === "explicit_override" ? true : repoShapeIsValid(envDefaultPath),
      detail: resolutionMode === "explicit_override" ? "not_used" : envDefaultPath ?? "unset",
    },
    { name: "repo_shape", ok: repoShapeIsValid(repoRoot), detail: path.join(repoRoot, "AGENTS.md") },
    { name: "scrapling_preflight", ok: preflight.ok, detail: preflight.resolvedCliPath ?? "unavailable" },
  ];

  const broken = checks.filter((check) => !check.ok);
  const resultState = broken.length === 0 ? "success" : preflight.ok || repoShapeIsValid(repoRoot) ? "partial_success" : "failure";

  return makeResult(
    "doctor",
    "runtime",
    repoRef,
    broken.length === 0
      ? `Launcher and repository prerequisites are healthy. ${resolutionSummary(repoRef, resolutionMode)}`
      : `Doctor found ${broken.length} issue(s): ${broken.map((check) => check.name).join(", ")}.`,
    checks.map((check) => ({
      path: check.detail,
      lifecycle: "durable",
      description: check.name,
      action: check.ok ? "checked" : "missing",
    })),
    broken.length === 0
      ? "none"
      : "Install the global launcher, set CHROME_AGENT_REPO or supply an explicit --repo <path|repo://id>, and repair Scrapling CLI availability.",
    resultState,
    {
      checks,
      resolution_mode: resolutionMode,
      workflow: "runtime_support",
      engine_path: `doctor -> repo_resolution:${resolutionMode} -> scrapling_preflight:${preflight.status ?? "unavailable"}`,
    },
  );
}

function safeListSubdirs(dirPath) {
  if (!fs.existsSync(dirPath)) {
    return [];
  }
  return fs
    .readdirSync(dirPath, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(dirPath, entry.name));
}

function runClean(repoRoot, repoRef, scope) {
  const outputsDir = path.join(repoRoot, "outputs");
  const reportsDir = path.join(repoRoot, "reports");
  const removed = [];
  const preserved = [];

  for (const dir of safeListSubdirs(outputsDir)) {
    fs.rmSync(dir, { recursive: true, force: true });
    removed.push(absoluteArtifact(dir, "disposable", "Removed run output", "removed"));
  }

  if (scope === "all") {
    for (const name of fs.existsSync(reportsDir) ? fs.readdirSync(reportsDir) : []) {
      const filePath = path.join(reportsDir, name);
      fs.rmSync(filePath, { recursive: true, force: true });
      removed.push(absoluteArtifact(filePath, "durable", "Removed durable report", "removed"));
    }
  } else if (fs.existsSync(reportsDir)) {
    preserved.push(absoluteArtifact(reportsDir, "durable", "Preserved durable reports", "preserved"));
  }

  return makeResult(
    "clean",
    "artifacts",
    repoRef,
    scope === "all"
      ? `Removed ${removed.length} artifact path(s), including durable reports.`
      : `Removed ${removed.length} disposable output path(s) and preserved durable reports.`,
    [...removed, ...preserved],
    scope === "all" ? "none" : "Use --scope all only when you explicitly intend to delete durable reports.",
    "success",
    {
      workflow: "artifact_maintenance",
      engine_path: `clean -> scope:${scope}`,
    },
  );
}

function main() {
  const parsed = parseArgs(process.argv.slice(2));

  if (!parsed.command || parsed.command === "help" || process.argv.includes("--help") || process.argv.includes("-h")) {
    printHelp();
    process.exit(0);
  }

  const repoRoot = parsed.internal.resolvedRepo ? path.resolve(parsed.internal.resolvedRepo) : inferredRepoRoot;
  const repoRef = parsed.internal.resolvedRepoRef ?? (parsed.repoOverride || DEFAULT_REPO_REF);
  const resolutionMode = parsed.internal.resolutionMode ?? "repo_local";

  try {
    if (parsed.command !== "doctor" && !repoShapeIsValid(repoRoot)) {
      throw new Error(`Target repository is missing AGENTS.md: ${path.join(repoRoot, "AGENTS.md")}`);
    }

    let result;
    switch (parsed.command) {
      case "explore":
        if (!parsed.target) {
          throw new Error("explore requires a target URL.");
        }
        result = runExplore(repoRoot, repoRef, resolutionMode, parsed.target, parsed.report);
        break;
      case "fetch":
        if (!parsed.target) {
          throw new Error("fetch requires a target URL.");
        }
        result = runFetch(repoRoot, repoRef, resolutionMode, parsed.target, parsed.report);
        break;
      case "crawl":
        if (!parsed.target) {
          throw new Error("crawl requires a target URL.");
        }
        result = runCrawl(repoRoot, repoRef, resolutionMode, parsed.target, parsed.entryPoint, parsed.maxPages, parsed.report);
        break;
      case "doctor":
        result = runDoctor(repoRoot, repoRef, resolutionMode);
        break;
      case "clean":
        result = runClean(repoRoot, repoRef, parsed.scope);
        break;
      default:
        throw new Error(`Unknown command: ${parsed.command}`);
    }

    renderResult(result, parsed.format);
    process.exit(result.result === "failure" ? 1 : 0);
  } catch (error) {
    renderResult(
      makeResult(
        parsed.command ?? "unknown",
        parsed.target,
        repoRef,
        error.message,
        [],
        "Check the command syntax and retry.",
        "failure",
      ),
      parsed.format,
    );
    process.exit(1);
  }
}

main();
