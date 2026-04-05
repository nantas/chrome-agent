#!/usr/bin/env node

import { execSync } from "child_process";
import { existsSync, writeFileSync, readFileSync, readdirSync } from "fs";
import { resolve, dirname, basename, join, extname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CDP = resolve(__dirname, "..", ".agents", "skills", "chrome-cdp", "scripts", "cdp.mjs");
const BASE_DIR = "/Volumes/video/学习资料/Anime/ATD";
const DETAIL_API = "https://api.fanbox.cc/post.info";
const PROGRESS_FILE = resolve(__dirname, "fanbox-nfo-external-progress.json");
const TODAY = new Date().toISOString().replace("T", " ").slice(0, 19);
const API_DELAY_MS = 4000;
const RATE_LIMIT_COOLDOWN_MS = 3 * 60 * 60 * 1000;
const START_PAGE = 1;
const CREATOR_ID = "atdfb";

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

function cdpNav(url) {
  sh(`node "${CDP}" nav ${TARGET} '${url.replace(/'/g, "'\\''")}'`);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function escapeXml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function norm(s) {
  return s.normalize("NFKC").toLowerCase()
    .replace(/[\s\-_.~()（）【】\[\]＆&+''\u2019\uFF07]+/g, " ")
    .replace(/\s+/g, " ").trim();
}

function stripVideoSuffixes(s) {
  let n = norm(s);
  const suffixes = [
    /\bmoz\.?$/, /\bmoza\.?$/, /\bmozkai\.?$/, /\bkai\.?$/,
    /\bhd\d*$/, /\bfhd$/, /\bhigh$/, /\bbeta\d*$/,
    /\buncensored\.?$/, /\buncensord\.?$/, /\bfree$/,
    /\bpart\d+$/, /\bscene\d+\w*$/,
    /\bpg\d+$/, /\b\d+p\d+$/,
  ];
  for (const r of suffixes) n = n.replace(r, "");
  return n.replace(/\s+/g, " ").trim();
}

function scanVideoFiles() {
  const videos = [];
  function scanDir(dir, depth) {
    if (depth > 5) return;
    let entries;
    try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      const full = join(dir, e.name);
      if (e.isDirectory()) {
        if (depth === 0 && e.name === "Fanbox") continue;
        scanDir(full, depth + 1);
      } else if (/\.(mp4|mkv|avi|wmv|mov|webm)$/i.test(e.name)) {
        const name = basename(e.name, extname(e.name));
        videos.push({ path: full, name, norm: norm(name), stripped: stripVideoSuffixes(name) });
      }
    }
  }
  scanDir(BASE_DIR, 0);
  return videos;
}

function findMatch(fbFileName, videos, usedPaths) {
  const fbName = basename(fbFileName, extname(fbFileName));
  const fbNorm = norm(fbName);
  const fbStripped = stripVideoSuffixes(fbName);

  let m = videos.find(v => !usedPaths.has(v.path) && v.norm === fbNorm);
  if (m) return m;

  m = videos.find(v => !usedPaths.has(v.path) && v.stripped === fbStripped && fbStripped.length >= 8);
  if (m) return m;

  m = videos.find(v => {
    if (usedPaths.has(v.path)) return false;
    if (fbNorm.length < 8 || v.norm.length < 8) return false;
    return v.norm.includes(fbNorm) || fbNorm.includes(v.norm);
  });
  if (m) return m;

  m = videos.find(v => {
    if (usedPaths.has(v.path)) return false;
    if (fbStripped.length < 8 || v.stripped.length < 8) return false;
    return v.stripped.includes(fbStripped) || fbStripped.includes(v.stripped);
  });
  if (m) return m;

  return null;
}

function extractChineseText(bodyText) {
  if (!bodyText) return null;
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
  const candidates = ["ULALA", "HINA", "SUIREN", "FROST", "ALICE", "CHRIS", "MOCA", "BUNNY", "PALADIN", "BIOSEEKER", "PHI", "BIO"];
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
    const d=await r.json();const p=d.body;
    const files=[];
    if(p.body&&p.body.files){
      p.body.files.forEach(f=>{
        const ext=f.extension||"";
        if(/\.(mp4|mkv|avi|wmv|mov|webm)$/i.test("."+ext)) files.push(f.name+"."+ext);
      });
    }
    return JSON.stringify({
      title:p.title,
      date:p.publishedDatetime,
      coverUrl:p.coverImageUrl||"",
      bodyText:p.body?p.body.text||"":""
      ,files:files
    });
  })()`;
  return JSON.parse(cdpEval(expr));
}

async function fetchWithRetry(postId, maxRetries = 2) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const detail = fetchPostDetail(postId);
      if (detail.error) {
        console.log(`HTTP ${detail.status}, retry ${attempt}/${maxRetries}...`);
        await sleep(5000 * attempt);
        continue;
      }
      return detail;
    } catch (err) {
      const msg = err.message || "";
      if (msg.includes("Failed to fetch")) return "RATE_LIMITED";
      console.log(`ERR ${attempt}: ${msg.slice(0, 60)}`);
      if (attempt < maxRetries) {
        try { TARGET = findTarget(); } catch {}
        await sleep(5000 * attempt);
      }
    }
  }
  return null;
}

function downloadCover(url, destPath) {
  const cookie = "FANBOXSESSID=3391520_YwKSEowRvq7OztoTheOkT5AeqkA4UiNs; p_ab_id=0; p_ab_id_2=7; p_ab_d_id=1522472693";
  const ep = destPath.replace(/'/g, "'\\''");
  try {
    return sh(`curl -L -s -o '${ep}' -w '%{http_code}' -H 'Cookie: ${cookie}' -H 'Referer: https://www.fanbox.cc/' -H 'User-Agent: Mozilla/5.0' '${url}'`, 30000);
  } catch { return "0"; }
}

function generateNfo(data) {
  const actorXml = data.actors.map(n => `  <actor>\n    <name>${escapeXml(n)}</name>\n    <type>Actor</type>\n  </actor>`).join("\n");
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

function loadProgress() {
  try { return JSON.parse(readFileSync(PROGRESS_FILE, "utf8")); }
  catch { return { processedPosts: [], matchedFiles: [], rateLimitEvents: [] }; }
}

function saveProgress(p) { writeFileSync(PROGRESS_FILE, JSON.stringify(p, null, 2), "utf8"); }

async function main() {
  console.log("=== FANBOX External NFO Generator ===");
  console.log(`Base: ${BASE_DIR}`);
  console.log(`Start page: ${START_PAGE}\n`);

  const videos = scanVideoFiles();
  console.log(`Videos found: ${videos.length}\n`);

  const progress = loadProgress();
  const usedPaths = new Set(progress.matchedFiles || []);

  TARGET = findTarget();
  console.log(`Tab: ${TARGET}\n`);

  let page = START_PAGE;
  let generated = 0, skipped = 0, failed = 0;
  let noMatchPages = 0;

  while (true) {
    const url = `https://www.fanbox.cc/@${CREATOR_ID}/posts?page=${page}&sort=newest`;
    console.log(`\n=== Page ${page} ===`);

    try {
      cdpNav(url);
      await sleep(5000);
      TARGET = findTarget();
    } catch (err) {
      console.log(`Nav error: ${err.message.slice(0, 80)}`);
      break;
    }

    let postIds;
    let extractRetries = 0;
    while (true) {
      try {
        const json = cdpEval(`(()=>{
          const ids=new Set();
          document.querySelectorAll('a[href*="/@${CREATOR_ID}/posts/"]').forEach(a=>{
            const m=a.href.match(/@${CREATOR_ID}\\/posts\\/(\\d+)/);
            if(m) ids.add(m[1]);
          });
          return JSON.stringify([...ids].sort((a,b)=>parseInt(b)-parseInt(a)));
        })()`);
        postIds = JSON.parse(json);
        if (postIds.length > 0) break;
      } catch (err) {
        extractRetries++;
        if (extractRetries > 3) {
          console.log(`ID extract failed after 3 retries`);
          postIds = [];
          break;
        }
        await sleep(3000);
        try { TARGET = findTarget(); } catch {}
      }
    }

    if (postIds.length === 0) {
      console.log("No posts found. Done.");
      break;
    }

    console.log(`Posts: ${postIds.length}`);
    let pageMatched = 0;
    let pageVideosChecked = 0;

    for (const postId of postIds) {
      if (progress.processedPosts.includes(postId)) continue;

      let detail;
      while (true) {
        process.stdout.write(`  ${postId} ... `);
        detail = await fetchWithRetry(postId);

        if (detail === "RATE_LIMITED") {
          const now = new Date().toISOString();
          console.log(`RATE LIMITED at ${now}`);
          progress.rateLimitEvents.push({ time: now, page, postId });
          saveProgress(progress);
          const waitMin = Math.round(RATE_LIMIT_COOLDOWN_MS / 60000);
          console.log(`Waiting ${waitMin} min (${new Date(Date.now() + RATE_LIMIT_COOLDOWN_MS).toISOString()} resume)...`);
          await sleep(RATE_LIMIT_COOLDOWN_MS);
          console.log("Cooldown done, reconnecting...");
          try { TARGET = findTarget(); } catch (err) {
            console.log(`Reconnect failed: ${err.message}`);
            saveProgress(progress);
            process.exit(1);
          }
          continue;
        }

        if (!detail) {
          console.log("FAIL");
          failed++;
          progress.processedPosts.push(postId);
          saveProgress(progress);
          await sleep(API_DELAY_MS);
          break;
        }
        break;
      }

      if (!detail) continue;

      progress.processedPosts.push(postId);
      const videoFiles = detail.files || [];

      if (videoFiles.length === 0) {
        console.log("no videos");
        skipped++;
        saveProgress(progress);
        await sleep(API_DELAY_MS);
        continue;
      }

      pageVideosChecked++;
      const plot = extractChineseText(detail.bodyText) || detail.bodyText.split(/\n/).filter(l => l.trim().length > 10).join("\n\n").slice(0, 500);
      const actors = extractActorNames(detail.title);
      let matched = 0;
      let firstMatchPath = null;

      for (const fbFile of videoFiles) {
        const local = findMatch(fbFile, videos, usedPaths);
        if (!local) continue;

        const nfoPath = local.path.replace(/\.[^.]+$/, ".nfo");
        writeFileSync(nfoPath, generateNfo({
          title: local.name,
          sorttitle: local.name,
          plot, date: detail.date, actors,
        }), "utf8");

        usedPaths.add(local.path);
        progress.matchedFiles.push(local.path);
        if (!firstMatchPath) firstMatchPath = local.path;
        matched++;
        generated++;
        process.stdout.write(`[${basename(local.path)}] `);
      }

      if (matched === 0) {
        console.log(`no match (${videoFiles.length} videos)`);
      } else {
        console.log(`OK (${matched})`);
        pageMatched += matched;
      }

      if (detail.coverUrl && firstMatchPath) {
        const coverPath = firstMatchPath.replace(/\.[^.]+$/, "-poster.jpg");
        if (!existsSync(coverPath)) {
          process.stdout.write("  [cover] ");
          const code = downloadCover(detail.coverUrl, coverPath);
          if (code !== "200") {
            downloadCover(detail.coverUrl, coverPath.replace(/\.jpg$/, ".png"));
          }
          console.log("");
        }
      }

      saveProgress(progress);
      await sleep(API_DELAY_MS);
    }

    if (pageVideosChecked > 0 && pageMatched === 0) {
      noMatchPages++;
      console.log(`  (no match page, streak: ${noMatchPages})`);
      if (noMatchPages >= 5) {
        console.log(`\n${noMatchPages} consecutive pages with videos but no matches. Stopping.`);
        break;
      }
    } else {
      noMatchPages = 0;
    }

    page++;
  }

  console.log(`\n=== Results ===`);
  console.log(`Generated/Updated: ${generated}`);
  console.log(`Skipped (no videos): ${skipped}`);
  console.log(`Failed: ${failed}`);
  if (progress.rateLimitEvents.length > 0) {
    console.log(`Rate limit events: ${progress.rateLimitEvents.length}`);
    progress.rateLimitEvents.forEach(e => console.log(`  ${e.time} (page ${e.page}, post ${e.postId})`));
  }

  const remaining = videos.filter(v => !usedPaths.has(v.path));
  if (remaining.length > 0) {
    console.log(`\nUnmatched (${remaining.length}):`);
    remaining.forEach(v => console.log(`  ${v.path}`));
  }

  saveProgress(progress);
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1); });
