#!/usr/bin/env node

import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawn, spawnSync } from "node:child_process";
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
  crawl <url>            Run the explicit strategy-guided bounded-crawl backend workflow.
  scrape <url>           Run the explicit strategy-free recursive scraping backend workflow.
  batch <urls...>        Fetch multiple URLs in parallel using the Obscura serve pool.
  bootstrap-strategy <url> --from <domain> [--profile <name>]
                         Bootstrap a new site strategy from an existing reference strategy.
  doctor                 Validate launcher, repo resolution, repo shape, and Scrapling readiness.
  freeze <scaffold-path>  Finalize a strategy scaffold: remove marker, update registry, generate report.
  iterate <scaffold-path> Re-run sample conversion with updated extraction rules after user feedback.
  clean [--scope all]    Remove disposable outputs by default.

Command options:
  --entry-point <id>     Crawl from a specific declared entry point.
  --max-pages <n>        Maximum pages to traverse. Default: 3 (crawl), 10 (scrape).
  --from <domain>        Reference domain for bootstrap-strategy (required).
  --profile <name>       Cleanup profile override for bootstrap-strategy.
  --no-same-domain       Allow cross-domain link following in scrape (default: same-domain only).
  --match <glob>         URL pathname glob filter for scrape (e.g., "/wiki/*").
  --no-markdown          Retain HTML output, skip Markdown conversion.
  --merge                Merge all per-page Markdown files into a single document.
  --concurrency <n>      Phase 2 Markdown conversion concurrency. Default: 5.
  --fetcher <name>       Override Scrapling fetcher for scrape (default: get).
  --keep-html            Retain intermediate HTML files alongside Markdown.
  --parallel             Use Obscura serve pool for parallel content retrieval (crawl/scrape).
  --workers <n>          Number of Obscura workers for parallel mode. Default: 5, max: 30.
  --report               Force durable report emission to reports/.
  --no-report            Disable durable report emission for this run.
  --discovery-only       Stop after discovery phase, output discovery_summary.json.
  --from-manifest <path> Resume crawl from existing page manifest.
  --output <dir>        Specify output directory for crawl results.
  --yes                  Bypass confirmation gate (passthrough signal for SKILL layer).
  --exclude-category <n> Exclude category from extraction (repeatable).
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
  let maxPages = null;
  let report = null;
  let fromDomain = null;
  let profile = null;
  let sameDomain = true;
  let matchPattern = null;
  let markdown = true;
  let merge = false;
  let concurrency = 5;
  let fetcherOverride = null;
  let keepHtml = false;
  let parallel = false;
  let workers = 5;
  let discoveryOnly = false;
  let fromManifest = null;
  let phase = null;
  let reFetch = false;
  let yes = false;
  let excludeCategory = [];
  let outputDir = null;
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
    if (value === "--from" && i + 1 < passthrough.length) {
      fromDomain = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--from=")) {
      fromDomain = value.slice("--from=".length);
      continue;
    }
    if (value === "--profile" && i + 1 < passthrough.length) {
      profile = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--profile=")) {
      profile = value.slice("--profile=".length);
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
    if (value === "--no-same-domain") {
      sameDomain = false;
      continue;
    }
    if (value === "--match" && i + 1 < passthrough.length) {
      matchPattern = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--match=")) {
      matchPattern = value.slice("--match=".length);
      continue;
    }
    if (value === "--no-markdown") {
      console.error("Tip: Use --phase fetch for persistent caching of raw content");
      markdown = false;
      continue;
    }
    if (value === "--merge") {
      merge = true;
      continue;
    }
    if (value === "--concurrency" && i + 1 < passthrough.length) {
      concurrency = Number.parseInt(passthrough[i + 1], 10);
      i += 1;
      continue;
    }
    if (value.startsWith("--concurrency=")) {
      concurrency = Number.parseInt(value.slice("--concurrency=".length), 10);
      continue;
    }
    if (value === "--fetcher" && i + 1 < passthrough.length) {
      fetcherOverride = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--fetcher=")) {
      fetcherOverride = value.slice("--fetcher=".length);
      continue;
    }
    if (value === "--keep-html") {
      console.error("WARNING: --keep-html is deprecated; HTML is now persisted via --phase fetch cache");
      keepHtml = true;
      continue;
    }
    if (value === "--parallel") {
      parallel = true;
      continue;
    }
    if (value === "--workers" && i + 1 < passthrough.length) {
      workers = Number.parseInt(passthrough[i + 1], 10);
      i += 1;
      continue;
    }
    if (value.startsWith("--workers=")) {
      workers = Number.parseInt(value.slice("--workers=".length), 10);
      continue;
    }
    if (value === "--discovery-only") {
      discoveryOnly = true;
      continue;
    }
    if (value === "--from-manifest" && i + 1 < passthrough.length) {
      fromManifest = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--from-manifest=")) {
      fromManifest = value.slice("--from-manifest=".length);
      continue;
    }
    if (value === "--yes" || value === "--no-confirm") {
      yes = true;
      continue;
    }
    if (value === "--exclude-category" && i + 1 < passthrough.length) {
      excludeCategory.push(passthrough[i + 1]);
      i += 1;
      continue;
    }
    if (value.startsWith("--exclude-category=")) {
      excludeCategory.push(value.slice("--exclude-category=".length));
      continue;
    }
    if (value === "--phase" && i + 1 < passthrough.length) {
      phase = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--phase=")) {
      phase = value.slice("--phase=".length);
      continue;
    }
    if (value === "--re-fetch") {
      reFetch = true;
      continue;
    }
    if (value === "--output" && i + 1 < passthrough.length) {
      outputDir = passthrough[i + 1];
      i += 1;
      continue;
    }
    if (value.startsWith("--output=")) {
      outputDir = value.slice("--output=".length);
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
    maxPages,
    report,
    fromDomain,
    profile,
    sameDomain,
    matchPattern,
    markdown,
    merge,
    concurrency: Number.isFinite(concurrency) && concurrency > 0 ? concurrency : 5,
    fetcherOverride,
    keepHtml,
    parallel,
    workers: Number.isFinite(workers) && workers > 0 ? Math.min(workers, 30) : 5,
    discoveryOnly,
    fromManifest,
    phase,
    reFetch,
    yes,
    excludeCategory,
    outputDir,
    command: positionals[0] ?? null,
    target: positionals[1] ?? null,
    positionals,
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
  if (result.handoff_path) {
    lines.push(`handoff_path: ${result.handoff_path}`);
    lines.push(`handoff_summary: ${result.handoff_summary ?? ""}`);
  }
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

// --- Scrapling cache helpers (file-system based, .cache/scrapling/<domain>/) ---

function scraplingCacheDir(repoRoot, domain) {
  return path.join(repoRoot, ".cache", "scrapling", domain);
}

function scraplingSlugFromUrl(urlStr) {
  const u = new URL(urlStr);
  let p = u.pathname.replace(/^\/+/, "").replace(/\/+$/, "");
  if (!p) p = "index";
  return p.replace(/[^a-zA-Z0-9/_-]/g, "_").replace(/_+/g, "_").replace(/(^_|_$)/g, "");
}

function saveScraplingCache(repoRoot, domain, slug, html, meta) {
  const dir = scraplingCacheDir(repoRoot, domain);
  ensureDir(dir);
  const htmlPath = path.join(dir, `${slug}.html`);
  const metaPath = path.join(dir, `${slug}.meta.json`);
  fs.writeFileSync(htmlPath, html, "utf8");
  fs.writeFileSync(metaPath, JSON.stringify({
    url: meta.url ?? "",
    fetched_at: new Date().toISOString(),
    fetcher: meta.fetcher ?? "unknown",
  }, null, 2), "utf8");
  return { htmlPath, metaPath };
}

function loadScraplingCache(repoRoot, domain, slug) {
  const dir = scraplingCacheDir(repoRoot, domain);
  const htmlPath = path.join(dir, `${slug}.html`);
  const metaPath = path.join(dir, `${slug}.meta.json`);
  if (!fs.existsSync(htmlPath) || !fs.existsSync(metaPath)) return null;
  return {
    html: fs.readFileSync(htmlPath, "utf8"),
    meta: JSON.parse(fs.readFileSync(metaPath, "utf8")),
  };
}

function isScraplingCached(repoRoot, domain, slug) {
  const dir = scraplingCacheDir(repoRoot, domain);
  return fs.existsSync(path.join(dir, `${slug}.html`)) &&
         fs.existsSync(path.join(dir, `${slug}.meta.json`));
}

function listScraplingCached(repoRoot, domain) {
  const dir = scraplingCacheDir(repoRoot, domain);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => f.endsWith(".html"))
    .map(f => f.replace(/\.html$/, ""));
}

function readFrontmatter(strategyPath) {
  const raw = fs.readFileSync(strategyPath, "utf8");
  const match = raw.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!match) {
    throw new Error(`Strategy file is missing YAML frontmatter: ${strategyPath}`);
  }
  return YAML.parse(match[1]);
}

