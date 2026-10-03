"""Generate handsfree-demo/index.html; all edit-time cues are given in SOURCE seconds and mapped through plan.json."""
import json, os

P = json.load(open("plan.json"))
FPS, fr, st = P["fps"], P["pieces"], P["starts"]
N = P["total_frames"] / FPS

# opening: hook line (John: "...never touched the keyboard or the mouse...") then title card
H0 = 0.6  # hook VO start ("Building plans, then waiting on bids ... No keyboard, no mouse.")
HOOK_VO = 13.79
# word times in the hook take (Parakeet), relative to H0
HW = {"building": 0.0, "bids": 1.84, "three": 3.10, "before": 4.22, "with": 7.11, "ten": 9.11,
      "just": 10.16, "keyboard": 12.08, "mouse": 13.04}
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


# reframe on the first frame of the next screen, not mid-screen: in the window from the cut to the
# next reframe, find the largest frame-to-frame change in recording_new.mp4
import subprocess
import numpy as np

_raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", "recording_new.mp4", "-vf", "scale=96:72",
                       "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
DIFF = np.abs(np.diff(np.frombuffer(_raw, np.uint8).reshape(-1, 72, 96).astype(np.int16), axis=0)).mean((1, 2))

bounds, cur = [], None
for k, (fa, fb) in enumerate(fr):
    o = oy_of(fa / FPS)
    if o != cur:
        bounds.append((k, o))
        cur = o
frames_js = []
for j, (k, o) in enumerate(bounds):
    if k == 0:
        t = 0.0
    else:
        f0 = st[k] - 3  # just before the dissolve
        f1 = f0 + int(1.6 * FPS)  # the next screen arrives within ~1.5 s of the cut
        f = f0 + 1 + int(np.argmax(DIFF[f0:f1]))  # first frame of the new screen
        t = f / FPS - 0.5 / FPS
    frames_js.append(f'      tl.set("#cam", {{ y: {-o * K:.0f} }}, V + {r(t)});')
OY = {k: oy_of(a / FPS) for k, (a, b) in enumerate(fr)}

PL = {f: t for t, f, d in P["placed"]}  # edit time of each re-voiced line
# highlight boxes: (id, rect in recording px, edit start, edit end)
BOXES = [
    ("hl-scope", (188, 618, 996, 212), ps(133.33) + 0.25, ps(156.9) - 0.1),
    ("hl-total1", (1095, 3, 92, 46), m(210.2) - 0.1, m(219.4)),
    ("hl-addons", (198, 885, 332, 104), PL["n15.wav"] + 0.3, m(365.3)),
    ("hl-siding", (184, 508, 356, 340), ps(423.73) + 0.3, PL["n19.wav"] - 0.1),
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


def hk(w, d=-0.08):
    return r(H0 + HW[w] + d)


IN_ = "{ opacity: 1, y: 0, duration: 0.45, ease: IN }"
hook_js = "\n".join([
    "      // hook beat 1: the old way",
    f'      tl.fromTo("#hp1", {{ opacity: 0, y: 30 }}, {IN_}, {hk("building", 0.0)});',
    f'      tl.fromTo("#hpa", {{ opacity: 0, x: -16 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: IN }}, {hk("bids", -0.45)});',
    f'      tl.fromTo("#hp2", {{ opacity: 0, y: 30 }}, {IN_}, {hk("bids", -0.3)});',
    f'      tl.fromTo("#hm", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: IN }}, {hk("three")});',
    f'      tl.fromTo("#hsub", {{ opacity: 0, y: 20 }}, {IN_}, {hk("before")});',
    "      // hook beat 2: strike the months, land the minutes",
    f'      tl.fromTo("#hstrike", {{ opacity: 1, scaleX: 0 }}, {{ scaleX: 1, duration: 0.45, ease: "power2.inOut" }}, {hk("with")});',
    f'      tl.to(["#hm", "#hp1", "#hp2", "#hpa", "#hsub"], {{ opacity: 0.35, duration: 0.45, ease: OUT }}, {hk("with")});',
    f'      tl.fromTo("#h10-k", {{ opacity: 0, y: 16 }}, {IN_}, {hk("with", 0.3)});',
    f'      tl.fromTo("#h10", {{ opacity: 0, y: 40, scale: 0.96 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.55, ease: IN }}, {hk("ten", -0.25)});',
    "      // hook beat 3: one conversation, hands-free",
    f'      tl.to("#hookA", {{ opacity: 0, y: -30, duration: 0.35, ease: OUT }}, {hk("just", -0.4)});',
    f'      tl.set("#hookA", {{ opacity: 0 }}, {hk("just", -0.05)});',
    f'      tl.fromTo("#hc1", {{ opacity: 0, y: 30 }}, {IN_}, {hk("just")});',
    f'      tl.fromTo("#hk1", {{ opacity: 0, y: 40 }}, {IN_}, {hk("keyboard")});',
    f'      tl.fromTo("#hk2", {{ opacity: 0, y: 40 }}, {IN_}, {hk("mouse")});',
])

html = open("index.tpl.html").read()
for k, v in {
    "{{T}}": r(T), "{{N}}": r(N), "{{OUT}}": r(V + N), "{{V}}": r(V), "{{FADE}}": r(V + N - 0.5),
    "{{FRAMES_JS}}": "\n".join(frames_js), "{{BOXES}}": "\n".join(boxes_html), "{{BOXES_JS}}": "\n".join(boxes_js),
    "{{O1}}": r(V + N + 0.1), "{{O2}}": r(V + N + 0.6), "{{O3}}": r(V + N + 0.9), "{{O4}}": r(V + N + 1.15),
    "{{HOOK_END}}": r(HOOK_OUT + 0.4), "{{HOOK_OUT}}": r(HOOK_OUT), "{{HOOK_JS}}": hook_js, "{{TITLE_START}}": r(TITLE_START), "{{TITLE_DUR}}": r(V - TITLE_START),
    "{{CAPS}}": caps_html, "{{CAPS_JS}}": "\n".join(caps_js),
    "{{NAMES}}": "\n".join(names_html), "{{NAMES_JS}}": "\n".join(names_js) or "      // (no name patches)",
}.items():
    html = html.replace(k, v)
open("index.html", "w").write(html)
json.dump({"V": V, "H0": H0, "N": N, "T": T}, open("timing.json", "w"))
print("V", r(V), "N", r(N), "T", r(T), "patches", len(names_html))
for i, s, *_ in caps:
    print(i, s, "->", r(m(s)))
