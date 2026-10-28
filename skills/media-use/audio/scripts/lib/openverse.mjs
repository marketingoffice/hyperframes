// openverse.mjs — openly-licensed audio from Openverse (https://api.openverse.org).
// Opt-in SFX/music source: search CC0 / CC-BY / etc. audio and download it with
// the attribution the license requires. Anonymous access is rate-limited; set
// $OPENVERSE_TOKEN (OAuth bearer) for higher limits. Commercial-safe by default
// (license_type=commercial); pass allowDerivatives=false to also exclude ND.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

const API = "https://api.openverse.org/v1";

/** Trim an Openverse audio result to what we persist (and credit). */
export function toRecord(r) {
  return {
    id: r.id,
    title: r.title ?? "",
    creator: r.creator ?? "",
    license: r.license ?? "",
    license_version: r.license_version ?? "",
    license_url: r.license_url ?? "",
    source_url: r.foreign_landing_url ?? "",
    audio_url: r.url ?? "",
    duration_s: typeof r.duration === "number" ? Number((r.duration / 1000).toFixed(3)) : null,
    attribution: r.attribution ?? "",
  };
}

/** CC0 / public-domain marks need no credit; everything else does. */
export function needsAttribution(rec) {
  return !["cc0", "pdm"].includes(String(rec.license).toLowerCase());
}

export async function searchOpenverse(query, opts = {}, deps = {}) {
  const fetchImpl = deps.fetch ?? fetch;
  const env = deps.env ?? process.env;
  const {
    category = "sound_effect", // sound_effect | music | pronunciation | …; "" for any
    limit = 5,
    maxDurationS = 15,
    allowDerivatives = true,
  } = opts;
  const qs = new URLSearchParams({
    q: query,
    license_type: allowDerivatives ? "commercial,modification" : "commercial",
    page_size: String(limit),
    mature: "false",
  });
  if (category) qs.set("category", category);
  if (maxDurationS) qs.set("length", "short");
  const headers = env.OPENVERSE_TOKEN ? { Authorization: `Bearer ${env.OPENVERSE_TOKEN}` } : {};
  const res = await fetchImpl(`${API}/audio/?${qs}`, { headers });
  if (!res.ok) throw new Error(`Openverse search HTTP ${res.status}`);
  const body = await res.json();
  return (body.results ?? [])
    .map(toRecord)
    .filter((r) => r.audio_url && (r.duration_s == null || r.duration_s <= maxDurationS));
}

export async function downloadOpenverse(rec, destAbs, deps = {}) {
  const fetchImpl = deps.fetch ?? fetch;
  const res = await fetchImpl(rec.audio_url);
  if (!res.ok) throw new Error(`Openverse download HTTP ${res.status}`);
  mkdirSync(dirname(destAbs), { recursive: true });
  writeFileSync(destAbs, Buffer.from(await res.arrayBuffer()));
}
