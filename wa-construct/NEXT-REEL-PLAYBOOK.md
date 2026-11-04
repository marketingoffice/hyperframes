# WA Construct: Next Reel Playbook (self-contained, for a fresh Claude session)

Paste this whole file into a new Claude session. Everything needed is here, so the session should not need to re-derive anything. Fill the **INPUTS** block first.

## 0. Rules that never change

- Brand: WA Construct, design-build firm, Mountainside, NJ (waconstruct.com).
- Never mention pricing or HomeEstimator.ai.
- No voiceover. Sound = real construction audio first, quiet music bed under it.
- Output: 1080x1920, 9:16, 30 fps, H.264 (`-preset veryfast`), yuv420p, AAC 48 kHz 192k.
- Post as a NEW Short. Never re-upload an old file.

## 1. INPUTS (fill before starting)

```
TOWN:
COUNTY:
SOURCE CLIPS (Drive folder "2026 Site RawVideo WA Construct"): list file names + length of each
PROJECT TYPE (pour / framing / demo / excavation / lift / driveway / other):
THE BIG EVENT in the footage (the most dramatic 1-2 seconds):
```

## 2. Lessons from the failed Short (do not repeat)

| Mistake                                                | Fix                                                                         |
| ------------------------------------------------------ | --------------------------------------------------------------------------- |
| Opened mid-process ("THEN the base is compacted")      | Open on the biggest event or a risky question, text on frame 1              |
| Slots longer than the clips (2 s clip in a 4-5 s slot) | Build the timeline FROM the clip lengths, never the reverse                 |
| 24 s runtime, 6 s of CTA + outro                       | Total 15-18 s including outro                                               |
| Too much text in the first 2 s                         | Max one headline + one short subline, ~7 words per card                     |
| Text in the Shorts UI zone                             | Keep text between y=1100 and y=1500 (of 1920) and 120 px off the right edge |
| Off-topic tags (home addition on a driveway video)     | Tags must describe THIS video                                               |
| "Burned-in captions" with no speech                    | The on-screen text cards ARE the captions. No separate captions track       |
| Stuffed title ("NJ New Jersey")                        | One clean keyword + town                                                    |

## 3. What gets views (pattern from the channel's winners)

Basement Wall Pour (1,229), Day 1 to Framed Walls (1,203), "Most Dangerous Part of Construction?" (954) each opened with one of:

1. A big event already happening (pour, lift, demo)
2. A visible change (before -> after)
3. A risky or curious question

Pick ONE of those for frame 1. Do not open with a process step.

Honest note: nobody can guarantee views. This plan removes known retention killers. Check results in YouTube Studio (Engagement -> Viewed vs. swiped away; target above 70% viewed) and iterate.

## 4. Recommended next reel (default concept)

**"Day 1 to Framed" style time-compression OR the biggest-event clip.** Choose whichever the footage supports:

- **A. Big event** (pour, truss set, crane lift, demolition): start on the event at its peak.
- **B. Visible change**: hard cut between two states (empty lot -> framed, old -> new).
- **C. Risky question**: e.g. "Would you stand under this?" over a lift or truss shot.

Default hook line (edit to fit footage): **WATCH THIS GO UP IN [N] DAYS** / ([Town], NJ)

## 5. Timeline template (total 16-18 s)

Build durations from the real clip lengths. Cut pace: a new shot every 2-3 s.

| Time      | Visual                                                                                                                                                  | Text card (bottom zone)                                                        |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 0.0-2.5   | Biggest-event clip, already in motion, tight framing                                                                                                    | Headline (Roboto Black): line 1 white, line 2 gold #b7964e. Appears on frame 1 |
| 2.5-5.5   | Context shot: what it is and why it matters                                                                                                             | One short sentence (Roboto Light, white)                                       |
| 5.5-9.5   | Process/progress shot #1, subtle speed-ramp or slow zoom                                                                                                | One short sentence                                                             |
| 9.5-13.5  | Process/progress shot #2 or the "change" shot                                                                                                           | One short sentence                                                             |
| 13.5-15.5 | Wide finished/result shot                                                                                                                               | Payoff line, e.g. "Built right in [Town], NJ."                                 |
| 15.5-17.5 | Merged CTA + logo outro (shortened from 3.1 s to about 1.8 s): white screen, logo wipe-in, waconstruct.com fades up. Text: "Tell us about your project" | none                                                                           |

