"""Generate the 9:16 Reel composition (index.html) from reel.json."""
import json, html

R = json.load(open("reel.json"))
SEGS, WORDS, NAMES = R["segs"], R["words"], R["names"]
DEMO, END = R["demo"], R["end"]
T = round(DEMO + END, 2)
K = 1080 / 1002  # recording px -> screen px at scale 1 (height fills the 1080 window)
RW, RH = round(1338 * K, 1), 1080
r = lambda x: f"{x:.2f}"


def pose(fx, fy, s):
    x = min(0, max(1080 - RW * s, 540 - fx * K * s))
    y = min(0, max(1080 - RH * s, 540 - fy * K * s))
    return x, y


# per-beat step labels (top band)
STEPS = {
    "greet": ("STEP 1", "Just talk to Alex"), "start": ("STEP 1", "Just talk to Alex"),
    "ranch": ("STEP 2", "Describe the job"), "addition": ("STEP 2", "Describe the job"),
    "fields": ("STEP 3", "The scope fills itself in"),
    "generating": ("STEP 4", "Alex builds the estimate"), "total": ("RESULT", "Priced in minutes"),
}

cam_js, step_js = [], []
prev_step = None
for i, sg in enumerate(SEGS):
    a, b = sg["reel"]
    x, y = pose(sg["fx"], sg["fy"], sg["scale"])
    s2 = sg["scale"] * 1.05
    x2, y2 = pose(sg["fx"], sg["fy"], s2)
    cam_js.append(f'      tl.set("#cam", {{ scale: {sg["scale"]}, x: {x:.0f}, y: {y:.0f} }}, {r(a)});')
    cam_js.append(f'      tl.to("#cam", {{ scale: {s2:.3f}, x: {x2:.0f}, y: {y2:.0f}, duration: {r(b - a)}, ease: "none" }}, {r(a)});')
    st = STEPS.get(sg["label"])
    if st and st != prev_step:
        sid = f"st{i}"
        step_js.append((sid, st, a))
        prev_step = st

steps_html = "\n".join(
    f'        <div class="step" id="{sid}"><span class="k">{k}</span><span class="t">{html.escape(t)}</span></div>'
    for sid, (k, t), _ in step_js)
steps_tl = []
for j, (sid, _, a) in enumerate(step_js):
    end = step_js[j + 1][2] if j + 1 < len(step_js) else DEMO
    steps_tl.append(f'      tl.fromTo("#{sid}", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: IN }}, {r(a + 0.05)});')
    steps_tl.append(f'      tl.to("#{sid}", {{ opacity: 0, duration: 0.2, ease: OUT }}, {r(end - 0.2)});')
    steps_tl.append(f'      tl.set("#{sid}", {{ opacity: 0 }}, {r(end)});')

# captions: chunks of <= 3 words, break after punctuation; active word turns gold
hook_end = SEGS[0]["reel"][1]
body = [x for x in WORDS if x["t"] >= hook_end - 0.01]
# hand-set phrase breaks (word counts) so every caption reads as a natural phrase
COUNTS = [3, 5, 4, 5, 5, 4, 4, 5, 4, 4, 4, 2, 4, 2, 3, 3, 2]
assert sum(COUNTS) == len(body), (sum(COUNTS), len(body), [x["w"] for x in body])
chunks, i = [], 0
for n in COUNTS:
    chunks.append(body[i:i + n]); i += n
cap_html, cap_js = [], []
for c, ch in enumerate(chunks):
    start = ch[0]["t"]
    nxt = chunks[c + 1][0]["t"] if c + 1 < len(chunks) else start + 1.4
    end = min(nxt, ch[-1]["t"] + 1.1)
    spans = "".join(f'<span id="w{c}_{k}">{html.escape(w["w"])}</span> ' for k, w in enumerate(ch))
    cap_html.append(f'        <div class="cap" id="c{c}">{spans.strip()}</div>')
    cap_js.append(f'      tl.set("#c{c}", {{ opacity: 1 }}, {r(start)});')
    cap_js.append(f'      tl.set("#c{c}", {{ opacity: 0 }}, {r(end)});')
    for k, w in enumerate(ch):
        cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#d4af37" }}, {r(w["t"])});')
        if k + 1 < len(ch):
            cap_js.append(f'      tl.set("#w{c}_{k}", {{ color: "#ffffff" }}, {r(ch[k + 1]["t"])});')

