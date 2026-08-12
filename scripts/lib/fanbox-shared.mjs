/** Shared helpers for the fanbox NFO generator scripts.
 *
 * Extracted from fanbox-generate-nfo.mjs / fanbox-generate-nfo-external.mjs.
 * Stateless: CDP path / target / cookie are passed per call so neither
 * script's module-level state leaks into the shared layer.
 */

import { execSync } from "child_process";

export function sh(cmd, timeout = 30000) {
  return execSync(cmd, { timeout }).toString().trim();
}

export function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export function findTarget(cdpPath) {
  const list = sh(`node "${cdpPath}" list`);
  for (const line of list.split("\n")) {
    if (line.includes("fanbox.cc")) return line.split(/\s+/)[0];
  }
  throw new Error("No fanbox.cc tab found.");
}

export function cdpEval(cdpPath, target, expr) {
  return sh(`node "${cdpPath}" eval ${target} '${expr.replace(/'/g, "'\\''")}'`);
}

export function cdpNav(cdpPath, target, url) {
  sh(`node "${cdpPath}" nav ${target} '${url.replace(/'/g, "'\\''")}'`);
}

export function escapeXml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function extractChineseText(bodyText) {
  if (!bodyText) return null;
  const blocks = bodyText.split(/\n\n+/);
  for (const block of blocks) {
    const zhChars = [...block].filter((c) => c.charCodeAt(0) >= 0x4e00 && c.charCodeAt(0) <= 0x9fff).length;
    const totalChars = [...block].filter((c) => c.trim()).length;
    if (totalChars > 0 && zhChars / totalChars > 0.3 && block.trim().length >= 30) {
      return block.trim();
    }
  }
  return null;
}

export function extractActorNames(title, candidates) {
  const names = [];
  for (const name of candidates) {
    if (title.toUpperCase().includes(name)) {
      if (!names.includes(name)) names.push(name);
    }
  }
  if (names.length === 0) names.push("ATD");
  return names;
}

export function downloadCover(url, destPath, cookie) {
  const escapedPath = destPath.replace(/'/g, "'\\''");
  try {
    return sh(`curl -L -s -o '${escapedPath}' -w '%{http_code}' -H 'Cookie: ${cookie}' -H 'Referer: https://www.fanbox.cc/' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' '${url}'`, 30000);
  } catch {
    return "0";
  }
}

export function generateNfo(data) {
  const dateadded = new Date().toISOString().replace("T", " ").slice(0, 19);
  const actorXml = data.actors.map((name) => `  <actor>\n    <name>${escapeXml(name)}</name>\n    <type>Actor</type>\n  </actor>`).join("\n");
  return `<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<movie>
  <plot><![CDATA[${escapeXml(data.plot)}]]></plot>
  <outline />
  <lockdata>false</lockdata>
  <lockedfields>Name|OriginalTitle|SortName|Overview|Genres|Cast|Studios</lockedfields>
  <dateadded>${dateadded}</dateadded>
  <title>${escapeXml(data.title)}</title>
${actorXml}
  <year>${data.date.slice(0, 4)}</year>
  <sorttitle>${escapeXml(data.sorttitle)}</sorttitle>
  <premiered>${data.date.slice(0, 10)}</premiered>
  <releasedate>${data.date.slice(0, 10)}</releasedate>
  <studio>ATD</studio>
</movie>`;
}
