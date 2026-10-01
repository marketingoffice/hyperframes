"""Generate handsfree-demo/index.html; all edit-time cues are given in SOURCE seconds and mapped through plan.json."""
import json, os

P = json.load(open("plan.json"))
FPS, fr, st = P["fps"], P["pieces"], P["starts"]
N = P["total_frames"] / FPS

# opening: hook line (John: "...never touched the keyboard or the mouse...") then title card
H0 = 0.6  # hook VO start
HOOK_VO = 7.63
HK = [H0 + 2.76, H0 + 3.64, H0 + 5.96]  # "keyboard", "mouse", "just by having a normal conversation"
HOOK_OUT = H0 + HOOK_VO + 0.45
TITLE_START = HOOK_OUT + 0.25
V = round(TITLE_START + 2.9, 2)  # demo (recording) starts here
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
W, H, K = 1442, 1080, 1442 / 1338


def pose(px, py, s):
    x = min(0, max(W - s * W, W / 2 - s * px * K))
    y = min(0, max(H - s * H, H / 2 - s * py * K))
    return f"{{ scale: {s}, x: {x:.0f}, y: {y:.0f} }}"


FULL = "{ scale: 1, x: 0, y: 0 }"
SCOPE = pose(640, 720, 1.4)
TOTAL = pose(1130, 40, 1.7)
ADDONS = pose(330, 900, 1.6)
moves = [  # (source time, pose, duration)
    (116.5, SCOPE, 1.2), (157.0, FULL, 1.0), (210.0, TOTAL, 1.2), (219.6, FULL, 1.0),
    (349.6, ADDONS, 1.2), (365.8, FULL, 1.0), (507.0, TOTAL, 1.2), (519.6, FULL, 1.2),
]
moves_js = ",\n".join(f"        [{r(m(t))}, {ps}, {d}]" for t, ps, d in moves)

EX = '<div class="n">Example project &mdash; every project&rsquo;s estimate differs.</div>'
caps = [  # (id, source time, kicker, title html, extra)
    ("k1", 0.3, "01 &middot; THE TASK", "An addition + remodel estimate, by voice", ""),
    ("k2", 44.6, "02 &middot; HANDS-FREE START", "Alex opens a new project", ""),
    ("k3", 66.0, "03 &middot; DESCRIBE THE JOB", "The scope fills in as John talks", ""),
    ("k3b", 133.6, "03 &middot; SCOPE CAPTURED", "Ranch &middot; 1,100 sq ft addition &middot; gut-to-studs remodel", ""),
    ("k4", 157.3, "04 &middot; ESTIMATE", "Alex generates the estimate", ""),
    ("k4b", 210.1, "04 &middot; VERIFIED TOTAL", "Estimate ready: <b>$590,279</b>", EX),
    ("k5", 219.9, "05 &middot; REVIEW BY VOICE", "Scope, HVAC detail, payments, contract", ""),
    ("k6", 321.7, "06 &middot; ADJUST BY VOICE", "Kitchen add-ons, hardwood, primary bath, siding", ""),
    ("k7", 507.1, "07 &middot; UPDATED TOTAL", "Re-priced in place: <b>$606,982</b>", EX),
]
CAP_HOLD = 5.5
caps_html = "\n".join(
    f'          <div class="cap" id="{i}"><div class="k">{k}</div><div class="t">{t}</div>{x}</div>' for i, _, k, t, x in caps)
caps_js = ["      // chapter subtitles: slide up, hold, slide down"]
for i, s, *_ in caps:
    a = m(s)
    caps_js.append(f'      tl.fromTo("#{i}", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, V + {r(a)});')
    caps_js.append(f'      tl.to("#{i}", {{ opacity: 0, y: 20, duration: 0.35, ease: OUT }}, V + {r(a + CAP_HOLD)});')

# on-screen name patches (from OCR), coordinates in recording pixels
names_html, names_js = [], []
if os.path.exists("names.json"):
    for j, p in enumerate(json.load(open("names.json"))):
        x, y, w, h = (round(v * K, 1) for v in (p["x"], p["y"], p["w"], p["h"]))
        names_html.append(
            f'            <div class="nm" id="nm{j}" data-layout-ignore style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
            f'background:{p["bg"]};color:{p["fg"]};font-size:{round(p["size"] * K, 1)}px;font-weight:{p["weight"]};'
            f'justify-content:{p.get("align", "flex-start")};padding-left:{round(p.get("pad", 0) * K, 1)}px">{p["text"]}</div>')
        names_js.append(f'      tl.set("#nm{j}", {{ opacity: 1 }}, V + {r(p["start"])});')
        names_js.append(f'      tl.set("#nm{j}", {{ opacity: 0 }}, V + {r(p["end"])});')

html = open("index.tpl.html").read()
for k, v in {
    "{{T}}": r(T), "{{N}}": r(N), "{{OUT}}": r(V + N), "{{MOVES}}": moves_js, "{{V}}": r(V),
    "{{DRIFT}}": r(m(19.0) - 1.0), "{{FADE}}": r(V + N - 0.5),
    "{{O1}}": r(V + N + 0.1), "{{O2}}": r(V + N + 0.6), "{{O3}}": r(V + N + 0.9), "{{O4}}": r(V + N + 1.15),
    "{{HOOK_END}}": r(HOOK_OUT + 0.4), "{{HOOK_OUT}}": r(HOOK_OUT), "{{HK1}}": r(HK[0]), "{{HK2}}": r(HK[1]),
    "{{HK3}}": r(HK[2]), "{{TITLE_START}}": r(TITLE_START), "{{TITLE_DUR}}": r(V - TITLE_START),
    "{{CAPS}}": caps_html, "{{CAPS_JS}}": "\n".join(caps_js),
    "{{NAMES}}": "\n".join(names_html), "{{NAMES_JS}}": "\n".join(names_js) or "      // (no name patches)",
}.items():
    html = html.replace(k, v)
open("index.html", "w").write(html)
json.dump({"V": V, "H0": H0, "N": N, "T": T}, open("timing.json", "w"))
print("V", r(V), "N", r(N), "T", r(T), "patches", len(names_html))
for i, s, *_ in caps:
    print(i, s, "->", r(m(s)))