function detectBackend(repoRoot, htmlContent, targetUrl) {
  const sigPath = path.join(repoRoot, "configs", "backend-signatures.json");
  if (!fs.existsSync(sigPath)) {
    return null;
  }
  const parsed = JSON.parse(fs.readFileSync(sigPath, "utf8"));
  const backends = parsed.backends ?? [];
  const url = new URL(targetUrl);
  const pathname = url.pathname;

  for (const backend of backends) {
    const detection = backend.detection;
    if (!detection) continue;

    let matches = 0;
    let checks = 0;

    if (detection.meta_generator !== undefined) {
      checks += 1;
      const metaMatch = htmlContent.match(/<meta\s+name=["']generator["']\s+content=["']([^"']*)["']/i);
      if (metaMatch && metaMatch[1].includes(detection.meta_generator)) {
        matches += 1;
      }
    }

    if (detection.dom_selector !== undefined) {
      checks += 1;
      const selector = detection.dom_selector.trim();
      if (selector.startsWith("#")) {
        const id = selector.slice(1);
        const idRegex = new RegExp(`id=["']${id}["']`, "i");
        if (idRegex.test(htmlContent)) {
          matches += 1;
        }
      } else if (selector.startsWith(".")) {
        const cls = selector.slice(1);
        const classRegex = new RegExp(`class=["'][^"']*${cls}[^"']*["']`, "i");
        if (classRegex.test(htmlContent)) {
          matches += 1;
        }
      } else {
        if (htmlContent.includes(selector)) {
          matches += 1;
        }
      }
    }

    if (detection.url_patterns !== undefined && detection.url_patterns.length > 0) {
      checks += 1;
      const urlMatch = detection.url_patterns.some((pattern) => pathname.includes(pattern));
      if (urlMatch) {
        matches += 1;
      }
    }

    if (checks > 0 && matches === checks) {
      return backend;
    }
  }

  return null;
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
  // API platform detection — checked before all scrapling-based engine selection.
  // When a strategy declares api.platform, the API engine is preferred over any scrapling path.
  const apiPlatform = strategy?.document?.api?.platform;
  if (apiPlatform === "mediawiki" || apiPlatform === "mediawiki-fandom") {
    return "mediawiki-api";
  }

  const preferred = page?.engine_preference?.preferred ?? strategy?.document?.engine_preference?.preferred ?? null;
  if (preferred === "scrapling-get") {
    return "get";
  }
  if (preferred === "scrapling-fetch") {
    return "fetch";
  }
  if (preferred === "scrapling-stealthy-fetch" || preferred === "cloakbrowser-fetch") {
    return "cloakbrowser";
  }

  const protection = strategy?.protection_level ?? strategy?.document?.protection_level;
  const antiCrawlRefs = new Set([...(strategy?.anti_crawl_refs ?? []), ...(page?.anti_crawl_refs ?? [])]);
  const pageType = page?.type ?? null;

  if (antiCrawlRefs.has("cloudflare-turnstile") || antiCrawlRefs.has("recaptcha") || protection === "high") {
    return "cloakbrowser";
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
  // Ensure the output directory exists before invoking Scrapling
  ensureDir(path.dirname(outputPath));

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

function runCloakbrowserFetch(repoRoot, targetUrl, outputPath, extraArgs = []) {
  ensureDir(path.dirname(outputPath));

  const preflight = spawnSync("bash", ["./scripts/cloakbrowser-preflight.sh"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  if (preflight.status !== 0) {
    return {
      ok: false,
      preflight: { ok: false },
      summary: "CloakBrowser preflight failed. Install with: pip install cloakbrowser",
      stderr: `${preflight.stdout ?? ""}${preflight.stderr ?? ""}`.trim(),
    };
  }

  const args = ["python3", "scripts/cloakbrowser_fetcher.py", targetUrl, "--output", outputPath, "--json", ...extraArgs];
  const result = spawnSync(args[0], args.slice(1), {
    cwd: repoRoot,
    encoding: "utf8",
  });
  return {
    ok: result.status === 0,
    preflight: { ok: true },
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
    command: args.join(" "),
  };
}

/**
 * Fetch page HTML via MediaWiki action=parse API.
 * Reads strategy's api.base_url, extracts page title from targetUrl,
 * calls the MediaWiki parse API, and writes the resulting HTML to outputPath.
 */
function runMediawikiApiFetch(repoRoot, targetUrl, outputPath, extraArgs = []) {
  // extraArgs[0] is expected to be the strategy path (passed from runEngineFetch)
  const strategyPath = extraArgs[0];
  if (!strategyPath) {
    return { ok: false, summary: "runMediawikiApiFetch requires a strategy path in extraArgs[0].", stderr: "Missing strategy path." };
  }

  let strategy;
  try {
    strategy = readFrontmatter(strategyPath);
  } catch (err) {
    return { ok: false, summary: `Failed to read strategy frontmatter: ${err.message}`, stderr: err.message };
  }

  const apiConfig = strategy?.api;
  if (!apiConfig?.base_url) {
    return { ok: false, summary: "Strategy has no api.base_url configured.", stderr: "Missing api.base_url in strategy." };
  }

  // Extract page title from URL (strip /wiki/ prefix, decode underscores to spaces)
  let pageTitle;
  try {
    const url = new URL(targetUrl);
    const pathParts = url.pathname.split("/");
    // Look for the part after /wiki/ (or use the last path segment)
    const wikiIdx = pathParts.indexOf("wiki");
    if (wikiIdx >= 0 && wikiIdx + 1 < pathParts.length) {
      pageTitle = decodeURIComponent(pathParts[wikiIdx + 1].replace(/_/g, " "));
    } else {
      pageTitle = decodeURIComponent(pathParts[pathParts.length - 1].replace(/_/g, " "));
    }
  } catch {
    return { ok: false, summary: `Invalid target URL: ${targetUrl}`, stderr: "Invalid URL." };
  }

  // Determine API endpoint: if base_url already includes /api.php, use it directly.
  // Otherwise append /api.php (standard MediaWiki endpoint suffix).
  let endpoint = apiConfig.base_url.replace(/\/+$/, "");
  if (!endpoint.endsWith("/api.php")) {
    endpoint += "/api.php";
  }
  const apiUrl = `${endpoint}?action=parse&page=${encodeURIComponent(pageTitle)}&redirects=true&prop=text&format=json`;

  const result = spawnSync("curl", ["-s", "--max-time", "30", apiUrl], {
    cwd: repoRoot,
    encoding: "utf8",
  });

  if (result.status !== 0) {
    return { ok: false, summary: `MediaWiki API request failed for "${pageTitle}".`, stderr: result.stderr || "curl failed." };
  }

  let data;
  try {
    data = JSON.parse(result.stdout);
  } catch (err) {
    return { ok: false, summary: `Invalid JSON from MediaWiki API for "${pageTitle}".`, stderr: err.message };
  }

  if (data.error) {
    return { ok: false, summary: `MediaWiki API error for "${pageTitle}": ${data.error.info || JSON.stringify(data.error)}`, stderr: JSON.stringify(data.error) };
  }

  const html = data?.parse?.text?.["*"];
  if (!html) {
    return { ok: false, summary: `MediaWiki API returned no text content for "${pageTitle}".`, stderr: "Missing parse.text[*] in API response." };
  }

  ensureDir(path.dirname(outputPath));
  fs.writeFileSync(outputPath, html, "utf8");

  return {
    ok: true,
    stdout: `Fetched "${pageTitle}" via MediaWiki API from ${baseUrl}`,
    stderr: "",
    command: `curl -s --max-time 30 "${apiUrl}"`,
    page_title: pageTitle,
  };
}

/** Route to the appropriate engine based on fetcher name */
function runEngineFetch(repoRoot, fetcher, targetUrl, outputPath, extraArgs = []) {
  if (fetcher === "mediawiki-api") {
    return runMediawikiApiFetch(repoRoot, targetUrl, outputPath, extraArgs);
  }
  if (fetcher === "cloakbrowser") {
    return runCloakbrowserFetch(repoRoot, targetUrl, outputPath, extraArgs);
  }
  return runScraplingFetch(repoRoot, fetcher, targetUrl, outputPath, extraArgs);
}

// =============================================================================
// Obscura preflight, serve pool, and concurrent fetch
// =============================================================================

function runObscuraPreflight(repoRoot, allowInstall) {
  const managedDir = path.join(os.homedir(), ".cache", "chrome-agent-obscura", "bin");
  const managedBin = path.join(managedDir, "obscura");
  const envPath = process.env.OBSCURA_CLI_PATH;

  const result = { ok: false, path: null, version: null, workerOk: false, source: null };

  if (envPath && fs.existsSync(envPath)) {
    const v = spawnSync(envPath, ["--help"], { encoding: "utf8" });
    if (v.status === 0) {
      result.path = envPath;
      result.source = "env";
    }
  }

  if (!result.path && fs.existsSync(managedBin)) {
    const v = spawnSync(managedBin, ["--help"], { encoding: "utf8" });
    if (v.status === 0) {
      result.path = managedBin;
      result.source = "managed";
    }
  }

  if (!result.path && allowInstall) {
    const installScript = path.join(repoRoot, "scripts", "obscura-cli-preflight.sh");
    if (fs.existsSync(installScript)) {
      const install = spawnSync("bash", [installScript], { cwd: repoRoot, encoding: "utf8" });
      if (install.status === 0 && fs.existsSync(managedBin)) {
        const v = spawnSync(managedBin, ["--help"], { encoding: "utf8" });
        if (v.status === 0) {
          result.path = managedBin;
          result.source = "installed";
        }
      }
    }
  }

  if (!result.path) {
    return result;
  }

  // Version detection
  const versionOut = spawnSync(result.path, ["--version"], { encoding: "utf8" });
  if (versionOut.status === 0) {
    const m = versionOut.stdout.match(/(\d+\.\d+\.\d+)/);
    result.version = m ? m[1] : null;
  }

  // Worker binary check
  const workerPath = path.join(path.dirname(result.path), "obscura-worker");
  if (fs.existsSync(workerPath)) {
    const w = spawnSync(workerPath, ["--help"], { encoding: "utf8" });
    result.workerOk = w.status === 0;
  }

  result.ok = true;
  return result;
}

function runObscuraFetch(repoRoot, targetUrl, outputPath, extraArgs = []) {
  ensureDir(path.dirname(outputPath));
  const preflight = runObscuraPreflight(repoRoot, true);
  if (!preflight.ok || !preflight.path) {
    return {
      ok: false,
      preflight,
      summary: "Obscura CLI preflight failed.",
      stderr: "Obscura binary not available.",
    };
  }
  const args = ["fetch", targetUrl, "--dump", "html", ...extraArgs];
  const result = spawnSync(preflight.path, args, { cwd: repoRoot, encoding: "utf8" });
  if (result.status === 0) {
    fs.writeFileSync(outputPath, result.stdout, "utf8");
  }
  return {
    ok: result.status === 0,
    preflight,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
    command: [preflight.path, ...args].join(" "),
  };
}

function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close();
      resolve(true);
    });
    server.listen(port, "127.0.0.1");
  });
}

async function findAvailablePort(startPort = 9200, maxAttempts = 100) {
  for (let i = 0; i < maxAttempts; i += 1) {
    const port = startPort + i;
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  throw new Error(`No available port found in range ${startPort}-${startPort + maxAttempts - 1}`);
}

async function startObscuraServe(obscuraPath, workers, port) {
  const child = spawn(obscuraPath, ["serve", "--workers", String(workers), "--port", String(port)], {
    detached: true,
    stdio: ["ignore", "ignore", "ignore"],
  });

  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    try {
      const resp = await new Promise((resolve, reject) => {
        const req = net.createConnection({ host: "127.0.0.1", port }, () => {
          req.write("GET /json/version HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n");
        });
        let data = "";
        req.on("data", (chunk) => { data += chunk; });
        req.on("end", () => resolve(data));
        req.on("error", reject);
        req.setTimeout(500, () => req.destroy());
      });
      if (resp.includes("200 OK") || resp.includes("Browser")) {
        return { process: child, port, workers, obscuraPath };
      }
    } catch {
      // not ready yet
    }
    await new Promise((r) => setTimeout(r, 200));
  }

  try { child.kill("SIGTERM"); } catch { /* ignore */ }
  throw new Error("Obscura serve failed to become ready within 5 seconds");
}

function isProcessAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function stopObscuraServe(handle) {
  const { process: child } = handle;
  if (!child || !child.pid) return;

  try {
    process.kill(-child.pid, "SIGTERM");
  } catch {
    try {
      child.kill("SIGTERM");
    } catch { /* ignore */ }
  }

  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    if (!isProcessAlive(child.pid)) {
      return;
    }
  }

  try {
    process.kill(-child.pid, "SIGKILL");
  } catch {
    try {
      child.kill("SIGKILL");
    } catch { /* ignore */ }
  }
}

async function concurrentFetch(serveHandle, urls, timeout = 15) {
  const { port, workers, obscuraPath } = serveHandle;
  const maxConcurrency = Math.min(urls.length, workers);
  const results = [];
  let index = 0;

  async function worker() {
    while (index < urls.length) {
      const i = index++;
      const url = urls[i];
      const start = Date.now();
      try {
        const child = spawn(obscuraPath, [
          "fetch", url,
          "--dump", "html",
          "--quiet",
          "--timeout", String(timeout),
        ], { encoding: "utf8" });

        let stdout = "";
        let stderr = "";
        child.stdout.on("data", (data) => { stdout += data; });
        child.stderr.on("data", (data) => { stderr += data; });

        const exitCode = await new Promise((resolve) => {
          child.on("close", resolve);
          child.on("error", () => resolve(-1));
        });

        const elapsed = Date.now() - start;
        if (exitCode !== 0) {
          results[i] = { url, html: null, elapsed_ms: elapsed, error: stderr || "fetch failed" };
        } else {
          results[i] = { url, html: stdout, elapsed_ms: elapsed, error: null };
        }
      } catch (err) {
        results[i] = { url, html: null, elapsed_ms: Date.now() - start, error: err.message };
      }
    }
  }

  const promises = [];
  for (let w = 0; w < maxConcurrency; w += 1) {
    promises.push(worker());
  }
  await Promise.all(promises);
  return results;
}

// Simple HTML-to-Markdown converter for Obscura parallel path
function htmlToMarkdown(html) {
  if (!html) return "";
  let md = html;

  // Remove script/style tags and their contents
  md = md.replace(/<script[\s\S]*?<\/script>/gi, "");
  md = md.replace(/<style[\s\S]*?<\/style>/gi, "");
  md = md.replace(/<nav[\s\S]*?<\/nav>/gi, "");
  md = md.replace(/<header[\s\S]*?<\/header>/gi, "");
  md = md.replace(/<footer[\s\S]*?<\/footer>/gi, "");

  // Headings
  md = md.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, (_, c) => `# ${stripTags(c)}\n\n`);
  md = md.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, (_, c) => `## ${stripTags(c)}\n\n`);
  md = md.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, (_, c) => `### ${stripTags(c)}\n\n`);
  md = md.replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, (_, c) => `#### ${stripTags(c)}\n\n`);
  md = md.replace(/<h5[^>]*>([\s\S]*?)<\/h5>/gi, (_, c) => `##### ${stripTags(c)}\n\n`);
  md = md.replace(/<h6[^>]*>([\s\S]*?)<\/h6>/gi, (_, c) => `###### ${stripTags(c)}\n\n`);

  // Block elements
  md = md.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, (_, c) => `${inlineToMd(c)}\n\n`);
  md = md.replace(/<div[^>]*>([\s\S]*?)<\/div>/gi, (_, c) => `${inlineToMd(c)}\n\n`);
  md = md.replace(/<article[^>]*>([\s\S]*?)<\/article>/gi, (_, c) => `${inlineToMd(c)}\n\n`);
  md = md.replace(/<section[^>]*>([\s\S]*?)<\/section>/gi, (_, c) => `${inlineToMd(c)}\n\n`);
  md = md.replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, (_, c) => {
    const text = inlineToMd(c).trim();
    return text.split("\n").map((l) => `> ${l}`).join("\n") + "\n\n";
  });
  md = md.replace(/<pre[^>]*>([\s\S]*?)<\/pre>/gi, (_, c) => `\`\`\`\n${stripTags(c)}\n\`\`\`\n\n`);

  // Lists
  md = md.replace(/<ul[^>]*>([\s\S]*?)<\/ul>/gi, (_, c) => processList(c, "ul") + "\n");
  md = md.replace(/<ol[^>]*>([\s\S]*?)<\/ol>/gi, (_, c) => processList(c, "ol") + "\n");

  // Inline elements
  md = md.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, (_, c) => `**${inlineToMd(c)}**`);
  md = md.replace(/<b[^>]*>([\s\S]*?)<\/b>/gi, (_, c) => `**${inlineToMd(c)}**`);
  md = md.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, (_, c) => `*${inlineToMd(c)}*`);
  md = md.replace(/<i[^>]*>([\s\S]*?)<\/i>/gi, (_, c) => `*${inlineToMd(c)}*`);
  md = md.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (_, c) => `\`${stripTags(c)}\``);
  md = md.replace(/<a[^>]+href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, (_, href, text) => {
    const t = inlineToMd(text).trim();
    if (!t) return "";
    return `[${t}](${href})`;
  });
  md = md.replace(/<img[^>]+src="([^"]*)"[^>]*>/gi, (_, src) => {
    const altMatch = _.match(/alt="([^"]*)"/);
    const alt = altMatch ? altMatch[1] : "image";
    return `![${alt}](${src})`;
  });
  md = md.replace(/<br\s*\/?>/gi, "\n");
  md = md.replace(/<hr\s*\/?>/gi, "\n---\n\n");

  // Tables (simple)
  md = md.replace(/<table[^>]*>([\s\S]*?)<\/table>/gi, (_, c) => processTable(c));

  // Remove remaining tags
  md = stripTags(md);

  // Cleanup whitespace
  md = md.replace(/\n{3,}/g, "\n\n");
  md = md.replace(/[ \t]+\n/g, "\n");
  return md.trim();
}

function stripTags(html) {
  return html.replace(/<[^>]+>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&nbsp;/g, " ");
}

function inlineToMd(html) {
  let md = html;
  md = md.replace(/<strong[^>]*>([\s\S]*?)<\/strong>/gi, (_, c) => `**${inlineToMd(c)}**`);
  md = md.replace(/<b[^>]*>([\s\S]*?)<\/b>/gi, (_, c) => `**${inlineToMd(c)}**`);
  md = md.replace(/<em[^>]*>([\s\S]*?)<\/em>/gi, (_, c) => `*${inlineToMd(c)}*`);
  md = md.replace(/<i[^>]*>([\s\S]*?)<\/i>/gi, (_, c) => `*${inlineToMd(c)}*`);
  md = md.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (_, c) => `\`${stripTags(c)}\``);
  md = md.replace(/<a[^>]+href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, (_, href, text) => {
    const t = inlineToMd(text).trim();
    if (!t) return "";
    return `[${t}](${href})`;
  });
  md = md.replace(/<br\s*\/?>/gi, "\n");
  return stripTags(md);
}

