"""Generate handsfree-demo/index.html; all edit-time cues are given in SOURCE seconds and mapped through plan.json."""
import json

P = json.load(open("plan.json"))
FPS, fr, st = P["fps"], P["pieces"], P["starts"]
N = P["total_frames"] / FPS
V = 3.0
T = V + N + 8.5


def m(t):
    f = t * FPS
    for k, (fa, fb) in enumerate(fr):
        if f < fa:
            return st[k] / FPS
        if f <= fb:
            return (st[k] + f - fa) / FPS
    return N


r = lambda x: f"{x:.2f}"
W, H, K = 1258, 942, 1258 / 1338


def pose(px, py, s):
    x = min(0, max(W - s * W, W / 2 - s * px * K))
    y = min(0, max(H - s * H, H / 2 - s * py * K))
    return f"{{ scale: {s}, x: {x:.0f}, y: {y:.0f} }}"


FULL = "{ scale: 1, x: 0, y: 0 }"
SCOPE = pose(640, 720, 1.4)
TOTAL = pose(1130, 40, 1.7)
ADDONS = pose(330, 900, 1.6)

chapters = [  # (id, progress tick, source time)
    ("c1", 1, 0.0), ("c2", 2, 44.6), ("c3", 3, 63.0), ("c3b", 3, 133.6), ("c4", 4, 157.2), ("c4b", 4, 210.1),
    ("c5", 5, 219.9), ("c6", 6, 321.7), ("c7", 7, 487.0), ("c7b", 7, 507.1),
]
moves = [  # (source time, pose, duration)
    (116.5, SCOPE, 1.2), (157.0, FULL, 1.0), (210.0, TOTAL, 1.2), (219.6, FULL, 1.0),
    (349.6, ADDONS, 1.2), (365.8, FULL, 1.0), (507.0, TOTAL, 1.2), (519.6, FULL, 1.2),
]
chap_js = ",\n".join(f'        ["#{c}", "#pg{p}", {r(m(t))}]' for c, p, t in chapters)
moves_js = ",\n".join(f"        [{r(m(t))}, {ps}, {d}]" for t, ps, d in moves)

html = open("index.tpl.html").read()
for k, v in {
    "{{T}}": r(T), "{{N}}": r(N), "{{OUT}}": r(V + N), "{{CHAPTERS}}": chap_js, "{{MOVES}}": moves_js,
    "{{DRIFT}}": r(m(19.0) - 1.0), "{{LIST}}": r(m(134.5)), "{{FADE}}": r(V + N - 0.5),
    "{{O1}}": r(V + N + 0.1), "{{O2}}": r(V + N + 0.6), "{{O3}}": r(V + N + 0.9), "{{O4}}": r(V + N + 1.15),
    "{{O5}}": r(V + N + 1.4),
}.items():
    html = html.replace(k, v)
open("index.html", "w").write(html)
print("N", r(N), "T", r(T))
for c, p, t in chapters:
    print(c, t, "->", r(m(t)))
