#!/usr/bin/env node

import { execSync } from "child_process";
import { mkdirSync, existsSync, statSync, writeFileSync, readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CDP = resolve(__dirname, "..", ".agents", "skills", "chrome-cdp", "scripts", "cdp.mjs");
const CREATOR_ID = "atdfb";
const BASE_DIR = "/Volumes/Shuttle/downloads";
const DETAIL_API = "https://api.fanbox.cc/post.info";
const CUTOFF_DATE = new Date("2021-06-01T00:00:00+09:00");
const PROGRESS_FILE = resolve(__dirname, "fanbox-download-progress.json");
const VIDEO_EXTS = ["mp4", "wmv", "avi", "mov", "mkv", "webm", "mpg", "mpeg"];
const MAX_PAGES = 10;

let TARGET = null;

function sh(cmd, timeout = 30000) {
  return execSync(cmd, { timeout }).toString().trim();
}

function findTarget() {
  const list = sh(`node "${CDP}" list`);
  for (const line of list.split("\n")) {
    if (line.includes("fanbox.cc")) return line.split(/\s+/)[0];
  }
  throw new Error("No fanbox.cc tab found. Open a FANBOX page in Chrome.");
}

function cdpEval(expr) {
  return sh(`node "${CDP}" eval ${TARGET} '${expr.replace(/'/g, "'\\''")}'`);
}

function cdpNav(url) {
  sh(`node "${CDP}" nav ${TARGET} "${url}"`, 15000);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function fmtSize(b) {
  if (b < 1048576) return (b / 1024).toFixed(1) + "KB";
  if (b < 1073741824) return (b / 1048576).toFixed(1) + "MB";
  return (b / 1073741824).toFixed(2) + "GB";
}

function monthDir(dateStr) {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function loadProgress() {
  try {
    return new Set(JSON.parse(readFileSync(PROGRESS_FILE, "utf8")).completed || []);
  } catch { return new Set(); }
}

function saveProgress(completed) {
  writeFileSync(PROGRESS_FILE, JSON.stringify({ completed: [...completed], updated: new Date().toISOString() }, null, 2));
}

function getPostIdsFromPage() {
  const raw = cdpEval(`(() => {
    const ids = new Set();
    document.querySelectorAll("a").forEach(a => {
      if (a.href && a.href.includes("/@atdfb/posts/")) {
        const parts = a.href.split("/@atdfb/posts/");
        if (parts.length > 1) ids.add(parts[1].split(/[?#]/)[0]);
      }
    });
    return JSON.stringify([...ids]);
  })()`);
  return JSON.parse(raw);
}

function fetchDetail(postId) {
  const raw = cdpEval(`(async()=>{
    const r=await fetch("${DETAIL_API}?postId=${postId}",{credentials:"include"});
    const d=await r.json();const post=d.body;const pt=post.type;const body=post.body;const videos=[];
    if(pt==="file"&&body.files){for(const f of body.files){if(${JSON.stringify(VIDEO_EXTS)}.includes(f.extension)){videos.push({name:f.name,ext:f.extension,size:f.size,url:f.url});}}}
    else if(pt==="article"&&body.blocks){const fm={};if(body.files){for(const f of body.files)fm[f.fileId]=f;}for(const b of body.blocks){if(b.type==="file"&&fm[b.fileId]){const f=fm[b.fileId];if(${JSON.stringify(VIDEO_EXTS)}.includes(f.extension)){videos.push({name:f.name,ext:f.extension,size:f.size,url:f.url});}}}}
    return JSON.stringify({title:post.title,date:post.publishedDatetime,videos:videos});
  })()`);
  return JSON.parse(raw);
}

function downloadVideo(url, destPath) {
  const cookie = "FANBOXSESSID=3391520_YwKSEowRvq7OztoTheOkT5AeqkA4UiNs; p_ab_id=0; p_ab_id_2=7; p_ab_d_id=1522472693";
  const cmd = `curl -L -s -o "${destPath}" -w "%{http_code}" -H "Cookie: ${cookie}" -H "Referer: https://www.fanbox.cc/" -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" "${url}"`;
  return sh(cmd, 600000);
}

async function main() {
  console.log("=== FANBOX Video Downloader ===");
  console.log(`Creator: ${CREATOR_ID} | Output: ${BASE_DIR} | Cutoff: 2021-06\n`);

  TARGET = findTarget();
  console.log(`Tab: ${TARGET}`);

  const completed = loadProgress();
  if (completed.size > 0) console.log(`Resuming: ${completed.size} posts already done\n`);

  // Phase 1: collect all post IDs via page navigation
  console.log("Phase 1: Collecting post IDs...");
  const allIds = [];
  const seen = new Set();

  for (let page = 1; page <= MAX_PAGES; page++) {
    const url = page === 1
      ? `https://www.fanbox.cc/@atdfb/posts`
      : `https://www.fanbox.cc/@atdfb/posts?page=${page}&sort=newest`;

    process.stdout.write(`  Page ${page} ... `);
    sh(`node "${CDP}" nav ${TARGET} "${url}"`, 15000);
    sh(`sleep 5`);
    TARGET = findTarget();

    const ids = getPostIdsFromPage();
    let newCount = 0;
    for (const id of ids) {
      if (!seen.has(id)) { seen.add(id); allIds.push(id); newCount++; }
    }
    console.log(`${ids.length} posts (${newCount} new)`);

    if (ids.length === 0 || newCount === 0) break;
  }
  console.log(`Total: ${allIds.length} posts\n`);

  // Phase 2: fetch detail + download videos
  console.log("Phase 2: Downloading videos...\n");
  let dl = 0, skip = 0, fail = 0;

  for (let i = 0; i < allIds.length; i++) {
    const postId = allIds[i];
    const tag = `[${i + 1}/${allIds.length}]`;

    if (completed.has(postId)) { console.log(`${tag} ${postId} SKIP`); skip++; continue; }

    process.stdout.write(`${tag} ${postId} ... `);

    let detail;
    try {
      detail = fetchDetail(postId);
    } catch (err) {
      console.log("reconnecting...");
      TARGET = findTarget();
      await sleep(2000);
      try {
        detail = fetchDetail(postId);
      } catch (err2) {
        console.log(`ERR: ${err2.message.slice(0, 80)}`);
        fail++;
        continue;
      }
    }

    if (new Date(detail.date) < CUTOFF_DATE) {
      console.log("cutoff");
      completed.add(postId);
      saveProgress(completed);
      continue;
    }

    if (!detail.videos.length) {
      console.log("no video");
      completed.add(postId);
      saveProgress(completed);
      await sleep(150);
      continue;
    }

    console.log(`${detail.videos.length} video(s) [${detail.title.slice(0, 40)}]`);

    for (const v of detail.videos) {
      const md = monthDir(detail.date);
      const dir = `${BASE_DIR}/${md}`;
      mkdirSync(dir, { recursive: true });
      const filename = `${v.name}.${v.ext}`;
      const destPath = `${dir}/${filename}`;

      if (existsSync(destPath) && Math.abs(statSync(destPath).size - v.size) < 1024) {
        console.log(`  SKIP: ${md}/${filename}`);
        skip++;
        continue;
      }

      process.stdout.write(`  DL ${filename} (${fmtSize(v.size)}) ... `);
      try {
        const code = downloadVideo(v.url, destPath);
        if (code === "200") {
          console.log(`OK (${fmtSize(statSync(destPath).size)})`);
          dl++;
        } else {
          console.log(`FAIL (${code})`);
          fail++;
        }
      } catch (dlErr) {
        console.log(`FAIL: ${dlErr.message.slice(0, 80)}`);
        fail++;
      }
    }

    completed.add(postId);
    saveProgress(completed);
    await sleep(400);
  }

  console.log(`\n=== Done === DL:${dl} SKIP:${skip} FAIL:${fail}`);
}

main().catch(e => { console.error("Fatal:", e.message); process.exit(1); });