function processList(html, type) {
  const items = [];
  const regex = /<li[^>]*>([\s\S]*?)<\/li>/gi;
  let m;
  let idx = 1;
  while ((m = regex.exec(html)) !== null) {
    const prefix = type === "ol" ? `${idx++}.` : "-";
    const text = inlineToMd(m[1]).trim();
    items.push(`${prefix} ${text}`);
  }
  return items.join("\n");
}

function processTable(html) {
  const rows = [];
  const rowRegex = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
  let rowMatch;
  while ((rowMatch = rowRegex.exec(html)) !== null) {
    const cells = [];
    const cellRegex = /<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi;
    let cellMatch;
    while ((cellMatch = cellRegex.exec(rowMatch[1])) !== null) {
      cells.push(inlineToMd(cellMatch[1]).trim().replace(/\|/g, "\\|"));
    }
    if (cells.length > 0) rows.push(cells);
  }
  if (rows.length === 0) return "";
  const header = rows[0];
  const separator = header.map(() => "---");
  const lines = [
    `| ${header.join(" | ")} |`,
    `| ${separator.join(" | ")} |`,
    ...rows.slice(1).map((r) => `| ${r.join(" | ")} |`),
  ];
  return lines.join("\n") + "\n\n";
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

function urlToStructuredPath(urlStr, baseDir) {
  const url = new URL(urlStr);
  let pathname = url.pathname.replace(/^\/+/, "");
  if (!pathname || pathname === "/") pathname = "index";
  // slugify special chars but preserve path separators
  pathname = pathname
    .replace(/[^a-zA-Z0-9/_-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/(^-|-$)/g, "");
  if (!pathname.endsWith(".md")) pathname += ".md";
  return path.join(baseDir, pathname);
}

function relativizeMarkdownLinks(content, mdPath, urlToPathMap) {
  const baseDir = path.dirname(mdPath);

  // Helper: compute relative path from current file to target file
  const makeRel = (targetPath) => {
    let rel = path.relative(baseDir, targetPath).replace(/\\/g, "/");
    if (!rel.startsWith(".")) rel = "./" + rel;
    return rel;
  };

  // Replace Markdown links: [text](absolute_url)
  content = content.replace(/\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g, (match, text, url) => {
    if (urlToPathMap[url]) {
      return `[${text}](${makeRel(urlToPathMap[url])})`;
    }
    return match;
  });

  // Replace bare absolute URLs on their own line or in angle brackets
  content = content.replace(/<(https?:\/\/[^>]+)>/g, (match, url) => {
    if (urlToPathMap[url]) {
      return `[${url}](${makeRel(urlToPathMap[url])})`;
    }
    return match;
  });

  return content;
}

function collectMarkdownArtifacts(runDir) {
  const artifacts = [];
  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.name.endsWith(".md") && !entry.name.endsWith(".error.log")) {
        const rel = path.relative(runDir, fullPath);
        artifacts.push(absoluteArtifact(fullPath, "disposable", `Converted page ${rel}`));
      }
    }
  }
  walk(runDir);
  return artifacts;
}

function convertTraversalToMarkdown(repoRoot, runDir, manifest, opts = {}) {
  const {
    fetcherFn = () => "get",
    concurrency = 5,
    merge = false,
    cleanupHtml = true,
    outputName = "output",
    relativize = true,
    prefetchedHtml = null,
  } = opts;

  const visited = manifest.visited ?? [];
  const successful = [];
  const failed = [];
  const urlToPath = {};

  // NOTE: v1 processes sequentially because runScraplingFetch uses spawnSync.
  // True concurrency requires async spawn; concurrency param is reserved for v2.
  for (let i = 0; i < visited.length; i += 1) {
    const url = visited[i];
    const mdPath = urlToStructuredPath(url, runDir);
    ensureDir(path.dirname(mdPath));
    urlToPath[url] = mdPath;

    if (prefetchedHtml?.[url]) {
      // Use Scrapling --ai-targeted via file:// for DOM-quality Markdown conversion
      const tmpHtmlPath = path.join(runDir, `_tmp_${i}.html`);
      writeTextFile(tmpHtmlPath, prefetchedHtml[url]);
      const scraplingResult = runEngineFetch(repoRoot, "get", `file://${tmpHtmlPath}`, mdPath, ["--ai-targeted"]);
      fs.unlinkSync(tmpHtmlPath);
      if (scraplingResult.ok) {
        successful.push({ url, path: mdPath });
      } else {
        // Fallback to htmlToMarkdown when Scrapling CLI is unavailable
        const markdown = htmlToMarkdown(prefetchedHtml[url]);
        writeTextFile(mdPath, markdown);
        successful.push({ url, path: mdPath });
      }
      continue;
    }

    const fetcher = fetcherFn(url);
    const result = runEngineFetch(repoRoot, fetcher, url, mdPath, ["--ai-targeted"]);
    if (result.ok) {
      successful.push({ url, path: mdPath });
    } else {
      failed.push({ url, error: result.stderr || "Scrapling markdown conversion failed." });
      const errorPath = `${mdPath}.error.log`;
      writeTextFile(errorPath, result.stderr || "Scrapling markdown conversion failed.");
    }
  }

  // Post-process: relativize internal links
  if (relativize && Object.keys(urlToPath).length > 0) {
    for (const { path: mdPath } of successful) {
      let content = fs.readFileSync(mdPath, "utf8");
      content = relativizeMarkdownLinks(content, mdPath, urlToPath);
      writeTextFile(mdPath, content);
    }
  }

  // Cleanup HTML intermediates
  if (cleanupHtml) {
    for (const file of fs.readdirSync(runDir)) {
      if (file.endsWith(".html")) {
        fs.unlinkSync(path.join(runDir, file));
      }
    }
  }

  // Merge
  let mergedPath = null;
  if (merge && successful.length > 0) {
    mergedPath = path.join(runDir, `${outputName}.md`);
    mergeMarkdownFiles(successful.map((s) => s.path), mergedPath, manifest.target);
  }

  return { successful, failed, mergedPath, urlToPath };
}

