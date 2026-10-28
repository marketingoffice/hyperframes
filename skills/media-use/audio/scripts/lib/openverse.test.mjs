import assert from "node:assert/strict";
import { test } from "node:test";
import { needsAttribution, searchOpenverse, toRecord } from "./openverse.mjs";

const hit = {
  id: "a1",
  title: "Glass",
  creator: "Ann",
  license: "by",
  license_version: "4.0",
  url: "https://x/y.mp3",
  duration: 1500,
};

test("toRecord converts ms to seconds", () => {
  assert.equal(toRecord(hit).duration_s, 1.5);
});

test("needsAttribution: cc0 no, by yes", () => {
  assert.equal(needsAttribution({ license: "cc0" }), false);
  assert.equal(needsAttribution({ license: "by" }), true);
});

test("searchOpenverse sends commercial filter + token, drops long clips", async () => {
  let seen;
  const fetch = async (url, init) => {
    seen = { url, init };
    return {
      ok: true,
      json: async () => ({ results: [hit, { ...hit, id: "b", duration: 99000 }] }),
    };
  };
  const out = await searchOpenverse("glass", {}, { fetch, env: { OPENVERSE_TOKEN: "t" } });
  assert.equal(out.length, 1);
  assert.match(seen.url, /license_type=commercial/);
  assert.equal(seen.init.headers.Authorization, "Bearer t");
});

test("searchOpenverse throws on HTTP error", async () => {
  const fetch = async () => ({ ok: false, status: 429 });
  await assert.rejects(searchOpenverse("x", {}, { fetch, env: {} }), /429/);
});
