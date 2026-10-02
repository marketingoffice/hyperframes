"""Reel 01 (9:16, ~30 s): cut the v2 hands-free edit into story beats, build audio, captions and name patches."""
import json, subprocess, wave
import numpy as np

RE = "/tmp/claude-0/hf/re"
FPS, SR = 30, 48000
HOOK_LEN = 3.95  # "In this whole experience, we never touched the keyboard or the mouse."
# (edit-time start, end, focus_x, focus_y, scale, label) — focus in recording px (1338x1002)
SEGS = [
    (0.20, 0.20 + HOOK_LEN, 669, 501, 1.0, "hook"),       # dashboard behind the hook text (muted)
    (21.25, 25.30, 1000, 420, 1.0, "greet"),             # Alex: Hi, I'm Alex ... start a new one?
    (26.38, 27.78, 1000, 420, 1.0, "start"),             # John: Let's start a new one.
    (34.38, 38.60, 640, 560, 1.0, "ranch"),              # John: ranch house, 1,200 sq ft
    (38.82, 42.85, 640, 560, 1.0, "addition"),           # John: second-level addition, 1,100 sq ft
    (59.40, 61.55, 600, 690, 1.15, "fields"),            # fields fill in; Alex: Okay. Thanks.
    (84.32, 88.00, 669, 430, 1.0, "generating"),         # John: That would be good. Alex: generating...
    (92.78, 96.60, 1130, 40, 1.9, "total"),              # Alex: Your verified total is $590,279.
]
END_LEN = 3.6


def run(a):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + a, check=True)


# 1. video: frame-accurate cuts from the v2 recording, concatenated
parts, t, segs_out = [], 0.0, []
for i, (a, b, fx, fy, s, lab) in enumerate(SEGS):
    fa, fb = round(a * FPS), round(b * FPS)
    out = f"v{i}.mp4"
    run(["-ss", f"{fa / FPS:.6f}", "-i", f"{RE}/recording_new.mp4", "-frames:v", str(fb - fa), "-an",
         "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "30",
         "-video_track_timescale", "15360", out])
    parts.append(out)
    segs_out.append({"label": lab, "edit": [fa / FPS, fb / FPS], "reel": [round(t, 3), round(t + (fb - fa) / FPS, 3)],
                     "fx": fx, "fy": fy, "scale": s})
    t += (fb - fa) / FPS
open("vlist.txt", "w").writelines(f"file '{p}'\n" for p in parts)
run(["-f", "concat", "-safe", "0", "-i", "vlist.txt", "-c", "copy", "reel_rec.mp4"])
DEMO = t


# 2. voices: same ranges from the levelled v2 voice track; hook from the levelled hook line
def rd(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x.reshape(-1, w.getnchannels()).mean(1) if w.getnchannels() > 1 else x


vo, hook = rd(f"{RE}/vo_new.wav"), rd(f"{RE}/hook.wav")
out = np.zeros(int((DEMO + END_LEN) * SR) + SR, np.float32)
fade = int(0.012 * SR)
for sg in segs_out:
    a, b = sg["edit"]; o = int(sg["reel"][0] * SR)
    x = hook[:int(HOOK_LEN * SR)].copy() if sg["label"] == "hook" else vo[int(a * SR): int(b * SR)].copy()
    x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
    out[o: o + len(x)] += x
w = wave.open("reel_vo.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out[: int((DEMO + END_LEN) * SR)], -0.99, 0.99) * 32767).astype(np.int16).tobytes()); w.close()

# 3. captions: words from the transcript of the v2 voice track (+ the hook line's own word times)
W = json.load(open(f"{RE}/vo_new_words.json"))
hook_words = [("In", .04), ("this", .28), ("whole", .52), ("experience,", .84), ("we", 1.64), ("never", 1.88),
              ("touched", 2.12), ("the", 2.6), ("keyboard", 2.76), ("or", 3.32), ("the", 3.48), ("mouse.", 3.64)]
words = [{"w": w, "t": round(t0, 2)} for w, t0 in hook_words]
for sg in segs_out[1:]:
    a, b = sg["edit"]
    for x in W:
        if a <= x["s"] < b - 0.05:
            words.append({"w": x["w"], "t": round(sg["reel"][0] + x["s"] - a, 2)})
fix = {"1200": "1,200", "1100": "1,100"}
for x in words:
    x["w"] = fix.get(x["w"].strip(".,"), x["w"]) + ("," if x["w"].endswith(",") and x["w"].strip(".,") in fix else "")

# 4. name patches (Hasnain -> John) that fall inside the chosen ranges, shifted to reel time
names = []
for p in json.load(open(f"{RE}/names.json")):
    for sg in segs_out[1:]:
        a, b = sg["edit"]
        s, e = max(p["start"], a), min(p["end"], b)
        if s < e:
            q = dict(p); q["start"] = round(sg["reel"][0] + s - a, 3); q["end"] = round(sg["reel"][0] + e - a, 3)
            names.append(q)
json.dump({"segs": segs_out, "words": words, "names": names, "demo": DEMO, "end": END_LEN},
          open("reel.json", "w"), indent=1)
print(f"demo {DEMO:.2f}s + end {END_LEN}s = {DEMO + END_LEN:.2f}s | words {len(words)} | name patches {len(names)}")
for sg in segs_out:
    print(sg["label"], sg["reel"])
