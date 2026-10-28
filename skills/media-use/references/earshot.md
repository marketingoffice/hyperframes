# Earshot — listening to audio you cannot hear

[earshot](https://github.com/Leonxlnx/earshot) gives an agent ears: it describes, matches, trims and critiques audio locally on CPU. Use it **before saying how any audio sounds** — picking between SFX or BGM candidates, finding the clean moment in a long clip, checking sync to picture, or reviewing a finished render's mix.

Opt-in, never required. Setup (once): `pip install -e "<earshot repo>[mcp]"` then `earshot doctor`. Each CLI call loads models (~20-40 s); for several calls run the MCP server (`python -m earshot mcp`) or one Python script.

| Need                                                          | Command                                                                 |
| ------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Does this SFX fit the cue? (rank Openverse/HeyGen candidates) | `earshot rank "glass shatter" a.mp3 b.mp3 c.mp3`                        |
| Best moment inside a long recording                           | `earshot find clip.mp3 "a single key press" --top 3` → trim             |
| Real recording vs code-synthesized                            | `earshot realness file.mp3`                                             |
| Whole render: events, sync to cuts, loudness                  | `earshot timeline out.mp4 --video out.mp4` / `earshot critique out.mp4` |
| Measurements only (no models)                                 | `earshot measure file.wav` (LUFS, true peak)                            |

Workflow with media-use: resolve 3-5 SFX candidates (`audio/scripts/openverse.mjs --list`, HeyGen retrieval) → `earshot rank` against the cue description → keep the winner → after render, `earshot critique` and fix flagged timestamps. Quote the numbers (z-score, LUFS) when reporting.
