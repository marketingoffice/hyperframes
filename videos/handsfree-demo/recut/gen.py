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
W, K = 1920, 1920 / 1338  # recording scaled to full width; 1438 px tall, cropped to 1080 by a per-scene offset


def ps(src):
    """edit time where the piece starting at source time `src` begins"""
    k = min(range(len(fr)), key=lambda k: abs(fr[k][0] / FPS - src))
    return st[k] / FPS


# vertical framing (recording px from the top, 0..249), chosen per scene; changes land on cuts only
FRAMING = [(0, 0), (54.5, 249), (156, 170), (200, 0), (332, 249), (388, 125), (495, 0)]  # (source time >=, offset)


def oy_of(src):
    return [o for t, o in FRAMING if src >= t][-1]


frames_js, cur = [], None
for k, (fa, fb) in enumerate(fr):
    o = oy_of(fa / FPS)
    if o != cur:
        t = 0 if k == 0 else st[k] / FPS + 0.1  # middle of the 0.2 s dissolve
        frames_js.append(f'      tl.set("#cam", {{ y: {-o * K:.0f} }}, V + {r(t)});')
        cur = o
OY = {k: oy_of(a / FPS) for k, (a, b) in enumerate(fr)}

# highlight boxes: (id, rect in recording px, edit start, edit end)
BOXES = [
    ("hl-scope", (188, 618, 996, 212), ps(133.33) + 0.25, ps(156.9) - 0.1),
    ("hl-total1", (1095, 3, 92, 46), m(210.2) - 0.1, m(219.4)),
    ("hl-addons", (198, 885, 332, 104), 153.07 + 0.3, m(365.3)),
    ("hl-siding", (184, 508, 356, 340), ps(423.73) + 0.3, 217.6),
    ("hl-total2", (842, 3, 90, 46), m(507.2), m(519.4)),
]
PAD = 7
boxes_html, boxes_js = [], ["      // fade in, hold while it is discussed, fade out"]
for i_, (x, y, w, h), a, b in BOXES:
    x0, y0 = max(2, x - PAD), max(2, y - PAD)
    x1, y1 = min(1336, x + w + PAD), min(1000, y + h + PAD)
    boxes_html.append(f'            <div class="hl" id="{i_}" data-layout-ignore style="left:{x0 * K:.0f}px;top:{y0 * K:.0f}px;'
                      f'width:{(x1 - x0) * K:.0f}px;height:{(y1 - y0) * K:.0f}px"></div>')
    boxes_js.append(f'      tl.fromTo("#{i_}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: IN }}, V + {r(a)});')
    boxes_js.append(f'      tl.to("#{i_}", {{ opacity: 0, duration: 0.3, ease: OUT }}, V + {r(b - 0.3)});')
    boxes_js.append(f'      tl.set("#{i_}", {{ opacity: 0 }}, V + {r(b)});')

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
    ("k7", 507.1, "07 &middot; UPDATED TOTAL", "Updated price: <b>$606,982</b>", EX),
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
    "{{T}}": r(T), "{{N}}": r(N), "{{OUT}}": r(V + N), "{{V}}": r(V), "{{FADE}}": r(V + N - 0.5),
    "{{FRAMES_JS}}": "\n".join(frames_js), "{{BOXES}}": "\n".join(boxes_html), "{{BOXES_JS}}": "\n".join(boxes_js),
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
