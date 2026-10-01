"""Word-coverage audit: every speech frame in the original VO must be kept (Alex) or re-voiced (presenter).

Usage (from the work dir, after build.py): python3 audit.py u_ 0.7
Prints any uncovered speech runs >= 30 ms; then scans kept Alex audio for presenter-like voice.
"""
import sys
import numpy as np
from scipy.ndimage import uniform_filter1d

g = {}
exec(open("build.py").read().split("# ---- audio ----")[0], g)
alex, BLOCKS, fr, events = g["alex"], g["BLOCKS"], g["fr"], g["events"]
db, pA = np.load("../db.npy"), np.load("../pA.npy")
th = np.percentile(db, 30) + 12
n = len(db)
inpiece = np.zeros(n, bool)
for fa, fb in fr:
    inpiece[int(fa / 30 * 100): int(fb / 30 * 100)] = True
hs = [(e[0], e[1]) for e in events if e[2] == "tts"] + [(a, b) for a, b, _ in BLOCKS]
alexwin = np.zeros(n, bool)
for a, b in alex:
    lo, hi = a - 0.12, b + 0.28
    for ha, hb in hs:
        if hb <= a and hb > lo: lo = hb + 0.02
        if ha >= b and ha < hi: hi = ha - 0.02
    alexwin[int(lo * 100): int(hi * 100)] = True
hb = np.zeros(n, bool)
for a, b, _ in BLOCKS:
    hb[int(a * 100): int(b * 100)] = True
hb[: int(60.7 * 100)] = True  # intro fully re-voiced
miss = (db > th - 8) & ~((alexwin & inpiece) | hb)
i = 0
while i < n:
    if miss[i]:
        j = i
        while j < n and miss[j]: j += 1
        if j - i >= 3:
            print(f"UNCOVERED src {i/100:.2f}-{j/100:.2f} ({(j-i)*10} ms) pAlex={pA[i:j].mean():.2f}")
        i = j
    else:
        i += 1
p = uniform_filter1d(pA, 20)
for a, b in alex:
    i, j = int(a * 100), int(b * 100)
    hz = (p[i:j] < 0.35) & (db[i:j] > th)
    if hz.sum() >= 15:
        print(f"CHECK presenter-like frames inside Alex segment {a:.2f}-{b:.2f}")
print("audit done")