names_html, names_js = [], []
for j, p in enumerate(NAMES):
    x, y, w, h = (round(v * K, 1) for v in (p["x"], p["y"], p["w"], p["h"]))
    names_html.append(
        f'            <div class="nm" id="nm{j}" data-layout-ignore style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
        f'background:{p["bg"]};color:{p["fg"]};font-size:{round(p["size"] * K, 1)}px;font-weight:{p["weight"]};'
        f'padding-left:{round(p.get("pad", 0) * K, 1)}px">{html.escape(p["text"])}</div>')
    names_js.append(f'      tl.set("#nm{j}", {{ opacity: 1 }}, {r(p["start"])});')
    names_js.append(f'      tl.set("#nm{j}", {{ opacity: 0 }}, {r(p["end"])});')

tot = next(s for s in SEGS if s["label"] == "total")
hook = SEGS[0]["reel"]

doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Hands-Free Estimating Reel 01</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      :root {{
        --navy: #1a1a2e;
        --card: #2d2d44;
        --gold: #d4af37;
        --gray: #a0aab2;
        --white: #ffffff;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: var(--navy); }}
      body {{ font-family: "Inter", sans-serif; color: var(--white); }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--navy); }}
      #bg {{ position: absolute; inset: 0; background: var(--navy); }}
      #top {{ position: absolute; left: 0; top: 96px; width: 1080px; text-align: center; opacity: 0; }}
      #top-logo {{ width: 150px; height: auto; }}
      .step {{ position: absolute; left: 0; top: 250px; width: 1080px; text-align: center; opacity: 0; }}
      .step .k {{ display: block; font-size: 26px; font-weight: 800; letter-spacing: 6px; color: var(--gold); }}
      .step .t {{ display: block; margin-top: 10px; font-size: 52px; font-weight: 900; letter-spacing: -1px; }}
      #screen {{ position: absolute; left: 0; top: 440px; width: 1080px; height: 1080px; overflow: hidden; background: #0e0e18; }}
      #cam {{ position: absolute; left: 0; top: 0; width: {RW}px; height: {RH}px; transform-origin: 0 0; }}
      #rec {{ position: absolute; left: 0; top: 0; width: {RW}px; height: {RH}px; object-fit: fill; }}
      .nm {{ position: absolute; white-space: nowrap; font-family: "Inter", sans-serif; display: flex; align-items: center; opacity: 0; }}
      #dim {{ position: absolute; inset: 0; background: rgba(26, 26, 46, 0.86); opacity: 0; }}
      #hook {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center; gap: 8px; }}
      .hk {{ font-size: 132px; font-weight: 900; letter-spacing: -3px; line-height: 1.02; opacity: 0; }}
      #hk3 {{ margin-top: 30px; font-size: 64px; font-weight: 800; color: var(--gold); opacity: 0; }}
      .cap {{ position: absolute; left: 60px; top: 1560px; width: 960px; text-align: center; font-size: 66px; font-weight: 900;
        letter-spacing: -1px; line-height: 1.1; opacity: 0; text-shadow: 0 4px 18px rgba(0, 0, 0, 0.55); }}
      #callout {{ position: absolute; left: 140px; top: 1290px; width: 800px; padding: 26px 30px; border-radius: 20px;
        background: var(--card); border: 3px solid var(--gold); text-align: center; opacity: 0; }}
      #callout .k {{ font-size: 26px; font-weight: 800; letter-spacing: 5px; color: var(--gold); }}
      #callout .v {{ margin-top: 6px; font-size: 92px; font-weight: 900; letter-spacing: -2px; }}
      #callout .n {{ margin-top: 6px; font-size: 22px; color: var(--gray); }}
      #outro {{ position: absolute; inset: 0; background: var(--navy); }}
      #outro-in {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
      #outro-logo {{ width: 520px; height: auto; }}
      #outro-rule {{ width: 300px; height: 4px; background: var(--gold); margin: 70px 0 56px; }}
      #outro-line {{ font-size: 58px; font-weight: 500; }}
      #outro-cta {{ margin-top: 30px; font-size: 66px; font-weight: 900; color: var(--gold); letter-spacing: 0.5px; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{r(T)}" data-width="1080" data-height="1920">
      <div id="bg" class="clip" data-start="0" data-duration="{r(T)}" data-track-index="0"></div>
      <audio id="mix" src="assets/reel_mix.m4a" data-start="0" data-duration="{r(T)}" data-track-index="10" data-volume="1"></audio>

      <section id="demo">
        <div id="top"><img id="top-logo" src="assets/logo-rail.png" alt="Home Estimator" /></div>
{steps_html}
        <div id="screen">
          <div id="cam" data-layout-allow-overflow>
            <video id="rec" class="clip" src="assets/reel_rec.mp4" data-start="0" data-duration="{r(DEMO)}" data-track-index="3" muted playsinline></video>
{chr(10).join(names_html)}
          </div>
        </div>
        <div id="callout"><div class="k">VERIFIED TOTAL</div><div class="v">$590,279</div><div class="n">Example project &mdash; every project&rsquo;s estimate differs.</div></div>
        <div id="dim"></div>
        <div id="hook">
          <div class="hk" id="hk1">No keyboard.</div>
          <div class="hk" id="hk2">No mouse.</div>
          <div id="hk3">Just a conversation with Alex.</div>
        </div>
{chr(10).join(cap_html)}
      </section>

      <section id="outro" class="clip" data-start="{r(DEMO)}" data-duration="{r(END)}" data-track-index="1">
        <div id="outro-in">
          <img id="outro-logo" src="assets/logo-end.png" alt="Home Estimator" />
          <div id="outro-rule"></div>
          <div id="outro-line">Try our hands-free mode</div>
          <div id="outro-cta">GO TO HOMEESTIMATOR.AI</div>
        </div>
      </section>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      const IN = "power3.out";
      const OUT = "power2.in";

      // hook: dimmed app + kinetic lines, then reveal the app
      tl.set("#dim", {{ opacity: 1 }}, 0);
      tl.fromTo("#hk1", {{ opacity: 0, y: 50 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: IN }}, 0.15);
      tl.fromTo("#hk2", {{ opacity: 0, y: 50 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: IN }}, 1.55);
      tl.fromTo("#hk3", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: IN }}, 2.8);
      tl.to(["#hook", "#dim"], {{ opacity: 0, duration: 0.3, ease: OUT }}, {r(hook[1] - 0.3)});
      tl.set(["#hook", "#dim"], {{ opacity: 0 }}, {r(hook[1])});
      tl.fromTo("#top", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: IN }}, {r(hook[1])});

      // per-beat framing of the app (1080x1080 window), slow push inside each beat
{chr(10).join(cam_js)}

      // step labels
{chr(10).join(steps_tl)}

      // total callout
      tl.fromTo("#callout", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: IN }}, {r(tot["reel"][0] + 1.3)});
      tl.to("#callout", {{ opacity: 0, duration: 0.25, ease: OUT }}, {r(DEMO - 0.25)});
      tl.set("#callout", {{ opacity: 0 }}, {r(DEMO)});

      // captions
{chr(10).join(cap_js)}

      // name patches (Hasnain -> John)
{chr(10).join(names_js)}

      // end card
      tl.fromTo("#outro-logo", {{ opacity: 0, scale: 0.95 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: IN }}, {r(DEMO + 0.05)});
      tl.fromTo("#outro-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: IN }}, {r(DEMO + 0.4)});
      tl.fromTo("#outro-line", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(DEMO + 0.65)});
      tl.fromTo("#outro-cta", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: IN }}, {r(DEMO + 0.9)});

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open("index.html", "w").write(doc)
print("T", T, "captions", len(chunks), "steps", len(step_js), "patches", len(NAMES))
