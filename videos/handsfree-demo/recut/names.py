"""Build names.json: on-screen 'Hasnain' text -> 'John', as timed patches in recording pixels / edit time.

1. group OCR hits (source time, 1 fps) by text + position,
2. refine each group's first/last frame at 30 fps by matching the box pixels to a reference frame,
3. sample background / text colour and size from the reference frame,
4. map source frames to output frames through plan.json (pieces + vmap freeze/replay).
"""
import json, re, subprocess
import numpy as np

SRC = "/root/.claude/uploads/2ff245cc-a70d-5a5f-a4bf-865a59807a5a/a7aa29b7-Hands_free_experience.mp4"
FPS = 30
P = json.load(open("plan.json"))
fr, st, X = P["pieces"], P["starts"], P["x"]
VMAP = {int(k): v for k, v in P.get("vmap", {}).items()}
hits = json.load(open("../socr_hits.json"))


def replace(t):
    t = re.sub(r"^[●•]\s*", "", t)
    t = re.sub(r"Welcome\s*back,\s*Hasn\w*\s*Nas\w*", "Welcome back, John", t)
    t = re.sub(r"Resume:\s*Hasn\w*?(\d+)\W*S?\$?([\d.,]+)\W*$", lambda m: f"Resume: John{m.group(1)} · ${m.group(2).replace('.', ',')} →", t)
    t = re.sub(r"Hasn\w*?(\d+)", r"John\1", t)
    t = re.sub(r"Hasn\w*\s*Nas\w*", "John", t)
    t = re.sub(r"Hasn\w*@", "John@", t)
    t = re.sub(r"Contact:\s*", "Contact: ", t).replace(",CEO", ", CEO").replace("&Founder", "& Founder")
    t = t.replace("Email:", "Email: ").replace("Email:  ", "Email: ")
    return t


def box_of(h):
    b = np.array(h["box"])
    return [b[:, 0].min(), b[:, 1].min(), b[:, 0].max(), b[:, 1].max()]


# 1. group
groups = []
for h in sorted(hits, key=lambda h: h["t"]):
    b = box_of(h)
    key = re.sub(r"\W", "", h["txt"]).lower()[:14]
    for g in groups:
        gb = g["box"]
        if abs(gb[0] - b[0]) < 12 and abs(gb[1] - b[1]) < 8 and abs(gb[3] - b[3]) < 8 and h["t"] - g["times"][-1] <= 2.5:
            g["times"].append(h["t"]); g["txts"].append(h["txt"])
            g["box"] = [min(gb[0], b[0]), min(gb[1], b[1]), max(gb[2], b[2]), max(gb[3], b[3])]
            break
    else:
        groups.append({"box": b, "times": [h["t"]], "txts": [h["txt"]], "key": key})


def frame(t):
    t = min(max(t, 0.05), 525.7)
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t - 0.02:.3f}", "-i", SRC, "-vf",
                          "crop=1338:1002:0:78", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1002, 1338, 3).astype(np.int16)


def clip(img, b, pad=2):
    x0, y0, x1, y1 = (int(round(v)) for v in b)
    return img[max(0, y0 - pad): y1 + pad, max(0, x0 - pad): x1 + pad]


def same(a, b):
    return np.abs(a - b).mean() < 6


def border_bg(img, b):
    x0, y0, x1, y1 = (int(round(v)) for v in b)
    br = np.concatenate([img[y0 - 2, x0:x1], img[y1 + 2, x0:x1], img[y0:y1, x0 - 2], img[y0:y1, x1 + 2]])
    return np.median(br, 0)


def style(img, b):
    x0, y0, x1, y1 = (int(round(v)) for v in b)
    region = img[y0:y1 + 1, x0:x1 + 1].reshape(-1, 3)
    bg = border_bg(img, b)
    dist = np.abs(region - bg).sum(1)
    fgpx = region[dist > np.percentile(dist, 92)]
    fg = np.median(fgpx, 0) if len(fgpx) else np.array([30, 30, 30])
    return bg, fg


import os
out = json.load(open("names_src.json")) if os.path.exists("names_src.json") else []
for g in ([] if out else groups):
    t0, t1 = g["times"][0], g["times"][-1]
    # sample the box background every 0.5 s and split where it changes (e.g. a modal dims the page)
    ts = list(np.arange(t0, t1 + 0.01, 0.5))
    bgs = [border_bg(frame(t), g["box"]) for t in ts]
    segs = [[0, 0]]
    for i in range(1, len(ts)):
        if np.abs(bgs[i] - bgs[segs[-1][0]]).sum() > 18: segs.append([i, i])
        else: segs[-1][1] = i
    for si, (i0, i1) in enumerate(segs):
        tm = ts[(i0 + i1) // 2]
        ref = frame(tm)
        rb = clip(ref, g["box"])
        # refine start/end at 30 fps (outer edges search 1 s; inner edges search back to previous sample)
        s_ = ts[i0]
        for k in range(1, 31 if si == 0 else 16):
            if same(clip(frame(ts[i0] - k / FPS), g["box"]), rb): s_ = ts[i0] - k / FPS
            else: break
        e_ = ts[i1]
        for k in range(1, 31 if si == len(segs) - 1 else 16):
            if same(clip(frame(ts[i1] + k / FPS), g["box"]), rb): e_ = ts[i1] + k / FPS
            else: break
        bg, fg = style(ref, g["box"])
        x0, y0, x1, y1 = (int(round(v)) for v in g["box"])
        txt = max(set(g["txts"]), key=g["txts"].count)
        out.append({"src": [round(s_, 3), round(e_ + 1 / FPS, 3)], "x": x0 - 2, "y": y0 - 2, "w": x1 - x0 + 4,
                    "h": y1 - y0 + 4, "bg": "rgb(%d,%d,%d)" % tuple(bg), "fg": "rgb(%d,%d,%d)" % tuple(fg),
                    "size": round((y1 - y0) * 0.78, 1), "weight": 600, "ocr": txt, "text": replace(txt)})


json.dump(out, open("names_src.json", "w"), indent=1, default=float)


# 4. map to output frames
def out_frames_for(src_a, src_b):
    fa_src, fb_src = round(src_a * FPS), round(src_b * FPS)
    vis = []
    for k, (fa, fb) in enumerate(fr):
        segs = VMAP.get(k, [[fb - fa, fa, "play"]])
        pos = 0
        for n, s0, mode in segs:
            for i in range(n):
                sf = s0 + (i if mode == "play" else 0)
                if fa_src <= sf < fb_src:
                    vis.append(st[k] + pos + i)
            pos += n
    vis = sorted(set(vis))
    iv = []
    for f in vis:
        if iv and f <= iv[-1][1] + 1: iv[-1][1] = f
        else: iv.append([f, f])
    return iv


patches = []
for o in out:
    for a, b in out_frames_for(*o["src"]):
        p = dict(o); p["start"] = round(a / FPS, 3); p["end"] = round((b + 1) / FPS, 3)
        patches.append(p)
json.dump(patches, open("names.json", "w"), indent=1)
for o in out:
    print(o["src"], o["ocr"], "->", o["text"], o["size"], o["weight"], o["bg"], o["fg"])
print(len(patches), "timed patches")