function mergeMarkdownFiles(filePaths, outputPath, targetUrl) {
  const toc = [];
  const sections = [];
  const outputName = path.basename(outputPath, ".md");

  for (const filePath of filePaths.sort()) {
    const content = fs.readFileSync(filePath, "utf8");
    const lines = content.split("\n");
    const firstHeading = lines.find((line) => line.startsWith("# "));
    const title = firstHeading ? firstHeading.slice(2).trim() : path.basename(filePath, ".md");
    const anchor = title.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-").replace(/^-|-$/g, "");
    toc.push(`- [${title}](#${anchor})`);
    sections.push(`## ${title}\n\n${content}`);
  }

  const merged = [
    `# ${outputName.includes("crawl") ? "Crawl" : "Scrape"} Output: ${targetUrl}`,
    "",
    "## Table of Contents",
    ...toc,
    "",
    "---",
    "",
    sections.join("\n\n---\n\n"),
    "",
  ].join("\n");

  writeTextFile(outputPath, merged);
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

// =============================================================================
// Handoff emission
// =============================================================================

/**
 * Determine whether a failure is internal (chrome-agent-repo-bound) or external.
 * Internal failures generate a handoff document; external failures do not.
 */
function isInternalFailure(command, errorInfo) {
  const { exitCode, reason, stderr } = errorInfo;

  // Pipeline exit code >= 10 → internal (MediaWiki API pipeline signals)
  if (typeof exitCode === "number" && exitCode >= 10) {
    return true;
  }

  // Strategy gap (no matching strategy) + deep discovery failure
  if (reason === "strategy_gap") {
    return true;
  }

  // Engine preflight failure (Scrapling, Obscura, CloakBrowser)
  if (reason === "preflight_failure") {
    return true;
  }

  // Sample conversion / self-check unrecoverable failure
  if (reason === "conversion_failure") {
    return true;
  }

  // Deep discovery pipeline failure
  if (reason === "deep_discovery_failure") {
    return true;
  }

  // Python deps missing for explore pipeline
  if (reason === "explore_deps_missing") {
    return true;
  }

  return false;
}

/**
 * Generate a handoff document for an internal failure.
 * Writes to outputs/handoffs/<run-tag>/handoff.md.
 * Returns { path: string, summary: string }.
 */
function generateHandoff(context) {
  const { command, target, repoRef, runDir, error, strategy } = context;
  const { stamp, slug } = nowParts();
  const runTag = `${stamp}-${command}-${slug}`;
  const handoffDir = path.join(inferredRepoRoot, "outputs", "handoffs", runTag);
  ensureDir(handoffDir);

  const timestamp = new Date().toISOString();
  const cliCommand = `chrome-agent ${command} ${target}`;

  // Build handoff content
  const lines = [
    `# Handoff: ${command} ${target}`,
    "",
    "## Context",
    "",
    `| Field | Value |`,
    `|-------|-------|`,
    `| Command | \`${command}\` |`,
    `| Target | ${target} |`,
    `| Timestamp | ${timestamp} |`,
    `| Repo ref | ${repoRef ?? DEFAULT_REPO_REF} |`,
  ];

  if (runDir) {
    lines.push(`| Run directory | ${path.resolve(runDir)} |`);
  }
  if (strategy) {
    lines.push(`| Strategy | ${strategy.path ?? "unknown"} |`);
  }
  lines.push("");

  lines.push("## What Went Wrong");
  lines.push("");
  lines.push(error.summary || "An internal failure occurred during command execution.");
  lines.push("");

  lines.push("## Error Details");
  lines.push("");
  if (error.exitCode != null) {
    lines.push(`- **Exit code**: ${error.exitCode}`);
  }
  if (error.reason) {
    lines.push(`- **Reason**: ${error.reason}`);
  }
  if (error.stderr) {
    const truncatedStderr = error.stderr.length > 2000 ? error.stderr.slice(0, 2000) + "\n... (truncated)" : error.stderr;
    lines.push(`- **stderr**:\n\`\`\``);
    lines.push(truncatedStderr);
    lines.push("\`\`\`");
  }
  lines.push(`- **CLI command**: \`${cliCommand}\``);
  lines.push("");

  lines.push("## Run Artifacts");
  lines.push("");
  if (runDir && fs.existsSync(path.resolve(runDir))) {
    const absRunDir = path.resolve(runDir);
    lines.push(`- **Manifest**: ${path.join(absRunDir, "manifest.json")}`);
    for (const file of fs.readdirSync(absRunDir)) {
      if (file.endsWith(".log") || file.endsWith(".json")) {
        lines.push(`- **${file}**: ${path.join(absRunDir, file)}`);
      }
    }
  } else {
    lines.push("- No run directory was created before the failure.");
  }
  lines.push("");

  lines.push("## Next Steps");
  lines.push("");
  lines.push("This issue must be resolved in the chrome-agent repository.");
  lines.push("");
  lines.push("1. Review the run artifacts listed above");
  lines.push("2. Classify the issue:");
  lines.push("   - **P-line** (Pipeline): code defect or missing feature in pipeline scripts");
  lines.push("   - **S-line** (Strategy): strategy file configuration gap");
  lines.push("   - **W-line** (Workflow): external workflow script overrode pipeline capability");
  lines.push("3. Create an openspec change proposal");
  lines.push("4. Implement the fix");
  lines.push(`5. Re-run the original command to verify: \`${cliCommand}\``);
  lines.push("");

  const handoffContent = lines.join("\n") + "\n";
  const handoffPath = path.join(handoffDir, "handoff.md");
  writeTextFile(handoffPath, handoffContent);

  const summaryParts = [`[${command}]`];
  if (error.reason) summaryParts.push(error.reason);
  summaryParts.push(error.summary || "Internal failure");
  const handoffSummary = summaryParts.join(" ").slice(0, 200);

  return { path: path.resolve(handoffPath), summary: handoffSummary };
}

function runExplorePythonDepsCheck(repoRoot) {
  try {
    const result = spawnSync("python3", ["-c", "import bs4, yaml; print('ok')"], {
      cwd: repoRoot,
      encoding: "utf8",
      timeout: 15000,
    });
    if (result.status === 0 && (result.stdout || "").trim() === "ok") {
      return { ok: true, detail: "bs4, yaml available" };
    }
    const stderr = (result.stderr || "").trim();
    const missing = stderr.includes("bs4") || stderr.includes("beautifulsoup4") ? "bs4" : "yaml";
    return { ok: false, detail: `missing: ${missing}. Install: pip3 install beautifulsoup4 pyyaml` };
  } catch (err) {
    return { ok: false, detail: `python3 check failed: ${err.message}` };
  }
}

function runExplore(repoRoot, repoRef, resolutionMode, targetUrl, reportOverride) {
  const { runDir, reportPath } = buildRunPaths(repoRoot, "explore", targetUrl);
  const { strategy } = findStrategy(repoRoot, targetUrl);
  const matchingPage = strategy ? findMatchingPage(strategy.document, targetUrl) : null;
  const preflight = runScraplingPreflight(repoRoot, false);
  const recommendedFetcher = strategy ? selectFetcher(strategy, matchingPage) : null;

  let discoveryResult = null;
  if (!strategy) {
    // Preflight: check Python deps before spawning deep discovery
    const depsCheck = runExplorePythonDepsCheck(repoRoot);
    if (!depsCheck.ok) {
    // Handoff: Python deps missing for explore pipeline is internal
    const handoff = generateHandoff({ command: "explore", target: targetUrl, repoRef, runDir: null, error: { reason: "explore_deps_missing", summary: `Deep discovery pipeline dependencies are missing: ${depsCheck.detail}` } });
    return makeResult(
      "explore",
      targetUrl,
      repoRef,
      `Deep discovery pipeline dependencies are missing: ${depsCheck.detail}`,
      [],
      `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
      "failure",
      {
        workflow: "platform_analysis",
        engine_path: "strategy_registry -> strategy_gap -> preflight_failed",
        handoff_path: handoff.path,
        handoff_summary: handoff.summary,
      },
    );
    }

    ensureDir(runDir);

    // Phase 1: Run deep discovery pipeline (no silent catch)
    const ddResult = spawnSync("python3", [
      path.join(repoRoot, "scripts", "explore", "main.py"),
      repoRoot,
      targetUrl,
      "--run-dir", runDir,
    ], {
      cwd: repoRoot,
      encoding: "utf8",
      maxBuffer: 50 * 1024 * 1024,
    });
    if (ddResult.status === 0 && ddResult.stdout) {
      try {
        discoveryResult = JSON.parse(ddResult.stdout);
      } catch (parseErr) {
        // Handoff: deep discovery returned invalid JSON is internal
        const handoff = generateHandoff({ command: "explore", target: targetUrl, repoRef, runDir, error: { reason: "deep_discovery_failure", summary: `Deep discovery pipeline returned invalid JSON: ${String(parseErr.message).slice(0, 200)}`, stderr: (ddResult.stdout || "").slice(0, 2000) } });
        return makeResult(
          "explore",
          targetUrl,
          repoRef,
          `Deep discovery pipeline returned invalid JSON: ${String(parseErr.message).slice(0, 200)}`,
          [],
          `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
          "failure",
          {
            workflow: "platform_analysis",
            engine_path: "strategy_registry -> strategy_gap -> deep_discovery_failed",
            handoff_path: handoff.path,
            handoff_summary: handoff.summary,
          },
        );
      }
    } else {
      const stderr = (ddResult.stderr || "").slice(0, 500);
      // Handoff: deep discovery pipeline failure is internal
      const handoff = generateHandoff({ command: "explore", target: targetUrl, repoRef, runDir, error: { reason: "deep_discovery_failure", exitCode: ddResult.status, summary: `Deep discovery pipeline failed (exit ${ddResult.status ?? "unknown"}): ${stderr}`, stderr: (ddResult.stderr || "").slice(0, 2000) } });
      return makeResult(
        "explore",
        targetUrl,
        repoRef,
        `Deep discovery pipeline failed (exit ${ddResult.status ?? "unknown"}): ${stderr}`,
        [],
        `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
        "failure",
        {
          workflow: "platform_analysis",
          engine_path: "strategy_registry -> strategy_gap -> deep_discovery_failed",
          handoff_path: handoff.path,
          handoff_summary: handoff.summary,
        },
      );
    }

    // Legacy fallback if deep discovery unavailable — removed
  }

  const emitReport = shouldEmitReport("explore", reportOverride);
  const artifacts = [];
  if (!strategy) {
    // Deep discovery path (always populated — preflight/pipeline failure returns early)
    const probe = discoveryResult.probe_chain ?? {};
    const apis = discoveryResult.api_discovery ?? [];
    const struct = discoveryResult.structure_mapping ?? {};
    const prot = discoveryResult.protection ?? {};
    const scaffold = discoveryResult.scaffold ?? {};
    const samples = discoveryResult.samples ?? [];
    const selfCheck = discoveryResult.self_check ?? {};

    const successEngine = probe.success_engine ?? "none";
    const apiTypes = apis.map((a) => a.type).join(", ") || "none detected";
    const pageType = struct.page_type ?? "unknown";
    const protectionType = prot.type ?? "none";

    const summaryLines = [
      `No matching site strategy exists yet; deep discovery completed.`,
      `Success engine: ${successEngine}.`,
      `APIs detected: ${apiTypes}.`,
      `Page type: ${pageType}.`,
      `Protection: ${protectionType}.`,
    ];
    if (scaffold.path) {
      summaryLines.push(`Strategy scaffold: ${scaffold.path}.`);
    }

    const nextAction = scaffold.path
      ? `Review the generated scaffold at ${scaffold.path}, confirm samples, and run chrome-agent freeze ${scaffold.path} when ready.`
      : `Create or refine a site strategy for ${new URL(targetUrl).hostname}.`;

    const extraFields = {
      workflow: "platform_analysis",
      engine_path: `strategy_registry -> strategy_gap -> deep_discovery:${successEngine} -> protection:${protectionType}`,
      discovery: {
        engine_chain: probe.results ?? [],
        api: apis,
        content_profile: struct,
        protection: prot,
        scale: apis.find((a) => a.pages !== undefined)
          ? { pages: apis.find((a) => a.pages !== undefined).pages }
          : null,
      },
      scaffold: scaffold.path
        ? { path: scaffold.path, template_id: scaffold.template_id }
        : null,
      samples: samples.map((s) => s.title),
      self_check: selfCheck,
    };

    return makeResult(
      "explore",
      targetUrl,
      repoRef,
      summaryLines.join(" "),
      artifacts,
      nextAction,
      "partial_success",
      extraFields,
    );
  }

  // Determine conversion engine and converter path for agent guidance
  const hasApiPlatform = strategy?.document?.api?.platform === "mediawiki" || strategy?.document?.api?.platform === "mediawiki-fandom";
  const conversionEngine = hasApiPlatform ? "mediawiki-api" : (recommendedFetcher ?? "unknown");
  const converterPath = hasApiPlatform
    ? "scripts/explore/sample_converter.py fetch-and-apply"
    : undefined;

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
      conversion_engine: conversionEngine,
      ...(converterPath ? { converter_path: converterPath } : {}),
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
  // When fetcher is mediawiki-api, pass strategy path instead of scrapling flags
  const fetchExtraArgs = fetcher === "mediawiki-api" ? [strategy.path] : ["--ai-targeted"];
  const fetchResult = runEngineFetch(repoRoot, fetcher, targetUrl, outputPath, fetchExtraArgs);

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
    // Handoff: check if this is an internal failure
    const fetchErrorInfo = {
      exitCode: null,
      reason: fetchResult.preflight?.ok === false ? "preflight_failure" : null,
      stderr: fetchResult.stderr || "",
      summary: `Fetch failed after ${fetcher} dispatch.`,
    };
    if (isInternalFailure("fetch", fetchErrorInfo)) {
      const handoff = generateHandoff({
        command: "fetch",
        target: targetUrl,
        repoRef,
        runDir,
        error: fetchErrorInfo,
        strategy,
      });
      return makeResult(
        "fetch",
        targetUrl,
        repoRef,
        `Fetch failed after ${fetcher} dispatch.`,
        artifacts,
        `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
        "failure",
        {
          workflow: "content_retrieval",
          engine_path: `scrapling:${fetcher} -> preflight:${fetchResult.preflight?.status ?? "unknown"} -> failed`,
          handoff_path: handoff.path,
          handoff_summary: handoff.summary,
        },
      );
    }
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

function buildCrawlReport({ targetUrl, repoRef, resolutionMode, strategy, events, result, phase2, extractionMethod, fallbackReason }) {
  const lines = [
    `# Crawl Report`,
    "",
    `- Target: ${targetUrl}`,
    `- Repo ref: ${repoRef}`,
    `- Resolution: ${resolutionSummary(repoRef, resolutionMode)}`,
    `- Strategy file: ${strategy ? path.relative(process.cwd(), strategy.path) : "none"}`,
    `- Result: ${result}`,
  ];
  if (extractionMethod) {
    lines.push(`- Extraction method: ${extractionMethod}`);
  }
  if (fallbackReason) {
    lines.push(`- Fallback reason: ${fallbackReason}`);
  }
  lines.push("", "## Traversal");
  for (const event of events) {
    lines.push(`- ${event}`);
  }
  if (phase2) {
    lines.push("");
    lines.push("## Phase 2: Markdown Conversion");
    lines.push(`- Successful: ${phase2.successful}`);
    lines.push(`- Failed: ${phase2.failed}`);
    if (phase2.mergedPath) {
      lines.push(`- Merged output: ${phase2.mergedPath}`);
    }
  }
  return `${lines.join("\n")}\n`;
}

async function runCrawl(repoRoot, repoRef, resolutionMode, targetUrl, opts = {}) {
  const {
    entryPoint: entryPointOverride = null,
    maxPages = null,
    report: reportOverride = null,
    markdown = true,
    merge = false,
    concurrency = 5,
    keepHtml = false,
    parallel = false,
    workers = 5,
    discoveryOnly = false,
    fromManifest = null,
    yes: yesFlag = false,
    excludeCategory = [],
    phase = null,
    reFetch = false,
    outputDir = null,
  } = opts;

  let { runDir, reportPath } = buildRunPaths(repoRoot, "crawl", targetUrl);
  if (outputDir) {
    runDir = path.resolve(outputDir);
  }
  ensureDir(runDir);
  const manifestPath = path.join(runDir, "manifest.json");
  const emitReport = shouldEmitReport("crawl", reportOverride);
  const { strategy } = findStrategy(repoRoot, targetUrl);

  if (!strategy) {
    return crawlInternalError({
      targetUrl, repoRef, resolutionMode, strategy: null, runDir: null, reportPath, emitReport,
      eventMsg: "No matching site strategy exists, so crawl was refused before traversal started.",
      resultMsg: "Crawl refused because no matching site strategy exists.",
      handoffReason: "strategy_gap",
      handoffSummary: "No matching site strategy exists.",
      enginePath: "strategy_registry -> strategy_gap",
    });
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
    return crawlInternalError({
      targetUrl, repoRef, resolutionMode, strategy, runDir, reportPath, emitReport,
      eventMsg: "Strategy exists but no usable entry point could be resolved.",
      resultMsg: "Crawl could not resolve a declared entry point.",
      handoffReason: "conversion_failure",
      handoffSummary: "Strategy exists but no usable entry point could be resolved.",
      enginePath: `strategy_registry -> ${path.relative(repoRoot, strategy.path)} -> missing_entry_point`,
    });
  }

  const apiConfig = doc?.api;
  if (apiConfig && apiConfig.platform === "mediawiki") {
    return runCrawlMediawikiApi(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints, opts);
  }
  if (discoveryOnly && !doc?.api?.platform) {
    return runCrawlScraplingDiscovery(repoRoot, repoRef, resolutionMode, runDir, reportPath, emitReport, targetUrl, strategy, doc, startPage, opts);
  }
  return runCrawlScrapling(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints, opts);
}

function crawlInternalError({ targetUrl, repoRef, resolutionMode, strategy, runDir, reportPath, emitReport, eventMsg, resultMsg, handoffReason, handoffSummary, enginePath }) {
  if (emitReport) {
    const report = buildCrawlReport({
      targetUrl, repoRef, resolutionMode, strategy,
      events: [eventMsg],
      result: "failure",
    });
    writeTextFile(reportPath, report);
  }
  const artifacts = [];
  if (emitReport) {
    artifacts.push(absoluteArtifact(reportPath, "durable", "Crawl failure report"));
  }
  const handoff = generateHandoff({ command: "crawl", target: targetUrl, repoRef, runDir, error: { reason: handoffReason, summary: handoffSummary }, strategy });
  return makeResult(
    "crawl", targetUrl, repoRef, resultMsg, artifacts,
    `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
    "failure",
    { workflow: "content_retrieval", engine_path: enginePath, handoff_path: handoff.path, handoff_summary: handoff.summary },
  );
}

function runCrawlMediawikiApi(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints, opts) {
  const {
    maxPages = null,
    concurrency = 5,
    discoveryOnly = false,
    fromManifest = null,
    yes: yesFlag = false,
    excludeCategory = [],
    phase = null,
    reFetch = false,
  } = opts;
  const apiConfig = doc?.api;
  const extractionScript = path.join(repoRoot, "scripts", "pipeline");
  if (fs.existsSync(extractionScript)) {
    console.log("Strategy has api.platform=mediawiki — routing to MediaWiki API extraction pipeline");
    const apiArgs = [
      "-m", "scripts.pipeline",
      targetUrl,
      "--strategy", strategy.path,
      "--output", runDir,
      "--concurrency", String(concurrency),
    ];
    // Pass --discovery based on strategy config
    if (apiConfig?.homepage) {
      apiArgs.push("--discovery", "homepage");
    } else {
      apiArgs.push("--discovery", "allpages");
    }
    // Pass --phase discover when --discovery-only
    if (discoveryOnly) {
      apiArgs.push("--phase", "discover");
    }
    // Pass --phase from opts (fetch, convert, assemble)
    if (phase && !discoveryOnly) {
      apiArgs.push("--phase", phase);
    }
    // Pass --re-fetch flag
    if (reFetch) {
      apiArgs.push("--re-fetch");
    }
    // Pass --from-manifest when resuming from existing manifest
    if (fromManifest) {
      apiArgs.push("--from-manifest", fromManifest);
    }
    // Pass --exclude-category
    for (const cat of excludeCategory) {
      apiArgs.push("--exclude-category", cat);
    }
    // Pass --max-pages
    if (maxPages != null) {
      apiArgs.push("--max-pages", String(maxPages));
    }
    const apiResult = spawnSync("python3", apiArgs, {
      cwd: repoRoot,
      encoding: "utf-8",
      timeout: 600_000,  // 10 min max
    });

    const exitCode = apiResult.status ?? 1;
    const isApiSuccess = exitCode === 0;
    const isApiPartial = exitCode === 1;
    const isApiFailure = exitCode >= 10;  // API_UNREACHABLE, PHASE_A/B/C_FAILURE

    if (isApiSuccess || isApiPartial) {
      // --- Discovery-only mode: return summary and exit early ---
      if (discoveryOnly) {
        const discoverySummaryPath = path.join(runDir, "discovery_summary.json");
        const pageManifestPath = path.join(runDir, "page_manifest.json");
        const discArtifacts = [];
        if (fs.existsSync(pageManifestPath)) {
          discArtifacts.push(absoluteArtifact(pageManifestPath, "disposable", "Page manifest"));
        }
        if (fs.existsSync(discoverySummaryPath)) {
          discArtifacts.push(absoluteArtifact(discoverySummaryPath, "disposable", "Discovery summary"));
        }
        return makeResult("crawl", targetUrl, repoRef,
          `Discovery-only completed via MediaWiki API pipeline.`,
          discArtifacts,
          "Review discovery summary. Use --from-manifest to proceed with extraction.",
          isApiSuccess ? "success" : "partial_success",
          {
            workflow: "content_retrieval",
            engine_path: `strategy_registry -> mediawiki_api_pipeline -> discovery_only -> exit:${exitCode}`,
            extraction_method: "mediawiki_api",
            discovery_only: true,
            discovery_summary_path: fs.existsSync(discoverySummaryPath) ? path.resolve(discoverySummaryPath) : null,
            manifest_path: fs.existsSync(pageManifestPath) ? path.resolve(pageManifestPath) : null,
            confirmation_bypassed: yesFlag,
          });
      }

      // Collect artifacts from the output directory
      const apiArtifacts = [absoluteArtifact(manifestPath, "disposable", "Crawl manifest")];
      for (const file of fs.readdirSync(runDir, { recursive: true })) {
        const filePath = path.join(runDir, String(file));
        if (String(file).endsWith(".md")) {
          apiArtifacts.push(absoluteArtifact(filePath, "disposable", `API extracted: ${file}`));
        }
      }
      // Add extraction results if present
      const resultsPath = path.join(runDir, "extraction_results.json");
      if (fs.existsSync(resultsPath)) {
        apiArtifacts.push(absoluteArtifact(resultsPath, "disposable", "Extraction results"));
      }

      const extractionMethod = "mediawiki_api";
      const resultState = isApiSuccess ? "success" : "partial_success";
      const summary = isApiSuccess
        ? `Crawl completed via MediaWiki API extraction pipeline.`
        : `Crawl completed via MediaWiki API pipeline with partial success (some pages failed).`;

      if (emitReport) {
        const report = buildCrawlReport({
          targetUrl, repoRef, resolutionMode, strategy,
          events: [
            `Routed to MediaWiki API extraction pipeline (platform=mediawiki).`,
            `Pipeline exit code: ${exitCode}`,
          ],
          result: resultState,
          extractionMethod,
        });
        writeTextFile(reportPath, report);
        apiArtifacts.unshift(absoluteArtifact(reportPath, "durable", "Crawl report"));
      }

      return makeResult("crawl", targetUrl, repoRef, summary, apiArtifacts,
        "Inspect the crawl outputs in the run directory.",
        resultState, {
          workflow: "content_retrieval",
          engine_path: `strategy_registry -> mediawiki_api_pipeline -> exit:${exitCode}`,
          extraction_method: extractionMethod,
          confirmation_bypassed: yesFlag,
        });
    }

    // API failure — log and fall through to Scrapling
    console.warn(`MediaWiki API pipeline failed (exit code ${exitCode}), falling back to Scrapling`);
    // API failure — delegate to Scrapling crawl
    return runCrawlScrapling(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints, opts);
  } else {
    console.warn("pipeline script not found, falling back to Scrapling");
    // Script missing — delegate to Scrapling crawl
    return runCrawlScrapling(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints, opts);
  }
}

function runCrawlScraplingDiscovery(repoRoot, repoRef, resolutionMode, runDir, reportPath, emitReport, targetUrl, strategy, doc, startPage, opts) {
  const { yes: yesFlag = false } = opts;
  const preflight = runScraplingPreflight(repoRoot, true);
  if (!preflight.ok) {
    return makeResult("crawl", targetUrl, repoRef,
      "Scrapling CLI preflight failed for discovery-only mode.",
      [],
      "Fix Scrapling CLI preflight and retry.",
      "failure",
      { workflow: "content_retrieval", engine_path: "scrapling_preflight -> discovery_only_blocked" });
  }

  const fetcher = selectFetcher(strategy, startPage);
  const outputPath = path.join(runDir, "_homepage.html");
  const fetchResult = runEngineFetch(repoRoot, fetcher, targetUrl, outputPath);
  if (!fetchResult.ok) {
    return makeResult("crawl", targetUrl, repoRef,
      `Failed to fetch main page for discovery: ${fetchResult.stderr || "unknown error"}`,
      [], "Check URL and retry.", "failure",
      { workflow: "content_retrieval", engine_path: `scrapling:${fetcher} -> discovery_fetch_failed` });
  }

  // Extract links matching links_to selectors and group by structure.pages
  const categories = [];
  const linksTo = startPage?.links_to ?? [];
  const structurePages = doc?.structure?.pages ?? [];
  const categoryMap = new Map(); // pageId -> { urls: Set }

  for (const link of linksTo) {
    const targetPage = structurePages.find((p) => p.id === link.target);
    if (!targetPage) continue;

    const discovered = collectLinksFromHtml(outputPath, targetUrl, link.selector);
    if (!categoryMap.has(targetPage.id)) {
      categoryMap.set(targetPage.id, { page: targetPage, urls: new Set() });
    }
    for (const url of discovered) {
      if (pagePatternMatches(targetPage, url)) {
        categoryMap.get(targetPage.id).urls.add(url);
      }
    }
  }

  let totalPages = 0;
  for (const [pageId, data] of categoryMap) {
    const count = data.urls.size;
    totalPages += count;
    const samples = [...data.urls].slice(0, 5).map((u) => {
      try { return decodeURIComponent(new URL(u).pathname.split("/").pop() || u).replace(/_/g, " "); } catch { return u; }
    });
    categories.push({
      name: data.page.label || data.page.id,
      directory: data.page.id,
      type: data.page.type || "static_article",
      is_index_page: false,
      page_count: count,
      sample_pages: samples,
      page_type: data.page.content_type || "wiki_article",
    });
  }

  const discoverySummary = {
    discovery_method: "first_level_links",
    site_title: doc.description?.split(" - ")[0] || targetUrl,
    domain: new URL(targetUrl).hostname,
    categories,
    excluded: [],
    unclassified: { count: 0, directory: "misc", sample_pages: [] },
    total_pages: totalPages,
    estimated_time_minutes: Math.max(Math.ceil(totalPages * 5 / 60), 1),
    manifest_path: null,
    warnings: [],
    caveats: [
      "Only first-level links from the main page were discovered.",
      "Actual page counts may differ after full traversal.",
    ],
    failure_rate: 0.0,
  };

  const summaryPath = path.join(runDir, "discovery_summary.json");
  writeTextFile(summaryPath, JSON.stringify(discoverySummary, null, 2));

  return makeResult("crawl", targetUrl, repoRef,
    `Discovery-only completed via Scrapling first-level link extraction (${totalPages} links across ${categories.length} categories).`,
    [absoluteArtifact(summaryPath, "disposable", "Discovery summary")],
    "Review discovery summary. Use --from-manifest to proceed with extraction (note: Scrapling path does not produce a page manifest).",
    "success",
    {
      workflow: "content_retrieval",
      engine_path: `strategy_registry -> scrapling_discovery_only -> first_level_links`,
      extraction_method: "scrapling",
      discovery_only: true,
      discovery_summary_path: path.resolve(summaryPath),
      manifest_path: null,
      confirmation_bypassed: yesFlag,
    });
}

async function runCrawlScrapling(repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints, opts) {
  const {
    maxPages = null,
    concurrency = 5,
    fromManifest = null,
    yes: yesFlag = false,
    excludeCategory = [],
    phase = null,
    reFetch = false,
    keepHtml = false,
    markdown = true,
    merge = false,
    parallel = false,
    workers = 5,
  } = opts;
let events = [];
let fallbackReason = null;
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
  // Handoff: Scrapling preflight failure is internal
  const handoff = generateHandoff({ command: "crawl", target: targetUrl, repoRef, runDir, error: { reason: "preflight_failure", summary: `Scrapling CLI preflight failed (${preflight.status ?? "unknown"}).`, stderr: `${preflight.stdout ?? ""}${preflight.stderr ?? ""}`.trim() }, strategy });
  return makeResult(
    "crawl",
    targetUrl,
    repoRef,
    "Crawl stopped because Scrapling CLI preflight failed.",
    artifacts,
    `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
    "failure",
    {
      workflow: "content_retrieval",
      engine_path: `strategy_registry -> scrapling_preflight:${preflight.status ?? "unavailable"} -> blocked`,
      handoff_path: handoff.path,
      handoff_summary: handoff.summary,
    },
  );
}

const queue = [];
// --- from-manifest: seed queue from existing manifest ---
if (fromManifest && fs.existsSync(fromManifest)) {
  try {
    const loadedManifest = JSON.parse(fs.readFileSync(fromManifest, "utf8"));
    const loadedVisited = loadedManifest.visited ?? [];
    for (const url of loadedVisited) {
      const page = pages.find((p) => pagePatternMatches(p, url));
      if (page) {
        queue.push({ url, page, paginationIndex: 1 });
      }
    }
    log.info(`Loaded ${queue.length} URLs from manifest for Scrapling traversal`);
  } catch (err) {
    console.warn(`Failed to load manifest: ${err.message}`);
  }
}
if (queue.length === 0) {
  const startUrl = matchingPage && matchingPage.id === startPage.id ? targetUrl : startPage.url_example;
  queue.push({ url: startUrl, page: startPage, paginationIndex: 1 });
}
const visited = new Set();
const artifacts = [];
// events already declared above (let events)
let failures = 0;

while (queue.length > 0 && (maxPages == null || visited.size < maxPages)) {
  const item = queue.shift();
  if (!item || visited.has(item.url)) {
    continue;
  }
  // --exclude-category filtering for Scrapling path (match by page id/label)
  if (excludeCategory.length > 0 && item.page) {
    const pageIdLower = (item.page.id || "").toLowerCase();
    const pageLabelLower = (item.page.label || "").toLowerCase();
    const isExcluded = excludeCategory.some(
      (cat) => cat.toLowerCase() === pageIdLower || cat.toLowerCase() === pageLabelLower,
    );
    if (isExcluded) {
      events.push(`Skipped ${item.url} — excluded category: ${item.page.id}`);
      continue;
    }
  }
  visited.add(item.url);
  const fetcher = selectFetcher(strategy, item.page);
  const pageSlug = `${String(visited.size).padStart(2, "0")}-${item.page.id}`;
  const outputPath = path.join(runDir, `${pageSlug}.html`);
  const fetchResult = runEngineFetch(repoRoot, fetcher, item.url, outputPath);

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

  if (item.page.pagination && item.page.pagination !== "none" && (maxPages == null || queue.length + visited.size < maxPages)) {
    if (item.page.pagination.mechanism === "url_parameter") {
      const nextPageNumber = item.paginationIndex + 1;
      const nextUrl = nextPaginationUrl(item.url, item.page.pagination, nextPageNumber);
      if (nextUrl && !visited.has(nextUrl) && (maxPages == null || queue.length + visited.size < maxPages)) {
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

// Determine domain for cache operations
const crawlDomain = new URL(targetUrl).hostname;
let phase2Result = null;

// --- Scrapling --phase fetch: save visited pages to cache, skip conversion ---
if (phase === "fetch" && visited.size > 0) {
  const domainCacheDir = scraplingCacheDir(repoRoot, crawlDomain);
  ensureDir(domainCacheDir);
  let cacheWriteCount = 0;
  let cacheSkipCount = 0;
  for (const url of visited) {
    const slug = scraplingSlugFromUrl(url);
    if (!reFetch && isScraplingCached(repoRoot, crawlDomain, slug)) {
      cacheSkipCount++;
      events.push(`Skipping cache write for ${url} (already cached)`);
      continue;
    }
    // Find the fetched HTML file for this URL
    let htmlContent = null;
    for (const f of fs.readdirSync(runDir)) {
      if (f.endsWith(".html")) {
        const fpath = path.join(runDir, f);
        const content = fs.readFileSync(fpath, "utf8");
        if (content.includes(url) || f.includes(slug)) {
          htmlContent = content;
          break;
        }
      }
    }
    if (htmlContent) {
      saveScraplingCache(repoRoot, crawlDomain, slug, htmlContent, {
        url, fetcher: "scrapling",
      });
      cacheWriteCount++;
      events.push(`Cached ${url} -> .cache/scrapling/${crawlDomain}/${slug}.html`);
    }
  }
  console.log(`Scrapling fetch phase: ${cacheWriteCount} cached, ${cacheSkipCount} skipped`);
}

// --- Scrapling --phase convert: read from cache and convert ---
if (phase === "convert" && fromManifest) {
  const manifestData = JSON.parse(fs.readFileSync(fromManifest, "utf8"));
  const urls = manifestData.visited || [];
  let convertOk = 0;
  let convertFail = 0;
  for (const url of urls) {
    const slug = scraplingSlugFromUrl(url);
    const cached = loadScraplingCache(repoRoot, crawlDomain, slug);
    if (!cached) {
      events.push(`Cache miss for ${url} — skipping`);
      convertFail++;
      continue;
    }
    const tmpHtmlPath = path.join(runDir, `_cached_${slug}.html`);
    writeTextFile(tmpHtmlPath, cached.html);
    const mdPath = urlToStructuredPath(url, runDir);
    const scraplingResult = runEngineFetch(repoRoot, "get", `file://${tmpHtmlPath}`, mdPath, ["--ai-targeted"]);
    if (scraplingResult.ok) {
      convertOk++;
      events.push(`Converted cached ${url} to Markdown`);
    } else {
      convertFail++;
      events.push(`Failed to convert cached ${url}`);
    }
    try { fs.unlinkSync(tmpHtmlPath); } catch {}
  }
  phase2Result = {
    successful: urls.slice(0, convertOk).map((url, i) => ({ url })),
    failed: urls.slice(0, convertFail).map((url, i) => ({ url, error: "conversion_failed" })),
    mergedPath: null,
  };
  console.log(`Scrapling convert phase: ${convertOk} converted, ${convertFail} failed`);
}

// Phase 2: Markdown conversion (standard path, not --phase fetch/convert)
let extractionMethod = "scrapling";
let parallelFallbackReason = null;

if (markdown && visited.size > 0 && phase !== "fetch" && phase2Result === null) {
  if (parallel) {
    const obscuraPreflight = runObscuraPreflight(repoRoot, true);
    if (obscuraPreflight.ok && obscuraPreflight.workerOk) {
      try {
        const port = await findAvailablePort();
        const serveHandle = await startObscuraServe(obscuraPreflight.path, workers, port);
        const fetchResults = await concurrentFetch(serveHandle, [...visited], 15);
        stopObscuraServe(serveHandle);

        const prefetchedHtml = {};
        for (const r of fetchResults) {
          if (r.html) {
            prefetchedHtml[r.url] = r.html;
          }
        }

        phase2Result = convertTraversalToMarkdown(repoRoot, runDir, manifest, {
          fetcherFn: (url) => {
            const page = pages.find((p) => pagePatternMatches(p, url));
            return selectFetcher(strategy, page);
          },
          concurrency,
          merge,
          cleanupHtml: !keepHtml,
          outputName: "crawl-output",
          prefetchedHtml,
        });
        extractionMethod = "obscura-serve-pool";
      } catch (err) {
        console.warn(`Obscura parallel fetch failed: ${err.message}. Falling back to Scrapling serial.`);
        parallelFallbackReason = err.message;
      }
    } else {
      console.warn("Obscura preflight failed or worker binary missing. Falling back to Scrapling serial.");
      parallelFallbackReason = "obscura_preflight_unavailable";
    }
  }

  if (!phase2Result) {
    phase2Result = convertTraversalToMarkdown(repoRoot, runDir, manifest, {
      fetcherFn: (url) => {
        const page = pages.find((p) => pagePatternMatches(p, url));
        return selectFetcher(strategy, page);
      },
      concurrency,
      merge,
      cleanupHtml: !keepHtml,
      outputName: "crawl-output",
    });
  }

  manifest.phase2 = {
    successful_count: phase2Result.successful.length,
    failed_count: phase2Result.failed.length,
    failed_urls: phase2Result.failed.map((f) => f.url),
    merged_path: phase2Result.mergedPath,
  };
}

writeTextFile(manifestPath, JSON.stringify(manifest, null, 2));

// Rebuild artifacts based on output mode
const finalArtifacts = [absoluteArtifact(manifestPath, "disposable", "Crawl manifest")];

if (markdown) {
  finalArtifacts.push(...collectMarkdownArtifacts(runDir));
  // Ensure merged file gets a descriptive label if found by collectMarkdownArtifacts
  for (const { url } of (phase2Result?.failed ?? [])) {
    const idx = manifest.visited.indexOf(url);
    if (idx >= 0) {
      const errorPath = path.join(runDir, `${String(idx + 1).padStart(2, "0")}.md.error.log`);
      if (fs.existsSync(errorPath)) {
        finalArtifacts.push(absoluteArtifact(errorPath, "disposable", `Conversion error for ${url}`));
      }
    }
  }
} else {
  for (const file of fs.readdirSync(runDir)) {
    if (file.endsWith(".html")) {
      finalArtifacts.push(absoluteArtifact(path.join(runDir, file), "disposable", `Crawled page ${file}`));
    }
  }
}

const traversalOk = visited.size > 0 && failures === 0;
const conversionOk = !markdown || (phase2Result && phase2Result.failed.length === 0);
const resultState =
  traversalOk && conversionOk ? "success" : visited.size > failures ? "partial_success" : "failure";

const finalExtractionMethod = extractionMethod;
const finalFallbackReason = parallelFallbackReason ?? fallbackReason;

if (emitReport) {
  const report = buildCrawlReport({
    targetUrl,
    repoRef,
    resolutionMode,
    strategy,
    events,
    result: resultState,
    phase2: markdown && phase2Result
      ? {
          successful: phase2Result.successful.length,
          failed: phase2Result.failed.length,
          mergedPath: phase2Result.mergedPath,
        }
      : null,
    extractionMethod: finalExtractionMethod,
    fallbackReason: finalFallbackReason,
  });
  writeTextFile(reportPath, report);
  finalArtifacts.unshift(absoluteArtifact(reportPath, "durable", "Crawl report"));
}

const summary =
  resultState === "success"
    ? `Crawl completed within declared strategy boundaries and visited ${visited.size} page(s)${markdown ? `; ${phase2Result.successful.length} converted to Markdown` : ""}.`
    : resultState === "partial_success"
      ? `Crawl visited ${visited.size} page(s)${markdown ? `; ${phase2Result.successful.length} converted, ${phase2Result.failed.length} failed` : ` with ${failures} fetch failure(s)`}.`
      : "Crawl failed before any page completed successfully.";
const nextAction =
  resultState === "failure"
    ? "Review the crawl report, strategy selectors, or authentication requirements before retrying."
    : "Inspect the crawl outputs. Extend the site strategy if more bounded traversal is needed.";

return makeResult("crawl", targetUrl, repoRef, summary, finalArtifacts, nextAction, resultState, {
  workflow: "content_retrieval",
  engine_path: `strategy_registry -> bounded_crawl -> scrapling_preflight:${preflight.status ?? "unknown"}${markdown ? ` -> markdown_conversion(${phase2Result?.successful.length ?? 0}/${visited.size})` : ""}`,
  extraction_method: finalExtractionMethod,
  ...(finalFallbackReason ? { fallback_reason: finalFallbackReason } : {}),
  confirmation_bypassed: yesFlag,
});
}

function extractAllLinks(htmlPath, baseUrl, opts = {}) {
  if (!fs.existsSync(htmlPath)) {
    return [];
  }
  const { sameDomain = true, matchPattern = null } = opts;
  const base = new URL(baseUrl);
  const html = fs.readFileSync(htmlPath, "utf8");
  const matches = [...html.matchAll(/<a\s[^>]*href="([^"#]+)"/gi)];
  const urls = new Set();
  for (const match of matches) {
    const href = match[1];
    try {
      const url = new URL(href, baseUrl);
      if (sameDomain && url.hostname !== base.hostname) {
        continue;
      }
      if (matchPattern && !minimatch(url.pathname, matchPattern)) {
        continue;
      }
      urls.add(url.toString());
    } catch {
      // skip malformed URLs
    }
  }
  return [...urls];
}

function minimatch(pathname, pattern) {
  // Simple glob matcher: supports * and **
  const regex = pattern
    .replace(/\*\*/g, "__DOUBLESTAR__")
    .replace(/\*/g, "[^/]*")
    .replace(/__DOUBLESTAR__/g, ".*");
  return new RegExp(`^${regex}$`).test(pathname);
}

function buildScrapeReport({ targetUrl, repoRef, resolutionMode, events, result, phase2 }) {
  const lines = [
    `# Scrape Report`,
    "",
    `- Target: ${targetUrl}`,
    `- Repo ref: ${repoRef}`,
    `- Resolution: ${resolutionSummary(repoRef, resolutionMode)}`,
    `- Result: ${result}`,
    "",
    "## Traversal",
  ];
  for (const event of events) {
    lines.push(`- ${event}`);
  }
  if (phase2) {
    lines.push("");
    lines.push("## Phase 2: Markdown Conversion");
    lines.push(`- Successful: ${phase2.successful}`);
    lines.push(`- Failed: ${phase2.failed}`);
    if (phase2.mergedPath) {
      lines.push(`- Merged output: ${phase2.mergedPath}`);
    }
  }
  return `${lines.join("\n")}\n`;
}

async function runScrape(repoRoot, repoRef, resolutionMode, targetUrl, opts) {
  const {
    maxPages = null,
    sameDomain = true,
    matchPattern = null,
    markdown = true,
    merge = false,
    concurrency = 5,
    fetcherOverride = null,
    keepHtml = false,
    reportOverride = null,
    parallel = false,
    workers = 5,
  } = opts;

  const { runDir, reportPath } = buildRunPaths(repoRoot, "scrape", targetUrl);
  ensureDir(runDir);
  const manifestPath = path.join(runDir, "manifest.json");
  const emitReport = shouldEmitReport("scrape", reportOverride);

  const preflight = runScraplingPreflight(repoRoot, true);
  if (!preflight.ok) {
    if (emitReport) {
      const report = buildScrapeReport({
        targetUrl,
        repoRef,
        resolutionMode,
        events: ["Scrapling CLI preflight failed before scrape traversal."],
        result: "failure",
      });
      writeTextFile(reportPath, report);
    }
    const artifacts = [];
    if (emitReport) {
      artifacts.push(absoluteArtifact(reportPath, "durable", "Scrape preflight report"));
    }
    // Handoff: Scrapling preflight failure is internal
    const handoff = generateHandoff({ command: "scrape", target: targetUrl, repoRef, runDir, error: { reason: "preflight_failure", summary: `Scrapling CLI preflight failed (${preflight.status ?? "unknown"}).`, stderr: `${preflight.stdout ?? ""}${preflight.stderr ?? ""}`.trim() } });
    return makeResult(
      "scrape",
      targetUrl,
      repoRef,
      "Scrape stopped because Scrapling CLI preflight failed.",
      artifacts,
      `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
      "failure",
      {
        workflow: "content_retrieval",
        engine_path: `scrapling_preflight:${preflight.status ?? "unavailable"} -> blocked`,
        handoff_path: handoff.path,
        handoff_summary: handoff.summary,
      },
    );
  }

  // Phase 1: Traversal
  const queue = [targetUrl];
  const visited = new Set();
  const events = [];
  let failures = 0;

  while (queue.length > 0 && (maxPages == null || visited.size < maxPages)) {
    const url = queue.shift();
    if (!url || visited.has(url)) {
      continue;
    }
    visited.add(url);
    const fetcher = fetcherOverride || "get";
    const pageNum = String(visited.size).padStart(2, "0");
    const outputPath = path.join(runDir, `${pageNum}.html`);
    const fetchResult = runEngineFetch(repoRoot, fetcher, url, outputPath);

    if (fetchResult.ok) {
      events.push(`Fetched ${url} via ${fetcher}.`);
      const discovered = extractAllLinks(outputPath, url, { sameDomain, matchPattern });
      for (const nextUrl of discovered) {
        if (!visited.has(nextUrl) && !queue.includes(nextUrl)) {
          queue.push(nextUrl);
        }
      }
      if (discovered.length > 0) {
        events.push(`Discovered ${discovered.length} new link(s) from ${url}.`);
      }
    } else {
      failures += 1;
      const errorPath = path.join(runDir, `${pageNum}.stderr.log`);
      writeTextFile(errorPath, fetchResult.stderr || "Scrapling scrape fetch failed.");
      events.push(`Failed ${url} via ${fetcher}.`);
    }
  }

  const manifest = {
    command: "scrape",
    target: targetUrl,
    repo_ref: repoRef,
    resolution_mode: resolutionMode,
    visited: [...visited],
    max_pages: maxPages,
    same_domain: sameDomain,
    match_pattern: matchPattern,
  };

  // Phase 2: Markdown conversion
  let phase2Result = null;
  let extractionMethod = "scrapling";
  let parallelFallbackReason = null;

  if (markdown && visited.size > 0) {
    if (parallel) {
      const obscuraPreflight = runObscuraPreflight(repoRoot, true);
      if (obscuraPreflight.ok && obscuraPreflight.workerOk) {
        try {
          const port = await findAvailablePort();
          const serveHandle = await startObscuraServe(obscuraPreflight.path, workers, port);
          const fetchResults = await concurrentFetch(serveHandle, [...visited], 15);
          stopObscuraServe(serveHandle);

          const prefetchedHtml = {};
          for (const r of fetchResults) {
            if (r.html) {
              prefetchedHtml[r.url] = r.html;
            }
          }

          phase2Result = convertTraversalToMarkdown(repoRoot, runDir, manifest, {
            fetcherFn: () => fetcherOverride || "get",
            concurrency,
            merge,
            cleanupHtml: !keepHtml,
            outputName: "scrape-output",
            prefetchedHtml,
          });
          extractionMethod = "obscura-serve-pool";
        } catch (err) {
          console.warn(`Obscura parallel fetch failed: ${err.message}. Falling back to Scrapling serial.`);
          parallelFallbackReason = err.message;
        }
      } else {
        console.warn("Obscura preflight failed or worker binary missing. Falling back to Scrapling serial.");
        parallelFallbackReason = "obscura_preflight_unavailable";
      }
    }

    if (!phase2Result) {
      phase2Result = convertTraversalToMarkdown(repoRoot, runDir, manifest, {
        fetcherFn: () => fetcherOverride || "get",
        concurrency,
        merge,
        cleanupHtml: !keepHtml,
        outputName: "scrape-output",
      });
    }

    manifest.phase2 = {
      successful_count: phase2Result.successful.length,
      failed_count: phase2Result.failed.length,
      failed_urls: phase2Result.failed.map((f) => f.url),
      merged_path: phase2Result.mergedPath,
    };
  }

  writeTextFile(manifestPath, JSON.stringify(manifest, null, 2));

  const artifacts = [absoluteArtifact(manifestPath, "disposable", "Scrape manifest")];

  if (markdown) {
    artifacts.push(...collectMarkdownArtifacts(runDir));
    // Ensure merged file gets a descriptive label if found by collectMarkdownArtifacts
    for (const { url } of (phase2Result?.failed ?? [])) {
      const idx = manifest.visited.indexOf(url);
      if (idx >= 0) {
        const errorPath = path.join(runDir, `${String(idx + 1).padStart(2, "0")}.md.error.log`);
        if (fs.existsSync(errorPath)) {
          artifacts.push(absoluteArtifact(errorPath, "disposable", `Conversion error for ${url}`));
        }
      }
    }
  } else {
    for (let i = 0; i < visited.size; i += 1) {
      const pageNum = String(i + 1).padStart(2, "0");
      const htmlPath = path.join(runDir, `${pageNum}.html`);
      if (fs.existsSync(htmlPath)) {
        artifacts.push(absoluteArtifact(htmlPath, "disposable", `Scraped page ${pageNum}`));
      }
    }
  }

  const traversalOk = visited.size > 0 && failures === 0;
  const conversionOk = !markdown || (phase2Result && phase2Result.failed.length === 0);
  const resultState =
    traversalOk && conversionOk ? "success" : visited.size > failures ? "partial_success" : "failure";

  if (emitReport) {
    const report = buildScrapeReport({
      targetUrl,
      repoRef,
      resolutionMode,
      events,
      result: resultState,
      phase2: markdown && phase2Result
        ? {
            successful: phase2Result.successful.length,
            failed: phase2Result.failed.length,
            mergedPath: phase2Result.mergedPath,
          }
        : null,
    });
    writeTextFile(reportPath, report);
    artifacts.unshift(absoluteArtifact(reportPath, "durable", "Scrape report"));
  }

  const summary =
    resultState === "success"
      ? `Scrape visited ${visited.size} page(s)${markdown ? ` and converted ${phase2Result.successful.length} to Markdown` : ""}.`
      : resultState === "partial_success"
        ? `Scrape visited ${visited.size} page(s)${markdown ? `; ${phase2Result.successful.length} converted, ${phase2Result.failed.length} failed` : ` with ${failures} fetch failure(s)`}.`
        : "Scrape failed before any page completed successfully.";

  const nextAction =
    resultState === "failure"
      ? "Review the scrape report, URL filters, or target availability before retrying."
      : "Inspect the scrape outputs. Adjust --match or --max-pages if more coverage is needed.";

  return makeResult("scrape", targetUrl, repoRef, summary, artifacts, nextAction, resultState, {
    workflow: "content_retrieval",
    engine_path: `scrapling_preflight:${preflight.status ?? "unknown"} -> scrape_traversal(${visited.size} pages)${markdown ? ` -> markdown_conversion(${phase2Result?.successful.length ?? 0}/${visited.size})` : ""}`,
    extraction_method: extractionMethod,
    ...(parallelFallbackReason ? { fallback_reason: parallelFallbackReason } : {}),
  });
}

function runBootstrapStrategy(repoRoot, repoRef, resolutionMode, targetUrl, fromDomain, profile, reportOverride) {
  const { registryPath, entries } = readRegistry(repoRoot);
  const refEntry = entries.find((e) => e.domain === fromDomain);
  if (!refEntry) {
    return makeResult(
      "bootstrap-strategy",
      targetUrl,
      repoRef,
      `No strategy exists for reference domain '${fromDomain}'.`,
      [],
      `Choose a valid --from domain that exists in sites/strategies/registry.json.`,
      "failure",
    );
  }

  const targetDomain = new URL(targetUrl).hostname;
  const existingEntry = entries.find(
    (e) => e.domain === targetDomain || targetDomain.endsWith(`.${e.domain}`),
  );
  if (existingEntry) {
    return makeResult(
      "bootstrap-strategy",
      targetUrl,
      repoRef,
      `A strategy already exists for '${targetDomain}'. Bootstrap would overwrite it.`,
      [absoluteArtifact(path.join(repoRoot, "sites", "strategies", existingEntry.file), "durable", "Existing strategy")],
      `Review the existing strategy or remove it before bootstrapping.`,
      "failure",
    );
  }

  const refStrategyPath = path.join(repoRoot, "sites", "strategies", refEntry.file);
  const refFrontmatter = readFrontmatter(refStrategyPath);
  const refRaw = fs.readFileSync(refStrategyPath, "utf8");

  const newFrontmatter = { ...refFrontmatter };
  const oldDomain = refFrontmatter.domain;
  newFrontmatter.domain = targetDomain;
  newFrontmatter.description = refFrontmatter.description.replace(oldDomain, targetDomain);

  if (newFrontmatter.structure?.pages) {
    for (const page of newFrontmatter.structure.pages) {
      if (page.url_example) {
        page.url_example = page.url_example.replace(oldDomain, targetDomain);
      }
    }
  }

  if (profile && newFrontmatter.extraction?.cleanup) {
    newFrontmatter.extraction.cleanup = [profile];
  }

  const sigPath = path.join(repoRoot, "configs", "backend-signatures.json");
  let matchingBackend = null;
  if (fs.existsSync(sigPath)) {
    const parsed = JSON.parse(fs.readFileSync(sigPath, "utf8"));
    const backends = parsed.backends ?? [];
    matchingBackend = backends.find((b) => b.reusable_strategies?.includes(fromDomain));
  }
  if (matchingBackend) {
    newFrontmatter.backend = matchingBackend.id;
  }

  const { date } = nowParts();
  const bodyLines = [
    `<!-- Bootstrapped from ${fromDomain} on ${date}; review recommended -->`,
    "",
    "## Overview",
    "",
    `\`${targetDomain}\` was bootstrapped from \`${fromDomain}\` as a shared-backend strategy. Review and validate all fields before production use.`,
    "",
    "## Page Structure",
    "",
    "*(Bootstrapped — copy the reference strategy's page structure narrative and adapt domain-specific details.)*",
    "",
    "## Extraction Flow",
    "",
    "*(Bootstrapped — copy the reference strategy's extraction flow and validate selectors.)*",
    "",
    "## Known Issues",
    "",
    "*(Bootstrapped — copy the reference strategy's known issues and add site-specific observations.)*",
    "",
    "## Evidence",
    "",
    `Bootstrapped from ${fromDomain} on ${date}; requires validation.`,
  ];
  const body = bodyLines.join("\n");

  const strategyDir = path.join(repoRoot, "sites", "strategies", targetDomain);
  const strategyPath = path.join(strategyDir, "strategy.md");
  const frontmatterYaml = YAML.stringify(newFrontmatter);
  const strategyContent = `---\n${frontmatterYaml}---\n${body}\n`;
  writeTextFile(strategyPath, strategyContent);

  const newEntry = {
    domain: targetDomain,
    description: newFrontmatter.description,
    protection_level: newFrontmatter.protection_level,
    page_types: [...new Set((newFrontmatter.structure?.pages ?? []).map((p) => p.type))],
    pagination: [...new Set((newFrontmatter.structure?.pages ?? []).map((p) => {
      if (typeof p.pagination === "object" && p.pagination !== null) {
        return p.pagination.mechanism;
      }
      return p.pagination ?? "none";
    }))],
    entry_points: newFrontmatter.structure?.entry_points ?? [],
    anti_crawl_refs: newFrontmatter.anti_crawl_refs ?? [],
    file: `${targetDomain}/strategy.md`,
    ...(newFrontmatter.backend ? { backend: newFrontmatter.backend } : {}),
  };
  entries.push(newEntry);
  fs.writeFileSync(registryPath, JSON.stringify({ entries }, null, 2), "utf8");

  const artifacts = [
    absoluteArtifact(strategyPath, "durable", "Bootstrapped strategy"),
    absoluteArtifact(registryPath, "durable", "Updated registry", "updated"),
  ];
  return makeResult(
    "bootstrap-strategy",
    targetUrl,
    repoRef,
    `Bootstrapped strategy for ${targetDomain} from ${fromDomain}.`,
    artifacts,
    `Review the generated strategy at ${strategyPath}, then run chrome-agent crawl ${targetUrl}.`,
    "success",
    {
      workflow: "strategy_authoring",
      engine_path: `bootstrap -> reference:${fromDomain} -> target:${targetDomain}`,
    },
  );
}

function runFreeze(repoRoot, repoRef, resolutionMode, scaffoldPath) {
  const absScaffoldPath = path.resolve(repoRoot, scaffoldPath);
  if (!fs.existsSync(absScaffoldPath)) {
    return makeResult(
      "freeze",
      scaffoldPath,
      repoRef,
      `Scaffold not found: ${absScaffoldPath}`,
      [],
      "Provide a valid path to a generated strategy.md scaffold.",
      "failure",
    );
  }

  const result = spawnSync("python3", [
    path.join(repoRoot, "scripts", "explore", "freeze.py"),
    repoRoot,
    absScaffoldPath,
  ], {
    cwd: repoRoot,
    encoding: "utf8",
  });

  if (result.status !== 0) {
    return makeResult(
      "freeze",
      scaffoldPath,
      repoRef,
      `Freeze failed: ${result.stderr.trim() || result.stdout.trim()}`,
      [],
      "Check that the scaffold has valid frontmatter and the repo structure is intact.",
      "failure",
    );
  }

  let parsed;
  try {
    parsed = JSON.parse(result.stdout);
  } catch {
    parsed = { stdout: result.stdout.trim() };
  }

  const artifacts = [
    absoluteArtifact(absScaffoldPath, "durable", "Frozen strategy"),
  ];
  if (parsed.report_path) {
    artifacts.push(absoluteArtifact(parsed.report_path, "durable", "Freeze report"));
  }

  return makeResult(
    "freeze",
    scaffoldPath,
    repoRef,
    `Strategy frozen for domain '${parsed.domain || "?"}'. Registry updated.`,
    artifacts,
    "none",
    "success",
    {
      workflow: "strategy_freeze",
      engine_path: `freeze -> scaffold:${path.basename(absScaffoldPath)}`,
    },
  );
}

function runIterate(repoRoot, repoRef, resolutionMode, scaffoldPath) {
  const absScaffoldPath = path.resolve(repoRoot, scaffoldPath);
  if (!fs.existsSync(absScaffoldPath)) {
    return makeResult(
      "iterate",
      scaffoldPath,
      repoRef,
      `Scaffold not found: ${absScaffoldPath}`,
      [],
      "Provide a valid path to a strategy.md file.",
      "failure",
    );
  }

  const result = spawnSync("python3", [
    path.join(repoRoot, "scripts", "explore", "iterate.py"),
    repoRoot,
    absScaffoldPath,
  ], {
    cwd: repoRoot,
    encoding: "utf8",
  });

  if (result.status !== 0) {
    return makeResult(
      "iterate",
      scaffoldPath,
      repoRef,
      `Iteration failed: ${result.stderr.trim() || result.stdout.trim()}`,
      [],
      "Check scaffold validity and re-run.",
      "failure",
    );
  }

  let parsed;
  try {
    parsed = JSON.parse(result.stdout);
  } catch {
    parsed = { stdout: result.stdout.trim() };
  }

  return makeResult(
    "iterate",
    scaffoldPath,
    repoRef,
    `Sample conversion re-run completed. ${parsed.success || 0}/${parsed.total || "?"} samples updated.`,
    [absoluteArtifact(absScaffoldPath, "durable", "Updated strategy")],
    "Review updated samples and run chrome-agent freeze <scaffold-path> when ready.",
    "success",
    {
      workflow: "strategy_iterate",
      engine_path: `iterate -> scaffold:${path.basename(absScaffoldPath)}`,
    },
  );
}

async function runBatch(repoRoot, repoRef, resolutionMode, urls, opts = {}) {
  const {
    workers = 5,
    timeout = 15,
    markdown = false,
    outputDir = null,
  } = opts;

  if (!urls || urls.length === 0) {
    return makeResult("batch", null, repoRef, "No URLs provided.", [], "Provide one or more URLs to batch fetch.", "failure");
  }

  const { runDir, reportPath } = buildRunPaths(repoRoot, "batch", urls[0]);
  const targetRunDir = outputDir ? path.resolve(outputDir) : runDir;
  ensureDir(targetRunDir);
  const manifestPath = path.join(targetRunDir, "manifest.json");

  // Try Obscura first
  const obscuraPreflight = runObscuraPreflight(repoRoot, true);
  let results = [];
  let extractionMethod = "scrapling";
  let fallbackReason = null;

  if (obscuraPreflight.ok && obscuraPreflight.workerOk) {
    try {
      const port = await findAvailablePort();
      const serveHandle = await startObscuraServe(obscuraPreflight.path, workers, port);
      const fetchResults = await concurrentFetch(serveHandle, urls, timeout);
      stopObscuraServe(serveHandle);

      for (let i = 0; i < fetchResults.length; i += 1) {
        const r = fetchResults[i];
        const htmlPath = path.join(targetRunDir, `${String(i + 1).padStart(2, "0")}.html`);
        if (r.html) {
          fs.writeFileSync(htmlPath, r.html, "utf8");
        }
        results.push({
          url: r.url,
          htmlPath: r.html ? htmlPath : null,
          elapsed_ms: r.elapsed_ms,
          error: r.error,
        });
      }
      extractionMethod = "obscura-serve-pool";
    } catch (err) {
      console.warn(`Obscura batch fetch failed: ${err.message}. Falling back to Scrapling serial.`);
      fallbackReason = err.message;
    }
  } else {
    console.warn("Obscura preflight failed. Falling back to Scrapling serial fetch.");
    fallbackReason = "obscura_preflight_unavailable";
  }

  // Fallback to Scrapling serial
  if (extractionMethod === "scrapling") {
    for (let i = 0; i < urls.length; i += 1) {
      const url = urls[i];
      const htmlPath = path.join(targetRunDir, `${String(i + 1).padStart(2, "0")}.html`);
      const start = Date.now();
      const fetchResult = runScraplingFetch(repoRoot, "get", url, htmlPath);
      const elapsed = Date.now() - start;
      if (fetchResult.ok) {
        results.push({ url, htmlPath, elapsed_ms: elapsed, error: null });
      } else {
        results.push({ url, htmlPath: null, elapsed_ms: elapsed, error: fetchResult.stderr || "fetch failed" });
      }
    }
  }

  // Optional Markdown conversion — use Scrapling --ai-targeted via file://, fallback to htmlToMarkdown
  if (markdown) {
    for (const r of results) {
      if (r.htmlPath && fs.existsSync(r.htmlPath)) {
        const html = fs.readFileSync(r.htmlPath, "utf8");
        const mdPath = r.htmlPath.replace(/\.html$/, ".md");
        const tmpHtmlPath = path.join(targetRunDir, `_tmp_md_${path.basename(r.htmlPath, ".html")}.html`);
        writeTextFile(tmpHtmlPath, html);
        const scraplingResult = runEngineFetch(repoRoot, "get", `file://${tmpHtmlPath}`, mdPath, ["--ai-targeted"]);
        fs.unlinkSync(tmpHtmlPath);
        if (!scraplingResult.ok) {
          // Fallback when Scrapling CLI is unavailable
          const md = htmlToMarkdown(html);
          writeTextFile(mdPath, md);
        }
      }
    }
  }

  const manifest = {
    command: "batch",
    urls,
    repo_ref: repoRef,
    extraction_method: extractionMethod,
    results: results.map((r) => ({ url: r.url, elapsed_ms: r.elapsed_ms, error: r.error })),
  };
  writeTextFile(manifestPath, JSON.stringify(manifest, null, 2));

  const artifacts = [absoluteArtifact(manifestPath, "disposable", "Batch manifest")];
  for (let i = 0; i < results.length; i += 1) {
    const r = results[i];
    if (r.htmlPath && fs.existsSync(r.htmlPath)) {
      artifacts.push(absoluteArtifact(r.htmlPath, "disposable", `Batch page ${String(i + 1).padStart(2, "0")}`));
    }
    if (markdown) {
      const mdPath = path.join(targetRunDir, `${String(i + 1).padStart(2, "0")}.md`);
      if (fs.existsSync(mdPath)) {
        artifacts.push(absoluteArtifact(mdPath, "disposable", `Batch markdown ${String(i + 1).padStart(2, "0")}`));
      }
    }
  }

  const successCount = results.filter((r) => !r.error).length;
  const failCount = results.length - successCount;
  const resultState = failCount === 0 ? "success" : successCount > 0 ? "partial_success" : "failure";
  const summary =
    resultState === "success"
      ? `Batch fetched ${successCount}/${results.length} URLs via ${extractionMethod}.`
      : `Batch fetched ${successCount}/${results.length} URLs via ${extractionMethod}; ${failCount} failed.`;

  return makeResult("batch", urls.join(", "), repoRef, summary, artifacts, "Inspect batch outputs in the run directory.", resultState, {
    workflow: "content_retrieval",
    engine_path: `batch -> ${extractionMethod}`,
    extraction_method: extractionMethod,
    ...(fallbackReason ? { fallback_reason: fallbackReason } : {}),
  });
}

const TRACKED_FILES_FOR_UPDATE = [
  "scripts/chrome-agent-runtime.mjs",
  "scripts/chrome-agent-cli.mjs",
  "skills/chrome-agent/SKILL.md",
];

function runGitFetchCheck(repoRoot) {
  const gitDir = path.join(repoRoot, ".git");
  if (!fs.existsSync(gitDir)) {
    return { ok: true, detail: "skipped: not a git repo", stale: false };
  }

  // git fetch origin main (timeout 10s)
  const fetchResult = spawnSync(
    "git",
    ["fetch", "origin", "main"],
    {
      cwd: repoRoot,
      encoding: "utf8",
      timeout: 10000,
      killSignal: "SIGTERM",
    },
  );

  if (fetchResult.error || fetchResult.status !== 0) {
    const reason = fetchResult.error?.code === "ETIMEDOUT" ? "timeout" : (fetchResult.stderr?.trim() || "unknown");
    return { ok: true, detail: `skipped: fetch failed (${reason})`, stale: false };
  }

  // Check detached HEAD
  const headBranch = spawnSync("git", ["symbolic-ref", "-q", "HEAD"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  if (headBranch.status !== 0) {
    return { ok: true, detail: "skipped: detached HEAD", stale: false };
  }

  // Compare HEAD vs origin/main
  const headRev = spawnSync("git", ["rev-parse", "HEAD"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  const mainRev = spawnSync("git", ["rev-parse", "origin/main"], {
    cwd: repoRoot,
    encoding: "utf8",
  });

  if (headRev.status !== 0 || mainRev.status !== 0) {
    return { ok: true, detail: "skipped: rev-parse failed", stale: false };
  }

  const headHash = headRev.stdout.trim();
  const mainHash = mainRev.stdout.trim();

  if (headHash === mainHash) {
    return { ok: true, detail: headHash, stale: false };
  }

  // Check if HEAD is behind (ancestor of) origin/main, not ahead
  const ancestorCheck = spawnSync("git", ["merge-base", "--is-ancestor", "HEAD", "origin/main"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  // exit 0 = HEAD is ancestor of origin/main => HEAD is behind or equal (equal already handled)
  // exit 1 = HEAD is NOT ancestor => HEAD is ahead or diverged
  if (ancestorCheck.status !== 0) {
    return { ok: true, detail: `ahead: HEAD ${headHash.slice(0, 8)} vs origin/main ${mainHash.slice(0, 8)}`, stale: false };
  }

  return { ok: false, detail: `behind: HEAD ${headHash.slice(0, 8)} vs origin/main ${mainHash.slice(0, 8)}`, stale: true, headHash, mainHash };
}

function runTrackedFilesCheck(repoRoot) {
  const diffResult = spawnSync(
    "git",
    ["diff", "--name-only", "HEAD", "origin/main"],
    {
      cwd: repoRoot,
      encoding: "utf8",
    },
  );

  if (diffResult.status !== 0) {
    return { ok: true, detail: "skipped: git diff failed", changedFiles: [] };
  }

  const changed = diffResult.stdout.trim().split("\n").filter(Boolean);
  const changedSet = new Set(changed);
  const trackedChanged = TRACKED_FILES_FOR_UPDATE.filter((f) => changedSet.has(f));

  if (trackedChanged.length === 0) {
    return { ok: true, detail: "behind but no tracked files changed", changedFiles: [] };
  }

  return { ok: false, detail: `tracked files changed: ${trackedChanged.join(", ")}`, changedFiles: trackedChanged };
}

function runAutoUpdateGlobalFiles(repoRoot, changedFiles) {
  const runtimeDir = process.env.CHROME_AGENT_RUNTIME_DIR || path.join(os.homedir(), ".agents", "scripts");
  const skillDir = path.join(os.homedir(), ".agents", "skills", "chrome-agent");
  const errors = [];

  try { ensureDir(runtimeDir); } catch (e) { errors.push(`mkdir ${runtimeDir}: ${e.message}`); }
  try { ensureDir(skillDir); } catch (e) { errors.push(`mkdir ${skillDir}: ${e.message}`); }

  if (errors.length > 0) {
    return { ok: false, detail: errors.join(";") };
  }

  if (changedFiles.includes("scripts/chrome-agent-runtime.mjs") || changedFiles.includes("scripts/chrome-agent-cli.mjs")) {
    const src = path.join(repoRoot, "scripts", "chrome-agent-runtime.mjs");
    const dst = path.join(runtimeDir, "chrome-agent.mjs");
    try {
      fs.copyFileSync(src, dst);
    } catch (e) {
      errors.push(`copy runtime: ${e.message}`);
    }
  }

  if (changedFiles.includes("skills/chrome-agent/SKILL.md")) {
    const src = path.join(repoRoot, "skills", "chrome-agent", "SKILL.md");
    const dst = path.join(skillDir, "SKILL.md");
    try {
      fs.copyFileSync(src, dst);
    } catch (e) {
      errors.push(`copy skill: ${e.message}`);
    }
  }

  // Write installed hash
  if (errors.length === 0) {
    const headRev = spawnSync("git", ["rev-parse", "HEAD"], {
      cwd: repoRoot,
      encoding: "utf8",
    });
    if (headRev.status === 0) {
      const hashPath = path.join(runtimeDir, ".chrome-agent-installed-hash");
      try {
        fs.writeFileSync(hashPath, `${headRev.stdout.trim()}
`, "utf8");
      } catch (e) {
        errors.push(`write hash: ${e.message}`);
      }
    }
  }

  if (errors.length > 0) {
    return { ok: false, detail: errors.join(";") };
  }
  return { ok: true, detail: "updated" };
}

function runEngineVersionCheck(repoRoot) {
  const scriptPath = path.join(repoRoot, "scripts", "engine-version-check.sh");
  if (!fs.existsSync(scriptPath)) {
    return { all_ok: true, engines: [] };
  }
  const result = spawnSync("bash", [scriptPath, "--json"], {
    cwd: repoRoot,
    encoding: "utf8",
    timeout: 30_000,
  });
  if (!result.stdout) {
    return { all_ok: true, engines: [] };
  }
  try {
    return JSON.parse(result.stdout);
  } catch {
    return { all_ok: true, engines: [] };
  }
}

function runDoctor(repoRoot, repoRef, resolutionMode) {
  const runtimeDir = process.env.CHROME_AGENT_RUNTIME_DIR || path.join(os.homedir(), ".agents", "scripts");
  const binDir = process.env.CHROME_AGENT_BIN_DIR || path.join(os.homedir(), ".local", "bin");
  const runtimePath = path.join(runtimeDir, "chrome-agent.mjs");
  const shimPath = path.join(binDir, "chrome-agent");
  const preflight = runScraplingPreflight(repoRoot, false);
  const obscuraPreflight = runObscuraPreflight(repoRoot, false);
  const envDefaultPath = process.env.CHROME_AGENT_REPO ? path.resolve(process.env.CHROME_AGENT_REPO) : null;
  const versionCheck = runEngineVersionCheck(repoRoot);

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
    { name: "obscura_preflight", ok: obscuraPreflight.ok, detail: obscuraPreflight.path ?? "unavailable" },
    { name: "obscura_worker", ok: obscuraPreflight.workerOk, detail: obscuraPreflight.path ? path.join(path.dirname(obscuraPreflight.path), "obscura-worker") : "unavailable" },
  ];

  // Repo freshness check
  const freshnessResult = runGitFetchCheck(repoRoot);
  checks.push({ name: "repo_freshness", ok: freshnessResult.ok, detail: freshnessResult.detail });

  // If stale, check tracked files and auto-update if needed
  const exploreDepsCheck = runExplorePythonDepsCheck(repoRoot);
  checks.push({ name: "explore_deps", ok: exploreDepsCheck.ok, detail: exploreDepsCheck.detail });

  let skillReloadRequired = false;
  if (freshnessResult.stale) {
    const trackedResult = runTrackedFilesCheck(repoRoot);
    if (trackedResult.changedFiles.length > 0) {
      const updateResult = runAutoUpdateGlobalFiles(repoRoot, trackedResult.changedFiles);
      checks.push({ name: "global_skill_updated", ok: updateResult.ok, detail: updateResult.detail });
      if (updateResult.ok) {
        skillReloadRequired = true;
      }
    } else {
      // Behind but no tracked files changed — override to ok
      const lastIdx = checks.length - 1;
      checks[lastIdx] = { name: "repo_freshness", ok: true, detail: trackedResult.detail };
    }
  }

  // Add version check results as doctor checks
  for (const ve of versionCheck.engines) {
    checks.push({
      name: `version_${ve.engine}`,
      ok: !ve.needs_update,
      detail: `${ve.engine}: ${ve.detected ?? "not installed"} (expected: ${ve.expected})`,
    });
  }

  const broken = checks.filter((check) => !check.ok);
  const resultState = broken.length === 0 ? "success" : preflight.ok || repoShapeIsValid(repoRoot) ? "partial_success" : "failure";

  let summary;
  let nextAction;
  if (broken.length === 0) {
    summary = `Launcher and repository prerequisites are healthy. ${resolutionSummary(repoRef, resolutionMode)}`;
    nextAction = "none";
  } else if (skillReloadRequired) {
    summary = `Doctor found ${broken.length} issue(s): ${broken.map((check) => check.name).join(", ")}. Global skill and runtime files have been auto-updated.`;
    nextAction = "Global skill and runtime files have been updated. Please reload the skill (restart the session or re-read the skill file), then retry your command.";
  } else {
    summary = `Doctor found ${broken.length} issue(s): ${broken.map((check) => check.name).join(", ")}.`;
    nextAction = "Install the global launcher, set CHROME_AGENT_REPO or supply an explicit --repo <path|repo://id>, and repair Scrapling CLI availability.";
  }

  return makeResult(
    "doctor",
    "runtime",
    repoRef,
    summary,
    checks.map((check) => ({
      path: check.detail,
      lifecycle: "durable",
      description: check.name,
      action: check.ok ? "checked" : "missing",
    })),
    nextAction,
    resultState,
    {
      checks,
      resolution_mode: resolutionMode,
      workflow: "runtime_support",
      engine_path: `doctor -> repo_resolution:${resolutionMode} -> scrapling_preflight:${preflight.status ?? "unavailable"}`,
      version_check: versionCheck,
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

async function main() {
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
        result = await runCrawl(repoRoot, repoRef, resolutionMode, parsed.target, {
          entryPoint: parsed.entryPoint,
          maxPages: parsed.maxPages,
          report: parsed.report,
          markdown: parsed.markdown,
          merge: parsed.merge,
          concurrency: parsed.concurrency,
          keepHtml: parsed.keepHtml,
          parallel: parsed.parallel,
          workers: parsed.workers,
          discoveryOnly: parsed.discoveryOnly,
          fromManifest: parsed.fromManifest,
          phase: parsed.phase,
          reFetch: parsed.reFetch,
          yes: parsed.yes,
          excludeCategory: parsed.excludeCategory,
          outputDir: parsed.outputDir,
        });
        break;
      case "scrape":
        if (!parsed.target) {
          throw new Error("scrape requires a target URL.");
        }
        result = await runScrape(repoRoot, repoRef, resolutionMode, parsed.target, {
          maxPages: parsed.maxPages,
          sameDomain: parsed.sameDomain,
          matchPattern: parsed.matchPattern,
          markdown: parsed.markdown,
          merge: parsed.merge,
          concurrency: parsed.concurrency,
          fetcherOverride: parsed.fetcherOverride,
          keepHtml: parsed.keepHtml,
          reportOverride: parsed.report,
          parallel: parsed.parallel,
          workers: parsed.workers,
        });
        break;
      case "batch": {
        const batchUrls = parsed.positionals.slice(1);
        if (batchUrls.length === 0) {
          throw new Error("batch requires one or more target URLs.");
        }
        result = await runBatch(repoRoot, repoRef, resolutionMode, batchUrls, {
          workers: parsed.workers,
          timeout: parsed.concurrency || 15,
          markdown: parsed.markdown,
          outputDir: null,
        });
        break;
      }
      case "bootstrap-strategy":
        if (!parsed.target) {
          throw new Error("bootstrap-strategy requires a target URL.");
        }
        if (!parsed.fromDomain) {
          throw new Error("bootstrap-strategy requires --from <domain>.");
        }
        result = runBootstrapStrategy(repoRoot, repoRef, resolutionMode, parsed.target, parsed.fromDomain, parsed.profile, parsed.report);
        break;
      case "freeze":
        if (!parsed.target) {
          throw new Error("freeze requires a scaffold path.");
        }
        result = runFreeze(repoRoot, repoRef, resolutionMode, parsed.target);
        break;
      case "iterate":
        if (!parsed.target) {
          throw new Error("iterate requires a scaffold path.");
        }
        result = runIterate(repoRoot, repoRef, resolutionMode, parsed.target);
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

await main();
