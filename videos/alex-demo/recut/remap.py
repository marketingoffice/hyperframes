"""Rewrite the composition's edit-time constants through the new cut (plan.json)."""
import json, re
P = json.load(open("plan.json")); FPS = P["fps"]; fr = P["pieces"]; st = P["starts"]
N = P["total_frames"] / FPS
def m(t):
    f = t * FPS
    for k, (fa, fb) in enumerate(fr):
        if f < fa: return st[k] / FPS
        if f <= fb: return (st[k] + f - fa) / FPS
    return N
r = lambda x: f"{x:.2f}"
h = open("index_v1.html").read()
V = 3
T = V + N + 8.5
h = h.replace('data-duration="315.53"', f'data-duration="{r(T)}"')
h = h.replace('data-duration="304.03"', f'data-duration="{r(N)}"')
h = h.replace("CLOSING CARD 307.03–315.53", f"CLOSING CARD {r(V+N)}–{r(T)}")
h = h.replace('data-start="307.03"', f'data-start="{r(V+N)}"')
# chapters
def chap(mo):
    return f'["{mo.group(1)}", "{mo.group(2)}", {r(m(float(mo.group(3))))}]'
h = re.sub(r'\["(#c\w+)", "(#pg\d)", ([\d.]+)\]', chap, h)
h = h.replace("V + 226.3", f"V + {r(m(226.3))}")
# intro drift: V+1.0 for 41.5s -> ends at mapped 42.5
h = h.replace("duration: 41.5,", f"duration: {r(m(42.5) - 1.0)},")
def mv(mo):
    return f"[{r(m(float(mo.group(1))))}, {mo.group(2)}, {mo.group(3)}]"
h = re.sub(r"\[([\d.]+), (FULL|PANEL|SCOPE|FORM|RESULT|CONSULT), ([\d.]+)\]", mv, h)
for old, off in [("306.53", -0.5), ("307.03", 0), ("307.13", 0.1), ("307.63", 0.6), ("307.93", 0.9), ("308.18", 1.15), ("308.43", 1.4)]:
    h = h.replace(f", {old});", f", {r(V + N + off)});")
open("index_new.html", "w").write(h)
print("N", r(N), "T", r(T))
for t in [44.2, 60.1, 90, 131.5, 151, 196, 226, 227, 240, 265.5, 272.6, 273.8, 274.2, 284, 285.5, 288, 298.6]:
    print(t, "->", r(m(t)))
