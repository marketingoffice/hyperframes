# Sound effects (SFX)

Named sound effects, produced by the shared audio engine (`scripts/audio.mjs` → `scripts/lib/sfx.mjs`). **Provider-gated** by the engine's one switch — whether a HeyGen credential is present, decided once (not per cue):

- **HeyGen credential present → retrieve every cue** from HeyGen's audio library (`/v3/audio/sounds`, `type=sound_effects`, `min_score=0.4`). Search-and-download, **not** generation. The bundled library is NOT consulted.
- **No credential → the bundled 21-file library** (`assets/sfx/` + `manifest.json`): match each cue name, copy the matched file into the project. Offline, deterministic, free.

There is no `npx hyperframes sfx` command. SFX is never generated — it is retrieved (online) or taken from the bundled library (offline).

## Cues — request → meta

Each line names the effects it wants: `lines[].sfx: ["whoosh", "ui click"]`. The engine flattens these into cues, resolves them per the switch, dedupes identical `(id, name)` pairs (the same effect named twice downloads/copies once), and writes `audio_meta.sfx[]`:

```jsonc
{
  "id": "3",                       // joins the cue to the caller's model (frame / scene / segment)
  "name": "whoosh",
  "file": "assets/sfx/whoosh.mp3", // downloaded or copied, relative to project root
  "source": "heygen" | "local",    // which route resolved it
  "offset_s": 0,                   // delay from the line's start
  "duration_s": 0.57,
  "volume": 0.35                   // SFX sit UNDER voice + BGM
}
```

A cue that matches nothing is **skipped** (recorded as an anomaly); SFX never blocks a render.

## HeyGen retrieval (credentialed)

`searchSounds(name, "sound_effects", { limit: 3, minScore: 0.4 })` → top hit → `assets/sfx/<slug>.mp3`. Results are ranked by `score` (each carries a presigned `audio_url`, `duration`, `description`). The floor is **0.4** because good SFX hits score ~0.5–0.67 — below the API's default `0.7`, which would silently drop most named cues (only whoosh/swoosh-family clears 0.7). `duration_s` comes from the result (else 1.0). Name effects concretely (`glass shatter`, not `dramatic sound`); a vague query returns a poor match.

## Bundled library (no credential)

21 curated files in `assets/sfx/`, indexed by `manifest.json` — `{ file, duration, description }` per key (e.g. `whoosh`, `pop`, `click`, `chime`, `riser`, `impact-bass-1`, `glitch-1`, `typing`, …). A cue name resolves by **manifest key, file basename, or slug**, so `whoosh`, `whoosh.mp3`, or `"ui click"` (→ slug) all match. Matched files are copied into the project's `assets/sfx/`; `duration_s` comes from the manifest, so timing is known **offline** — e.g. `riser` is 10.03s, so trigger it at `climax − 10.03s`. The manifest's `description` field carries placement hints per effect; read `assets/sfx/manifest.json` for the full set and usage.

## Openverse (opt-in, openly licensed)

Longer tail than the bundled 21, no HeyGen credential needed. Openverse indexes CC0 / CC-BY audio; search is commercial-safe by default.

```bash
node <SKILL_DIR>/audio/scripts/openverse.mjs "glass shatter" --project <dir> --list   # candidates
node <SKILL_DIR>/audio/scripts/openverse.mjs "glass shatter" --project <dir> --pick 2 # download
```

Writes `assets/openverse/<slug>.<ext>` plus `assets/openverse/credits.json`. **CC-BY and similar need attribution** — the resolve line says `ATTRIBUTION REQUIRED`; put every such entry's `attribution` string in the video description/credits. CC0 needs none. Optional `$OPENVERSE_TOKEN` lifts anonymous rate limits. Add the clip to the composition as an ordinary SFX cue (volume ~0.35).

## Rules

- **Volume ~0.35.** SFX must sit under narration and BGM, not fight them.
- **No match → skip, don't fail.** A missing effect logs an anomaly and moves on; never a render blocker.
- **Retrieval (credentialed) or bundled library (offline) — never generation.** You search HeyGen by text, or match a name against the 21-file manifest.
- **One asset per distinct name.** Reuse across lines is deduped to a single download/copy, many cues.
- **The switch is global, not per cue.** With a credential, retrieval handles even the long tail (effects not in the 21); without one, only the 21 bundled names resolve.
