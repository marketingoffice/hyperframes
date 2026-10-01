# Re-voice + tighten a screen-recorded product demo

Workflow for HomeEstimator demo videos built from a real screen recording: replace the
human presenter's voice with a new American voiceover, remove fillers, trim dead air,
keep the AI agent's (Alex's) audio and every word intact, and stay frame-exact.

Used for two delivered videos (both approved):

- `videos/alex-demo/`: Alex on WA Construct's website. Scripts are in this folder.
- `videos/handsfree-demo/`: the hands-free estimating demo inside the app. Its scripts and the
  recording-specific notes are in `videos/handsfree-demo/recut/`.

Start a new demo from the closest one and copy its `recut/` scripts.

Scripts in this folder expect a work dir (e.g. `/tmp/claude-0/alex/re/`) whose parent holds
`edited4.mp4` (cleaned edit, 30 fps), `vo_final.wav` (levelled VO, 48 kHz mono),
`cvo16.wav` (VO at 16 kHz), `t1f.wav` / `musicloop.wav` (card music).

## 1. Ask first (house rule)

- Which voice? Use an ElevenLabs **built-in** voice (works on all plans). Used: intro
  "Desmond – Trailer/Ad", homeowner lines a second voice; Chris / Eric / Brian are safe defaults.
  The same person in the demo should ideally get the same voice.
- Free ElevenLabs plan = no commercial licence. Investor/sales video needs Starter+.
- Pacing: "tight" = cap silences, keep every word, keep the result hold.

## 2. Transcript + who speaks when

- **Word-level transcript:**
  - ElevenLabs scribe is expensive (~1,500 credits for 2 min), so use local Parakeet
    instead: `videos/handsfree-demo/recut/asr.py`, with sherpa-onnx installed via pip.
  - The model, `sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8`, downloads from GitHub
    releases. HuggingFace and OpenAI hosts are blocked here.
  - It takes about 1 minute for 9 minutes of audio.
- **Speaker split:** pick the method that fits the recording.
  - **Pitch:** works when the voices differ, as in the Alex demo (presenter ≈ 100 Hz,
    Alex ≈ 150 Hz).
  - **Timbre:** when pitch overlaps (hands-free), train an MFCC logistic classifier on
    clearly known turns and label every word.
  - **On-screen badge:** the "Alex Listening / Speaking / Working" badge helps, but it
    flickers mid-speech. Use it to confirm turns, not to label single words.
- **Garbled presenter lines:** rebuild them from what Alex confirms back and from the
  on-screen values (the field contents, checked cards and card index). Never guess numbers.
- **Fillers in waits** ("Yeah", "Mm-hmm" while Alex is working) are muted: their span is
  set to `null` in `hspans.json`.

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

- **Short breaks:** ElevenLabs often renders `<break time="2.5s"/>` as only about 0.5 s.
  Find the line boundaries from a transcript of the VO (run `asr.py` on it): use each
  line's first word, then snap to the energy onset. Use `align_lines.py` (silence chunks
  plus a DP over expected lengths) only as a fallback.
- **Extra takes:** the user's file may hold extra takes after the last line. Check the
  transcript and use only the main take.
- **Cutting:** give each line 40 ms pre-roll, a 100 ms tail and short fades, at 48 kHz mono.

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
- **Alex speech:** take it from the transcribed words outside the presenter spans, with the
  edges extended on the energy envelope. Do not use raw energy: waits contain noise that
  would be kept as "speech".
- **Waits** with on-screen changes keep up to about 1 s of the most visible change
  (motion map). Long estimate builds get ~2 s holds at the start and finish.
- **Quiet or uneven Alex** (hands-free: about −45 dB with a 10–15 dB spread):
  - Gain-match each turn on the 75th percentile of its active frames, ignoring
    clicks and chimes.
  - Then highpass, `afftdn`, a compressor and a **fixed measured gain**. Dynamic `loudnorm`
    under-boosts the start of the track.
  - Target: turns within about 2 dB of each other.
- `./level.sh` matches the new voice to Alex's loudness, then compresses and limits
  → `vo_new.wav`.
- Checks:
  - 0 overlap frames between the two voices.
  - Turn gaps between 0.3 and 0.65 s (median ~0.47 s) sounds natural; 0.25 s sounds robotic.
- `python3 audit.py u_ 0.7`: no uncovered speech, and no presenter voice left inside the
  kept Alex audio.

## 7. Video + composition

- **Probe the source first:**
  - It must be constant frame rate.
  - Check the video `start_time`. Hands-free started 23 ms after its audio, so every seek
    gets −20 ms.
  - Crop the browser bookmarks bar so personal tabs don't show.
- `python3 render.py`: per-piece frame-accurate encodes plus 6-frame dissolves, joined with
  the concat demuxer (stream copy). It must print `frames N expected N`.
- New project: generate `index.html` from a template with `gen.py`, giving every chapter
  and zoom cue in source seconds. Run `hyperframes check` and mark `#cam` with
  `data-layout-allow-overflow`; the zooms are intentional.
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
- **Measure the render's audio offset** against the reference mix with a wide lag search
  (±0.5 s) before mastering.
  - The Alex render had a 21.33 ms delay (one AAC priming block), fixed with
    `atrim=start=0.021333`.
  - The hands-free render had none. **Never apply the fix blind.**
- Then two-pass `loudnorm I=-14 TP=-1.5` with video copy.
- Renders take about 25 minutes. Snapshot the cards (`hyperframes snapshot --at …`)
  before rendering, because a late text change means a full re-render.
- Share copy: `-crf 26 -tune stillimage`, AAC 160k. Keep it under 30 MB (SSIM ≈ 0.995).

## 9. Frame-level QA before delivery

- Sync: 2 s windows every 2 s vs the reference mix. Expect 0.00 ms and correlation > 0.99.
- Loudness: −14.0 LUFS.
- `blackdetect`: none.
- `freezedetect`: only intentional holds (cards, ballpark result, static zoomed panels).
  Confirm the source recording has no freezes of its own.
- Contact sheets: every line (homeowner lines over "Alex is listening") and every cut
  (pre/post). Check chapters land on the right beat.
- `freezedetect` on an app recording: the screen is still whenever nobody clicks. Report
  the long static stretches and offer a slow camera push.
- Deliver the share copy and the master path. Commit `index.html` and `recut-plan.json`;
  large media stays out of git.

## 10. Cards and copy

- **Opening:** logo, gold rule, title and subtitle.
- **Closing:** follow what the user asks for.
  - Alex demo: "See Alex work with your leads / BOOK A LIVE DEMO /
    homeestimator.ai/book-demo".
  - Hands-free demo: "Try our hands-free mode / GO TO HOMEESTIMATOR.AI".
- **Rail notes:** totals and ranges carry "Example project — every project's estimate
  differs."
