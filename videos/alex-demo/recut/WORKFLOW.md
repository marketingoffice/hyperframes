# Re-voice + tighten a screen-recorded product demo

Workflow used for the Alex demo (HomeEstimator.ai on WA Construct's site): replace the
human presenter's voice with a new American voiceover, remove fillers, trim dead air,
keep the AI agent's (Alex's) audio and every word intact, and stay frame-exact.

Scripts in this folder expect a work dir (e.g. `/tmp/claude-0/alex/re/`) whose parent holds
`edited4.mp4` (cleaned edit, 30 fps), `vo_final.wav` (levelled VO, 48 kHz mono),
`cvo16.wav` (VO at 16 kHz), `t1f.wav` / `musicloop.wav` (card music).

## 1. Ask first (house rule)

- Which voice? Use an ElevenLabs **built-in** voice (works on all plans). Used: intro
  "Desmond – Trailer/Ad", homeowner lines a second voice; Chris / Eric / Brian are safe defaults.
  The same person in the demo should ideally get the same voice.
- Free ElevenLabs plan = no commercial licence. Investor/sales video needs Starter+.
- Pacing: "tight" = cap silences, keep every word, keep the result hold.

## 2. Find who speaks when

- `speakers_cluster.py` → speech segments + GMM speaker split (presenter ≈ 95–110 Hz,
  Alex ≈ 140–180 Hz); seeds presenter from the intro narration.
- `speakers_frames.py` → frame-level classifier (writes `pA.npy`, `db.npy`, `f0.npy`) to
  refine turn edges. Cross-check against the transcript and on-screen "Alex is listening".
- Record the presenter spans as `BLOCKS` in `build.py`.

## 3. Write the clean script

- Remove uh/um/false starts; keep every fact (town, sq ft, rooms, name/email/phone/address
  exactly as shown on screen). Intro lines: `intro_lines.json`; homeowner: `hlines.json`.
- Pin sync-critical lines to on-screen events (e.g. "I'm going to click on it" ends just
  before the click; check frames to find click times).
- Give the user copy-paste text with `<break time="2.5s" />` between lines, Multilingual v2.

## 4. Get the audio

- ElevenLabs connector if credits allow. If the account is out of credits, or
  `api.elevenlabs.io` is blocked by the environment network policy, have the user generate
  it and upload the MP3s.
- Never commit or echo API keys.

## 5. Split the takes into lines

- `align_lines.py <wav> <lines.json> <out.json>`: silence chunks + DP over expected line
  lengths (works even when breaks come out ~0.5 s). Cut each line with 40 ms pre-roll, 100 ms
  tail, short fades → `i1..i6.wav`, `u_h01..u_h21.wav` (48 kHz mono).

## 6. Build the re-cut

- `python3 build.py u_ 0.7`:
  - The presenter's audio is gated out completely; only Alex's speech windows are kept
    (−0.12 s / +0.28 s margins).
  - Silences over 0.7 s are trimmed to a ~0.5 s heard gap (HEAD 0.32 / TAIL 0.38,
    with a 0.2 s xfade).
  - New lines go at the presenter's original slot. They are shifted earlier if they would
    run into Alex.
  - Writes `plan.json` (frame-snapped pieces + time map), `alex_track.wav` and
    `tts_track.wav`.
- `./level.sh`: matches the new voice to Alex's loudness, then compresses and limits
  → `vo_new.wav`.
- Checks:
  - 0 overlap frames between the two voices.
  - Turn gaps between 0.3 and 0.65 s (median ~0.47 s) sounds natural; 0.25 s sounds robotic.
- `python3 audit.py u_ 0.7`: no uncovered speech, and no presenter voice left inside the
  kept Alex audio.

## 7. Video + composition

- `python3 render.py`: per-piece frame-accurate encodes plus 6-frame dissolves, joined with
  the concat demuxer (stream copy). It must print `frames N expected N`.
- `python3 remap.py`: rewrites the chapters, camera moves, scope-recap stagger, intro drift,
  demo fade and outro/card times through the new cut → `index_new.html`.
- Mix:
  - Card music: musicloop 0–3.2 s at −9 dB, plus closebed (silence until 3+N+0.07, then
    `t1f.wav`).
  - VO is delayed by 3000 ms; output passes through `alimiter` 0.89.
  - Encode the AAC at −0.5 dB.
- Install `recording.mp4` and `mix.m4a`, update `index.html`, then run `hyperframes lint`
  (0 errors).

## 8. Render + master

- `hyperframes render --quality high --output renders/raw.mp4`.
- The renderer delays audio by **21.33 ms** (one AAC priming block). Fix it in mastering
  with `atrim=start=0.021333`, then two-pass `loudnorm I=-14 TP=-1.5`, video copy.
- Share copy: `-crf 26 -tune stillimage`, AAC 160k. Keep it under 30 MB (SSIM ≈ 0.995).

## 9. Frame-level QA before delivery

- Sync: 2 s windows every 2 s vs the reference mix. Expect 0.00 ms and correlation > 0.99.
- Loudness: −14.0 LUFS.
- `blackdetect`: none.
- `freezedetect`: only intentional holds (cards, ballpark result, static zoomed panels).
  Confirm the source recording has no freezes of its own.
- Contact sheets: every line (homeowner lines over "Alex is listening") and every cut
  (pre/post). Check chapters land on the right beat.
- Deliver the share copy and the master path. Commit `index.html` and `recut-plan.json`;
  large media stays out of git.
