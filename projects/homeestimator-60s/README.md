# HomeEstimator.ai — 60s GC Cut

HyperFrames composition for the 60-second GC-persona social cut. Vertical **1080×1920**, 30fps,
locked to 60.0s.

> Engineering notes only. The client-facing script deliverable is a `.docx` per brand rules —
> this file is not that deliverable.

## Scene map

| #   | Window | Dur | Kind            | Status          |
| --- | ------ | --- | --------------- | --------------- |
| 1   | 0–6s   | 6s  | A-roll (avatar) | **Placeholder** |
| 2   | 6–16s  | 10s | B-roll (stock)  | **Placeholder** |
| 3   | 16–24s | 8s  | A-roll (avatar) | **Placeholder** |
| 4   | 24–34s | 10s | Motion graphics | Built           |
| 5   | 34–44s | 10s | Motion graphics | Built           |
| 6   | 44–51s | 7s  | A-roll (avatar) | **Placeholder** |
| 7   | 51–60s | 9s  | Motion graphics | Built           |

Chapter-break gold sweeps sit on track 2 at each seam from Scene 3 onward. The persistent
logo lockup is track 3, spanning the full 60s.

## Open swap points

Three things are stubbed and need real assets before this renders as final:

1. **Logo** — `assets/logo/` is empty. The brand rule is the transparent logo blended
   bottom-left on every creative. Currently a CSS placeholder lockup stands in at the correct
   position and scale; see the `SWAP POINT` comment on `.logo-lockup` in `index.html`.
   Drop in `Transparent_Background.png` and replace `.logo-mark` with an `<img>`.
2. **A-roll footage** — Scenes 1, 3, 6 render as framed avatar placeholders carrying the VO
   line and the correct durations, so the timeline is complete and timed. Swap each
   `.aroll-frame` block for a `<video>` clip when the HeyGen renders exist.
3. **Scene 2 stock plate** — a described placeholder, not footage. Needs the kitchen-table
   shot sourced and dropped in as a `<video>`.

The Scene 5 proposal total (`$186,400`) is **sample figure, not a claim** — swap it for the
client's own sample proposal data before this ships.

## Brand constraints encoded here

- Palette limited to `#0A0A0A` / `#1A1A1A` deep black and `#D4AF37` / `#C9A84C` / `#F9E076` gold.
- CTA is the **3-day money-back guarantee** (Scene 7), not "book a demo".
- Proof point is **23+ years of field data** — rotated deliberately away from "<5% variance"
  and "150+ awards".
- Brand name typeset exactly as **HomeEstimator.ai**; lowercase `homeestimator.ai` is used only
  where it reads as a URL.
- No "free" language anywhere.

## Dev loop

```bash
npx hyperframes lint      # structure
npx hyperframes check     # browser gate — runtime, layout, motion, contrast
npx hyperframes preview   # Studio timeline
```

`render` additionally needs FFmpeg, which is not installed in the container this was authored in.