Loop trick: make the last frame visually close to the first so the Short replays smoothly.

## 6. Format

- WA logo top-left, small, always visible except on the outro.
- Fonts: Roboto Black (headline), Roboto Light (subline). Install first and verify with `fc-list | grep -i roboto`. No "01/05" numbering.
- Whoosh SFX on hard cuts, kept subtle.
- Audio: construction sound leads. Music from the Drive music folder at roughly -20 dB under it. Check the license. Fade music out with the outro. Loudness about -14 LUFS.

## 7. Tooling and model tiers (to save credits)

| Step                                        | Tier            | Notes                                                                               |
| ------------------------------------------- | --------------- | ----------------------------------------------------------------------------------- |
| Pull Studio stats, read analytics           | Light           | Viewed vs. swiped on the last 3 Shorts                                              |
| Download clips, probe durations (`ffprobe`) | Light           | Fill the INPUTS clip lengths                                                        |
| Write timeline with real durations          | Mid             | Follow section 5                                                                    |
| Trims, concat, audio mix, encode (ffmpeg)   | Light or Mid    | Commands below                                                                      |
| Text overlays, logo wipe outro              | Mid             | ffmpeg `drawtext`, or HyperFrames (this repo) rendered to MP4 / transparent overlay |
| Hook wording + final QC                     | Strongest, once | Review frame 1 and the QC checklist only                                            |
| Title, description, tags, schedule          | Light           | Section 9                                                                           |

Tip: do the strongest-model pass LAST and only on the finished MP4's frame 1, the captions and the checklist. Do not spend it on the mechanical steps.

### ffmpeg cheat-sheet

```bash
# probe clip length
ffprobe -v error -show_entries format=duration -of csv=p=0 clip.mp4

# normalize each clip to 1080x1920 30fps (crop to fill, no stretching)
ffmpeg -i in.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1" -an -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p seg.mp4

# slow digital zoom-in (4 s clip, 30 fps)
ffmpeg -i seg.mp4 -vf "zoompan=z='min(zoom+0.0008,1.12)':d=1:s=1080x1920:fps=30" -t 4 zoomed.mp4

# final encode
ffmpeg -i joined.mp4 -i mix.m4a -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 30 -c:a aac -ar 48000 -b:a 192k -movflags +faststart -shortest final.mp4
```

## 8. QC checklist (all must pass before upload)

- [ ] Frame 1 shows action AND the headline text (extract with `ffmpeg -i final.mp4 -frames:v 1 f1.png` and look at it)
- [ ] Total length 15-18 s including outro
- [ ] No text outside y=1100-1500 safe zone, none within 120 px of the right edge
- [ ] Every clip long enough for its slot, no frozen frames
- [ ] Construction audio audible, music underneath, music fades with the outro
- [ ] No pricing, no HomeEstimator.ai anywhere
- [ ] Town spelled correctly everywhere
- [ ] Specs verified: `ffprobe` shows 1080x1920, h264, aac

## 9. Upload metadata template

- **Title** (under 70 chars): `[Hook keyword] | [Town] NJ`. Examples: `Watch This Go Up in 5 Days | [Town] NJ`, `Why Driveways Crack in NJ (It Starts Here) | [Town] NJ`
- **Description**
  - Line 1: names the town, e.g. "[Project type] in [Town], NJ."
  - Line 2: "Design-build home additions, remodels and custom homes in Northern and Central New Jersey · https://waconstruct.com/get-in-touch/"
  - Hashtags (first 3 show above the title): `#NewJersey #NJhomes #newjerseybuilder` plus ONE topic tag for this video (e.g. `#NJdriveway`, `#framing`, `#foundation`). No global tags (`#construction #satisfying #asmr`).
- **Tags**: New Jersey, WA Construct, [town] NJ, [county] County NJ, design build New Jersey, plus 2-3 specific to this video's subject.
- **Schedule**: 7-9 AM or 6-9 PM US Eastern. Confirm against the channel's own "When your viewers are on YouTube" report.

## 10. After posting

- Day 1 and Day 7: record views, viewed-vs-swiped %, average view duration.
- If viewed is under 60%, change the hook only, keep everything else, and post the next Short.
- Log the result in `wa-construct/RESULTS.md` (one line per Short: date, hook type, viewed %, views).
