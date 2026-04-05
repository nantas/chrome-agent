#!/usr/bin/env node

import { execSync } from "child_process";
import { mkdirSync, existsSync, statSync, writeFileSync, readFileSync } from "fs";
import { resolve, dirname, basename } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CDP = resolve(__dirname, "..", ".agents", "skills", "chrome-cdp", "scripts", "cdp.mjs");
const BASE_DIR = "/Volumes/video/学习资料/Anime/ATD/Fanbox";
const DETAIL_API = "https://api.fanbox.cc/post.info";
const PROGRESS_FILE = resolve(__dirname, "fanbox-download-progress.json");
const TODAY = new Date().toISOString().replace("T", " ").slice(0, 19);

let TARGET = null;

function sh(cmd, timeout = 30000) {
  return execSync(cmd, { timeout }).toString().trim();
}

function findTarget() {
  const list = sh(`node "${CDP}" list`);
  for (const line of list.split("\n")) {
    if (line.includes("fanbox.cc")) return line.split(/\s+/)[0];
  }
  throw new Error("No fanbox.cc tab found.");
}

function cdpEval(expr) {
  return sh(`node "${CDP}" eval ${TARGET} '${expr.replace(/'/g, "'\\''")}'`);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function escapeXml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function extractChineseText(bodyText) {
  const blocks = bodyText.split(/\n\n+/);
  for (const block of blocks) {
    const zhChars = [...block].filter(c => c.charCodeAt(0) >= 0x4e00 && c.charCodeAt(0) <= 0x9fff).length;
    const totalChars = [...block].filter(c => c.trim()).length;
    if (totalChars > 0 && zhChars / totalChars > 0.3 && block.trim().length >= 30) {
      return block.trim();
    }
  }
  return null;
}

function extractActorNames(title) {
  const names = [];
  const candidates = ["ULALA", "HINA", "SUIREN", "FROST", "ALICE"];
  for (const name of candidates) {
    if (title.toUpperCase().includes(name)) {
      if (!names.includes(name)) names.push(name);
    }
  }
  if (names.length === 0) names.push("ATD");
  return names;
}

function fetchPostDetail(postId) {
  const expr = `(async()=>{
    const r=await fetch("${DETAIL_API}?postId=${postId}",{credentials:"include"});
    if(!r.ok) return JSON.stringify({error:true,status:r.status});
    const d=await r.json();const post=d.body;
    return JSON.stringify({
      title:post.title,
      date:post.publishedDatetime,
      coverUrl:post.coverImageUrl||"",
      bodyText:post.body?post.body.text||"":""
    });
  })()`;
  return JSON.parse(cdpEval(expr));
}

async function fetchWithRetry(postId, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const detail = fetchPostDetail(postId);
      if (detail.error) {
        const waitMs = 5000 * attempt;
        console.log(`HTTP ${detail.status}, retry ${attempt}/${maxRetries} (wait ${waitMs}ms)...`);
        await sleep(waitMs);
        continue;
      }
      return detail;
    } catch (err) {
      console.log(`ERR attempt ${attempt}: ${err.message.slice(0, 60)}`);
      if (attempt < maxRetries) {
        TARGET = findTarget();
        await sleep(5000 * attempt);
      }
    }
  }
  return null;
}

function downloadCover(url, destPath) {
  const cookie = "FANBOXSESSID=3391520_YwKSEowRvq7OztoTheOkT5AeqkA4UiNs; p_ab_id=0; p_ab_id_2=7; p_ab_d_id=1522472693";
  const escapedPath = destPath.replace(/'/g, "'\\''");
  const cmd = `curl -L -s -o '${escapedPath}' -w '%{http_code}' -H 'Cookie: ${cookie}' -H 'Referer: https://www.fanbox.cc/' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' '${url}'`;
  return sh(cmd, 30000);
}

function generateNfo(data) {
  const actorXml = data.actors.map(name => `  <actor>\n    <name>${escapeXml(name)}</name>\n    <type>Actor</type>\n  </actor>`).join("\n");
  return `<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<movie>
  <plot><![CDATA[${escapeXml(data.plot)}]]></plot>
  <outline />
  <lockdata>false</lockdata>
  <lockedfields>Name|OriginalTitle|SortName|Overview|Genres|Cast|Studios</lockedfields>
  <dateadded>${TODAY}</dateadded>
  <title>${escapeXml(data.title)}</title>
${actorXml}
  <year>${data.date.slice(0, 4)}</year>
  <sorttitle>${escapeXml(data.sorttitle)}</sorttitle>
  <premiered>${data.date.slice(0, 10)}</premiered>
  <releasedate>${data.date.slice(0, 10)}</releasedate>
  <studio>ATD</studio>
</movie>`;
}

async function main() {
  console.log("=== FANBOX NFO Generator ===");
  console.log(`Base dir: ${BASE_DIR}\n`);

  TARGET = findTarget();
  console.log(`Tab: ${TARGET}\n`);

  const completed = new Set(JSON.parse(readFileSync(PROGRESS_FILE, "utf8")).completed || []);
  const postIds = [...completed].sort((a, b) => parseInt(b) - parseInt(a));

  let generated = 0, skipped = 0, failed = 0;

  for (const postId of postIds) {
    process.stdout.write(`  Post ${postId} ... `);

    const detail = await fetchWithRetry(postId);
    if (!detail) {
      console.log("FAILED after retries");
      failed++;
      continue;
    }

    const date = detail.date;
    const md = `${date.slice(0, 4)}-${date.slice(5, 7)}`;
    const dir = `${BASE_DIR}/${md}`;
    if (!existsSync(dir)) { console.log("no dir"); skipped++; continue; }

    const mp4Files = [];
    try {
      const entries = execSync(`ls "${dir}"/*.mp4 2>/dev/null`, { shell: true, encoding: "utf-8" }).toString().trim().split("\n").filter(Boolean);
      for (const e of entries) mp4Files.push(basename(e, ".mp4"));
    } catch {
      console.log("no mp4"); skipped++; continue;
    }

    if (mp4Files.length === 0) { console.log("no mp4"); skipped++; continue; }

    const plot = extractChineseText(detail.bodyText) || detail.bodyText.split(/\n/).filter(l => l.trim().length > 10).join("\n\n").slice(0, 500);
    const actors = extractActorNames(detail.title);

    for (const mp4Name of mp4Files) {
      const nfoPath = `${dir}/${mp4Name}.nfo`;
      if (existsSync(nfoPath)) { skipped++; continue; }

      const nfoData = {
        title: mp4Name,
        sorttitle: mp4Name,
        plot: plot,
        date: date,
        actors: actors,
      };

      writeFileSync(nfoPath, generateNfo(nfoData), "utf8");
      generated++;
    }

    if (detail.coverUrl) {
      const coverPath = `${dir}/${mp4Files[0].replace(/\.mp4$/, "")}-poster.jpg`;
      if (!existsSync(coverPath)) {
        process.stdout.write("[cover] ");
        const code = downloadCover(detail.coverUrl, coverPath);
        if (code !== "200") {
          const coverPathPng = coverPath.replace(/\.jpg$/, ".png");
          downloadCover(detail.coverUrl, coverPathPng);
        }
      }
    }

    console.log(`OK (${mp4Files.length} nfo)`);
    await sleep(3000);
  }

  console.log(`\n=== Done === Generated:${generated} Skipped:${skipped} Failed:${failed}`);
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1); });
