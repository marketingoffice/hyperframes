"""Hands-free demo recut: presenter replaced by new VO lines, Alex kept, waits trimmed (keeping on-screen changes)."""
import json, sys, wave
import numpy as np
SR, FPS, X = 48000, 30, 6
GAP_MAX, HEAD, TAIL, EVW = 0.7, 0.32, 0.38, (0.35, 0.85)
SRC_END = 525.85


def rd(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x.reshape(-1, w.getnchannels()).mean(1) if w.getnchannels() > 1 else x


def dur(p):
    w = wave.open(p); return w.getnframes() / w.getframerate()


src = rd("../src48.wav")
H = json.load(open("../hspans_v2.json"))
h = SR // 100
n = len(src) // h
db = 20 * np.log10(np.sqrt((src[: n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
th = np.percentile(db, 30) + 12
# Alex speech = transcribed words outside presenter spans, edges refined on the energy envelope
W = json.load(open("../words.json"))
inH = lambda t: any(a <= t <= b for a, b, _ in H)
DROP = [(244.0, 244.7), (247.9, 249.8), (256.4, 261.1), (294.2, 294.9), (297.5, 298.6), (300.6, 301.4), (303.7, 305.6)]
inD = lambda t: any(a <= t <= b for a, b in DROP)
iv = [[w["s"], w["e"]] for w in W if not inH((w["s"] + w["e"]) / 2) and not inD((w["s"] + w["e"]) / 2)]
loud = db > th
for v in iv:  # extend each word to where the speech energy actually ends/starts (max 0.4 s)
    a, b = int(v[0] * 100), int(v[1] * 100)
    k = 0
    while k < 40 and a - 1 > 0 and loud[a - 1]: a -= 1; k += 1
    k = 0
    while k < 40 and b < n and loud[b]: b += 1; k += 1
    v[0], v[1] = a / 100, b / 100
iv.sort()
alex = []
for a, b in iv:
    if alex and a - alex[-1][1] <= GAP_MAX: alex[-1][1] = max(alex[-1][1], b)
    else: alex.append([a, b])
alex = [m for m in alex if m[1] - m[0] >= 0.15]

# events: (start, end, kind, [(t, file)])
ev = [(a, b, "alex", []) for a, b in alex]
for a, b, key in H:
    if key:
        d = dur(f"{key}.wav"); ev.append((a + 0.05, a + 0.05 + d, "vo", [(a + 0.05, f"{key}.wav")]))
ev.sort(key=lambda e: e[0])
for k in range(len(ev) - 1):  # never run a line into the next speech
    a, b, kind, aud = ev[k]
    if kind == "vo" and b > ev[k + 1][0] - 0.2:
        sh = b - (ev[k + 1][0] - 0.2); prev = ev[k - 1][1] if k else 0
        assert a - sh > prev + 0.1, f"line at {a:.2f} too long by {sh:.2f}"
        ev[k] = (a - sh, b - sh, kind, [(t - sh, f) for t, f in aud])

# screen changes that happen *during* a re-voiced request would now show before the request is
# finished: hold the frame while John speaks, then replay each change right after his line.
mo_ = np.load("../motion.npy")
REPLAY = 1.2
replays = []
for k, (a, b, kind, aud) in enumerate(ev):
    if kind != "vo" or a < 5: continue
    ch = np.where(mo_[int(a * 10): int(b * 10)] > 0.004)[0] / 10 + a
    wins = []
    for c in ch:
        if not wins or c > wins[-1] + REPLAY: wins.append(float(c))
    if not wins: continue
    R = REPLAY * len(wins)
    nxt = ev[k + 1][0] if k + 1 < len(ev) else SRC_END
    assert b + R < nxt - TAIL, f"no room to replay after line at {a:.2f}"
    replays.append((a, b - a, [w - 0.3 for w in wins]))
    ev[k] = (a, b + R, kind, aud)

# on-screen change windows inside gaps: keep the most visible changes, capped per gap
mo = np.load("../motion.npy")
CAP, WMAX = 1.0, 1.2
sp = sorted([(e[0], e[1]) for e in ev])
gaps = [(sp[k][1], sp[k + 1][0]) for k in range(len(sp) - 1) if sp[k + 1][0] - sp[k][1] > GAP_MAX]
keep = []
for ga, gb in gaps:
    i0, i1 = int((ga + HEAD) * 10), int((gb - TAIL) * 10)
    if i1 <= i0: continue
    m = mo[i0:i1].copy(); got = 0.0
    while got < CAP and m.max() > 0.002:
        c = int(np.argmax(m)); t = (i0 + c) / 10
        a, b = max(ga + HEAD, t - 0.4), min(gb - TAIL, t - 0.4 + WMAX)
        keep.append([a, b]); got += b - a
        m[max(0, c - 4 - int(WMAX * 10)): c + int(WMAX * 10) + 4] = 0
EXTRA = [(159.4, 161.4), (205.0, 207.0), (453.9, 455.9), (484.6, 486.6), (504.0, 506.0)]  # estimate build start/finish
keep += [list(x) for x in EXTRA]
keep.sort()
mk = []
for a, b in keep:
    if mk and a <= mk[-1][1] + 0.5: mk[-1][1] = max(mk[-1][1], b)
    else: mk.append([a, b])
keep = mk

# speech spans + keep windows -> intervals of content; gaps between content > GAP_MAX are trimmed
content = [[e[0], e[1], "s"] for e in ev] + [[a, b, "k"] for a, b in keep]
content.sort()
pieces, cur = [], None
prev_end = None
for a, b, kind in content:
    if cur is None:
        cur = [max(0.0, a - 0.3), b]; prev_end = b; continue
    if a - prev_end > GAP_MAX:
        cur[1] = prev_end + HEAD; pieces.append(cur); cur = [a - TAIL, b]
    prev_end = max(prev_end, b); cur[1] = max(cur[1], b)
cur[1] = min(SRC_END, prev_end + 0.6); pieces.append(cur)
# merge pieces that overlap / are too short for 2 dissolves
mp = []
for p in pieces:
    if mp and p[0] <= mp[-1][1] + 0.1: mp[-1][1] = max(mp[-1][1], p[1])
    else: mp.append(p)
fr = [[round(a * FPS), round(b * FPS)] for a, b in mp]
for fa, fb in fr: assert fb - fa > 2 * X + 2, (fa / FPS, fb / FPS)
starts, t = [], 0
for k, (fa, fb) in enumerate(fr):
    starts.append(t); t += (fb - fa) - (X if k < len(fr) - 1 else 0)
total = t


def map_t(s):
    f = s * FPS
    for k, (fa, fb) in enumerate(fr):
        if f < fa: return starts[k] / FPS
        if f <= fb: return (starts[k] + f - fa) / FPS
    return total / FPS


# audio: Alex gated windows
base = np.zeros_like(src); ramp = int(0.02 * SR)
spans = [(e[0], e[1]) for e in ev if e[2] == "vo"] + [(a, b) for a, b, _ in H]
for a, b in alex:
    lo, hi = a - 0.12, b + 0.28
    for ha, hb in spans:
        if hb <= a and hb > lo: lo = hb + 0.02
        if ha >= b and ha < hi: hi = ha - 0.02
    ia, ib = int(lo * SR), int(hi * SR); seg = src[ia:ib].copy()
    fr_ = seg[: len(seg) // h * h].reshape(-1, h); r = np.sqrt((fr_ ** 2).mean(1) + 1e-12)
    ref = np.percentile(r, 90)
    act = r[(r > ref * 0.1) & (r < ref * 2)]  # ignore clicks / chimes when measuring
    seg *= 0.05 / np.percentile(act, 75)  # per-turn level match
    seg[:ramp] *= np.linspace(0, 1, ramp); seg[-ramp:] *= np.linspace(1, 0, ramp); base[ia:ib] = seg
# splice the name out of "Hi <name>, I'm Alex" (audio only; screen is static there)
i0, i1, i2 = int(45.14 * SR), int(45.755 * SR), int(49.40 * SR)
fade = int(0.012 * SR)
tail = base[i1:i2].copy(); tail[:fade] *= np.linspace(0, 1, fade)
base[i0 - fade:i0] *= np.linspace(1, 0, fade)
base[i0:i2] = 0
base[i0:i0 + len(tail)] += tail
L = int(total / FPS * SR)
out = np.zeros(L + SR, np.float32); vo = np.zeros(L + SR, np.float32); xs = X * SR // FPS
for k, (fa, fb) in enumerate(fr):
    seg = base[fa * SR // FPS: fb * SR // FPS].copy()
    if k > 0: seg[:xs] *= np.linspace(0, 1, xs)
    if k < len(fr) - 1: seg[-xs:] *= np.linspace(1, 0, xs)
    o = starts[k] * SR // FPS; out[o: o + len(seg)] += seg
placed = []
for a, b, kind, aud in ev:
    for t0, f in aud:
        x = rd(f); o = int(map_t(t0) * SR); vo[o: o + len(x)] += x * 0.5
        placed.append([round(map_t(t0), 3), f, round(len(x) / SR, 3)])
for nm, arr in [("alex_track.wav", out[:L]), ("tts_track.wav", vo[:L])]:
    w = wave.open(nm, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(arr, -0.99, 0.99) * 32767).astype(np.int16).tobytes()); w.close()
MODAL, SAY = 147.1, 157.30
vmap = {}
for k, (fa, fb) in enumerate(fr):
    if fa / FPS < MODAL < fb / FPS:  # piece that would show the modal early: freeze from MODAL on
        vmap[k] = [[round(MODAL * FPS) - fa, fa, "play"], [fb - round(MODAL * FPS), round(MODAL * FPS) - 1, "freeze"]]
    if fa / FPS <= SAY < fb / FPS:  # piece where Alex says it: play from just before the modal appears
        off = round((SAY - MODAL) * FPS)
        vmap[k] = [[fb - fa, fa - off, "play"]]
for a, d, wins in replays:
    for k, (fa, fb) in enumerate(fr):
        if fa / FPS <= a < fb / FPS:
            assert str(k) not in vmap and k not in vmap
            fs, fd, fr_ = round(a * FPS), round(d * FPS), round(REPLAY * FPS)
            seg = [[fs - fa, fa, "play"], [fd, fs, "freeze"]] + [[fr_, round(w * FPS), "play"] for w in wins]
            used = sum(x[0] for x in seg)
            seg.append([fb - fa - used, fa + used, "play"])
            assert seg[-1][0] >= 0
            vmap[k] = [x for x in seg if x[0] > 0]
json.dump({"fps": FPS, "x": X, "pieces": fr, "vmap": vmap, "starts": starts, "total_frames": total, "placed": placed,
           "alex": alex}, open("plan.json", "w"), indent=1)
print(f"pieces {len(fr)}  length {total/FPS:.2f}s (src {SRC_END})  lines {len(placed)}")
