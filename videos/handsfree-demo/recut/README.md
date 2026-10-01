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
