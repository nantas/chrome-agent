/** Tests for scripts/lib/fanbox-shared.mjs — pure helpers only (no CDP/network). */

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  escapeXml,
  extractChineseText,
  extractActorNames,
  generateNfo,
  sh,
} from "../scripts/lib/fanbox-shared.mjs";

test("escapeXml escapes all four entities", () => {
  assert.equal(escapeXml(`a & b <c> "d"`), "a &amp; b &lt;c&gt; &quot;d&quot;");
});

test("extractChineseText returns first block above 30% zh ratio and >=30 chars", () => {
  const body = "short\n\n" + "这是一段足够长的中文文本用来测试提取逻辑是否正常工作并且能够被正确识别" + "\n\nenglish only block here";
  const result = extractChineseText(body);
  assert.ok(result.includes("中文文本"));
});

test("extractChineseText returns null for empty / non-Chinese input", () => {
  assert.equal(extractChineseText(""), null);
  assert.equal(extractChineseText(null), null);
  assert.equal(extractChineseText("english only, no chinese at all in this block"), null);
});

test("extractActorNames matches candidates case-insensitively, dedupes, falls back to ATD", () => {
  const candidates = ["ULALA", "HINA"];
  assert.deepEqual(extractActorNames("[Fanbox] Ulala & HINA", candidates), ["ULALA", "HINA"]);
  assert.deepEqual(extractActorNames("no match here", candidates), ["ATD"]);
});

test("generateNfo emits escaped title, actors, and date fields", () => {
  const nfo = generateNfo({
    title: 'A & "B"',
    sorttitle: "A",
    plot: "剧情<简介>",
    date: "2026-08-12T10:00:00",
    actors: ["ULALA"],
  });
  assert.match(nfo, /<title>A &amp; &quot;B&quot;<\/title>/);
  assert.match(nfo, /<name>ULALA<\/name>/);
  assert.match(nfo, /<year>2026<\/year>/);
  assert.match(nfo, /<premiered>2026-08-12<\/premiered>/);
  assert.match(nfo, /<dateadded>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}<\/dateadded>/);
});

test("sh runs a command and trims output", () => {
  assert.equal(sh("echo hello"), "hello");
});
