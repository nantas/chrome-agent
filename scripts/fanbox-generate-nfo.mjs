#!/usr/bin/env node

import { execSync } from "child_process";
import { mkdirSync, existsSync, statSync, writeFileSync, readFileSync } from "fs";
import { resolve, dirname, basename } from "path";
import { fileURLToPath } from "url";
import { sh, sleep, findTarget, cdpEval, escapeXml, extractChineseText, extractActorNames, downloadCover, generateNfo } from "./lib/fanbox-shared.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CDP = resolve(__dirname, "..", ".agents", "skills", "chrome-cdp", "scripts", "cdp.mjs");
const BASE_DIR = process.env.FANBOX_BASE_DIR ?? "/Volumes/video/学习资料/Anime/ATD/Fanbox";
const DETAIL_API = "https://api.fanbox.cc/post.info";
const ACTOR_CANDIDATES = ["ULALA", "HINA", "SUIREN", "FROST", "ALICE"];
const PROGRESS_FILE = resolve(__dirname, "fanbox-download-progress.json");

const FANBOX_COOKIE = process.env.FANBOX_COOKIE || "";
if (!FANBOX_COOKIE) {
  console.error("Error: FANBOX_COOKIE env var not set (expected 'FANBOXSESSID=...; p_ab_id=...; ...')");
  process.exit(1);
}

let TARGET = null;

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
  return JSON.parse(cdpEval(CDP, TARGET, expr));
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
        TARGET = findTarget(CDP);
        await sleep(5000 * attempt);
      }
    }
  }
  return null;
}

async function main() {
  console.log("=== FANBOX NFO Generator ===");
  console.log(`Base dir: ${BASE_DIR}\n`);

  TARGET = findTarget(CDP);
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
    const actors = extractActorNames(detail.title, ACTOR_CANDIDATES);

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
        const code = downloadCover(detail.coverUrl, coverPath, FANBOX_COOKIE);
        if (code !== "200") {
          const coverPathPng = coverPath.replace(/\.jpg$/, ".png");
          downloadCover(detail.coverUrl, coverPathPng, FANBOX_COOKIE);
        }
      }
    }

    console.log(`OK (${mp4Files.length} nfo)`);
    await sleep(3000);
  }

  console.log(`\n=== Done === Generated:${generated} Skipped:${skipped} Failed:${failed}`);
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1); });
