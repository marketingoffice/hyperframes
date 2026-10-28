#!/usr/bin/env node
// openverse.mjs — search/download openly-licensed audio, record its credit.
//   node openverse.mjs "glass shatter" --project ./proj [--category sound_effect|music]
//        [--limit 5] [--pick 1] [--list]
// Writes assets/openverse/<slug>.<ext> and appends the credit to
// assets/openverse/credits.json. --list prints candidates without downloading.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { extname, join, resolve } from "node:path";
import { downloadOpenverse, needsAttribution, searchOpenverse } from "./lib/openverse.mjs";

const argv = process.argv.slice(2);
const flag = (n, d) => {
  const i = argv.indexOf(`--${n}`);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : d;
};
const query = argv.find((a, i) => !a.startsWith("--") && !argv[i - 1]?.startsWith("--"));
if (!query) {
  console.error(
    'usage: openverse.mjs "<query>" --project <dir> [--category c] [--limit n] [--pick n] [--list]',
  );
  process.exit(2);
}
const project = resolve(flag("project", "."));
const results = await searchOpenverse(query, {
  category: flag("category", "sound_effect") === "any" ? "" : flag("category", "sound_effect"),
  limit: Number(flag("limit", "5")),
});
if (!results.length) {
  console.error(`openverse: no results for "${query}"`);
  process.exit(1);
}
results.forEach((r, i) =>
  console.error(
    `  ${i + 1}. ${r.title} — ${r.creator} [${r.license} ${r.license_version}] ${r.duration_s ?? "?"}s`,
  ),
);
if (argv.includes("--list")) process.exit(0);

const rec = results[Math.max(0, Number(flag("pick", "1")) - 1)] ?? results[0];
const slug =
  query
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40) || "x";
const ext = extname(new URL(rec.audio_url).pathname) || ".mp3";
const rel = `assets/openverse/${slug}${ext}`;
await downloadOpenverse(rec, join(project, rel));

const creditsPath = join(project, "assets/openverse/credits.json");
const credits = existsSync(creditsPath) ? JSON.parse(readFileSync(creditsPath, "utf8")) : [];
credits.push({ file: rel, requires_attribution: needsAttribution(rec), ...rec });
writeFileSync(creditsPath, JSON.stringify(credits, null, 2));
console.log(
  `resolved openverse → ${rel} (${rec.license} ${rec.license_version}, ${rec.duration_s ?? "?"}s${needsAttribution(rec) ? ", ATTRIBUTION REQUIRED" : ""})`,
);
