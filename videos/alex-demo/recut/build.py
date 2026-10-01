"""Re-edit the Alex demo: replace presenter lines with new VO, tighten pauses.

Usage: python3 build.py <prefix> [gap_max]   (prefix of homeowner line files, e.g. u_; gap_max default 0.6, used 0.7)
Writes plan.json (pieces + audio placements + time map) and vo_new.wav.
"""
import json, sys, wave
import numpy as np

SR = 48000
FPS = 30
X = 6  # xfade frames (0.2 s)
GAP_MAX = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6  # gaps longer than this get trimmed
HEAD, TAIL = 0.32, 0.38  # kept silence after / before speech at a trim (~0.5 s heard gap)
PART_GAP = 0.4  # gap between sentences inside one homeowner block

prefix = sys.argv[1] if len(sys.argv) > 1 else "ph_"


def rd(path):
    w = wave.open(path)
    assert w.getframerate() == SR, path
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getnchannels() > 1:
        x = x.reshape(-1, w.getnchannels()).mean(1)
    return x


def dur(path):
    w = wave.open(path)
    return w.getnframes() / w.getframerate()


# ---- homeowner blocks (src clean time spans to mute) ----
BLOCKS = [
    (69.0, 73.0, ["h01"]), (84.3, 87.5, ["h02"]), (95.25, 96.75, ["h03"]),
    (103.7, 105.55, ["h04"]), (118.8, 125.5, ["h05"]), (136.25, 138.0, ["h06"]),
    (142.35, 151.58, ["h07"]), (163.45, 163.95, ["h08"]), (167.55, 171.5, ["h09"]),
    (184.15, 207.0, ["h10", "h11", "h12", "h13", "h14"]), (223.35, 228.4, ["h15"]),
    (246.3, 262.4, ["h16", "h17", "h18", "h19"]), (284.7, 289.3, ["h20"]),
    (299.2, 301.65, ["h21"]),
]

vo = rd("../vo_final.wav")
db = np.load("../db.npy")
th = np.percentile(db, 30) + 12
sp = db > th  # 100 Hz speech mask (clean VO)

# Alex speech intervals: speech after 60.7 not inside homeowner blocks
mask = sp.copy()
mask[: int(60.7 * 100)] = False
for a, b, _ in BLOCKS:
    mask[int(a * 100): int(b * 100) + 1] = False
iv = []
i, n = 0, len(mask)
while i < n:
    if mask[i]:
        j = i
        while j < n and mask[j]:
            j += 1
        iv.append([i / 100, j / 100])
        i = j
    else:
        i += 1
merged = []
for a, b in iv:
    if merged and a - merged[-1][1] <= GAP_MAX:
        merged[-1][1] = b
    else:
        merged.append([a, b])
alex = [m for m in merged if m[1] - m[0] >= 0.12]

# ---- events: (src_start, src_end, kind, audio list[(src_offset, file)], head_override)
events = []
# intro lines placed against fixed on-screen moments
d = {k: dur(f"i{k}.wav") for k in range(1, 7)}
s1 = 0.6
s2 = s1 + d[1] + 0.45
events.append((s1, s2 + d[2], "tts", [(s1, "i1.wav"), (s2, "i2.wav")], None))
s3 = 43.35 - d[3]  # ends right before the "Talk with Alex" click (43.4)
s4 = 43.95
s5 = s4 + d[4] + 0.4
events.append((s3, s5 + d[5], "tts", [(s3, "i3.wav"), (s4, "i4.wav"), (s5, "i5.wav")], None))
s6 = 59.85 - d[6]  # ends before the "Start talking" click (~59.95)
events.append((s6, 59.85, "tts", [(s6, "i6.wav")], 0.45))
for a, b in alex:
    events.append((a, b, "alex", [], None))
for a, b, keys in BLOCKS:
    files = [f"{prefix}{k}.wav" for k in keys]
    tot = sum(dur(f) for f in files) + PART_GAP * (len(files) - 1)
    events.append((a + 0.06, a + 0.06 + tot, "tts", files, None))
events.sort(key=lambda e: e[0])

# resolve homeowner placement: never run into the next event
fixed = []
for k, e in enumerate(events):
    a, b, kind, aud, ho = e
    if kind == "tts" and aud and isinstance(aud[0], str):
        nxt = events[k + 1][0] if k + 1 < len(events) else 304.0
        prev_end = fixed[-1][1] if fixed else 0
        if b > nxt - 0.15:
            shift = b - (nxt - 0.15)
            if a - shift < prev_end + 0.1:
                raise SystemExit(f"line block at {a:.2f} too long by {shift:.2f}s")
            a, b = a - shift, b - shift
        t, pl = a, []
        for f in aud:
            pl.append((t, f))
            t += dur(f) + PART_GAP
        aud = pl
    fixed.append((a, b, kind, aud, ho))
