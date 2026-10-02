# Hands-free demo recut

Same workflow as `videos/alex-demo/recut/WORKFLOW.md`, with these differences for this recording:

- **Transcript:** local Parakeet ASR (`asr.py`, sherpa-onnx; the model comes from GitHub releases) gives word timings.
- **Speaker split:**
  - Alex and the presenter overlap in pitch here, so speakers come from an MFCC classifier trained on known turns.
  - Garbled presenter lines were rebuilt from Alex's confirmations and the on-screen values.
  - `hspans.json` holds the presenter spans and the line each one maps to; `null` means a filler that is muted.
- **Alex speech:** taken from the transcribed words (not energy), so background noise in waits isn't kept.
- **Waits:** each one keeps at most ~1 s of the most visible screen change. The estimate-build start and finish get ~2 s holds.
- **Alex levelling:** Alex is recorded about 30 dB down, so each turn is gain-matched individually. That is followed by a compressor and a fixed measured gain; avoid dynamic `loudnorm`, which under-boosts the start of the track. Turns land within 2.1 dB of each other.
- **Source handling:**
  - The video stream starts 23 ms after the audio, so seeks are offset by −20 ms.
  - The browser bookmarks bar is cropped off (`crop=1338:1002:0:78`).
- **AAC delay:** measure the render's audio offset before mastering. This render had **no** 21 ms delay, unlike the Alex demo. Never apply that fix blind.
- `gen.py` builds `index.html` from `index.tpl.html`; every cue is given in source seconds and mapped through `plan.json`.

## v3 (mobile-first framing)

- **Full-bleed 16:9:** the 4:3 recording is scaled to 1920 px wide (1438 px tall), and a per-scene vertical offset crops it to 1080. `FRAMING` in `gen.py` sets the offset (0–249 recording px). The offset changes only at a cut, in the middle of the 0.2 s dissolve. There are no pans and no zooms.
- **Highlight boxes:** gold boxes replace the camera moves. `BOXES` in `gen.py` gives each box a rectangle in recording px plus edit-time in/out points. Before placing a box, check the region is static over its window (mean pixel diff against a reference frame).
- **Speaker-bleed audit:** score every kept Alex interval with the speaker classifier (share of voiced frames that sound like the presenter). An interval over ~20% is presenter bleed, so drop it via `DROP` in `build.py` (the 270.0–274.6 HVAC line scored 26%).
- **Hook music:** sits about 12 dB under the hook voiceover (volume 0.16).