events = fixed

# ---- pieces in src time ----
pieces = []  # [src_a, src_b]
cur = [max(0.0, events[0][0] - 0.24), None]
prev_end, prev_ho = events[0][1], events[0][4]
for e in events[1:]:
    a, b = e[0], e[1]
    gap = a - prev_end
    if gap > GAP_MAX:
        cur[1] = prev_end + (prev_ho if prev_ho else HEAD)
        pieces.append(cur)
        cur = [a - TAIL, None]
    prev_end = max(prev_end, b)
    prev_ho = e[4]
cur[1] = min(304.0, prev_end + 0.5)
pieces.append(cur)

# snap to frames
fr = [[round(a * FPS), round(b * FPS)] for a, b in pieces]
# new-timeline start frame of each piece (xfade overlap X frames)
starts, t = [], 0
for k, (fa, fb) in enumerate(fr):
    starts.append(t)
    t += (fb - fa) - (X if k < len(fr) - 1 else 0)
total_frames = t


def map_t(src):
    """src clean time -> new edit time (removed spans map to the next piece start)."""
    f = src * FPS
    for k, (fa, fb) in enumerate(fr):
        if f < fa:
            return starts[k] / FPS
        if f <= fb:
            return (starts[k] + f - fa) / FPS
    return total_frames / FPS


# ---- audio ----
# keep only Alex's speech windows (gated), so no presenter residue leaks through
base = np.zeros_like(vo)
ramp = int(0.02 * SR)
hspans = [(e[0], e[1]) for e in events if e[2] == "tts"] + [(a, b) for a, b, _ in BLOCKS]
for a, b in alex:
    lo, hi = a - 0.12, b + 0.28
    for ha, hb in hspans:
        if hb <= a and hb > lo: lo = hb + 0.02
        if ha >= b and ha < hi: hi = ha - 0.02
    ia, ib = int(lo * SR), int(hi * SR)
    seg = vo[ia:ib].copy()
    seg[:ramp] *= np.linspace(0, 1, ramp); seg[-ramp:] *= np.linspace(1, 0, ramp)
    base[ia:ib] = seg
out = np.zeros(int(total_frames / FPS * SR) + SR, np.float32)
xs = X * SR // FPS
for k, (fa, fb) in enumerate(fr):
    seg = base[fa * SR // FPS: fb * SR // FPS].copy()
    if k > 0:
        seg[:xs] *= np.linspace(0, 1, xs)
    if k < len(fr) - 1:
        seg[-xs:] *= np.linspace(1, 0, xs)
    o = starts[k] * SR // FPS
    out[o: o + len(seg)] += seg

# TTS level match to Alex (active-speech RMS)
def active_rms(x):
    h = SR // 100
    fr_ = x[: len(x) // h * h].reshape(-1, h)
    r = np.sqrt((fr_ ** 2).mean(1) + 1e-12)
    act = r[20 * np.log10(r) > 20 * np.log10(r.max()) - 30]
    return np.sqrt((act ** 2).mean())

alex_ref = np.concatenate([vo[int(a * SR): int(b * SR)] for a, b in alex])
target = active_rms(alex_ref)
tts = np.zeros_like(out)
placed = []
for a, b, kind, aud, _ in events:
    if kind != "tts":
        continue
    for s, f in aud:
        x = rd(f)
        x = x * (target / active_rms(x))
        o = int(map_t(s) * SR)
        tts[o: o + len(x)] += x
        placed.append([round(map_t(s), 3), f, round(len(x) / SR, 3)])
L = int(total_frames / FPS * SR)
for nm, arr in [("alex_track.wav", out[:L]), ("tts_track.wav", tts[:L] * 0.5)]:
    w = wave.open(nm, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(arr, -0.99, 0.99) * 32767).astype(np.int16).tobytes()); w.close()

json.dump({"fps": FPS, "x": X, "pieces": fr, "starts": starts, "total_frames": total_frames,
           "placed": placed, "events": [[round(e[0], 3), round(e[1], 3), e[2]] for e in events]},
          open("plan.json", "w"), indent=1)
print(f"pieces {len(fr)}  new length {total_frames/FPS:.2f}s (was 304.03)")
for name, t in [("click1", 43.4), ("click2", 59.95), ("alex1", 61.09), ("result", 275.6), ("end", 303.54)]:
    print(name, t, "->", round(map_t(t), 2))
