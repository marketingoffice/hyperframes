"""Cut the source per plan.json into recording_new.mp4 (0.2 s dissolves at trims).

Each piece plays source frames [fa, fb) unless plan["vmap"][k] remaps it into
[n_frames, src_frame, "play" | "freeze"] segments (used to hold a frame so an on-screen
change lands on the line that announces it).
"""
import json, os, subprocess

P = json.load(open("plan.json"))
FPS, X, fr = P["fps"], P["x"], P["pieces"]
VMAP = {int(k): v for k, v in P.get("vmap", {}).items()}
SRC = "/root/.claude/uploads/2ff245cc-a70d-5a5f-a4bf-865a59807a5a/a7aa29b7-Hands_free_experience.mp4"
CROP = "crop=1338:1002:0:78"
OFF = 0.02  # video stream starts 23 ms after audio
os.makedirs("vp", exist_ok=True)
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p",
       "-r", str(FPS), "-video_track_timescale", "15360", "-an"]


def run(args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + args, check=True)


def segs(k):
    fa, fb = fr[k]
    return VMAP.get(k, [[fb - fa, fa, "play"]])


def frames_of(k, i0, i1):
    """[(n, src_frame, mode)] covering output frames i0..i1 of piece k."""
    out, pos = [], 0
    for n, s, mode in segs(k):
        a, b = max(i0, pos), min(i1, pos + n)
        if a < b:
            out.append([b - a, s + (a - pos if mode == "play" else 0), mode])
        pos += n
    return out


def encode(parts, out):
    tmp = []
    for j, (n, s, mode) in enumerate(parts):
        t = f"{out}.{j}.mp4"
        if mode == "play":
            run(["-ss", f"{s / FPS - OFF:.6f}", "-i", SRC, "-vf", CROP, "-frames:v", str(n)] + ENC + [t])
        else:
            run(["-ss", f"{s / FPS - OFF:.6f}", "-i", SRC, "-vf",
                 f"{CROP},trim=end_frame=1,tpad=stop_mode=clone:stop={n - 1}", "-frames:v", str(n)] + ENC + [t])
        tmp.append(t)
    if len(tmp) == 1:
        os.replace(tmp[0], out)
    else:
        with open(out + ".txt", "w") as f:
            f.writelines(f"file '{os.path.basename(t)}'\n" for t in tmp)
        run(["-f", "concat", "-safe", "0", "-i", out + ".txt", "-c", "copy", out])


files = []
for k, (fa, fb) in enumerate(fr):
    n = fb - fa
    a = X if k > 0 else 0
    b = n - (X if k < len(fr) - 1 else 0)
    out = f"vp/b{k:03d}.mp4"
    encode(frames_of(k, a, b), out)
    files.append(out)
    if k < len(fr) - 1:
        ta, tb = f"vp/ta{k:03d}.mp4", f"vp/tb{k:03d}.mp4"
        encode(frames_of(k, n - X, n), ta)
        encode(frames_of(k + 1, 0, X), tb)
        out = f"vp/x{k:03d}.mp4"
        run(["-i", ta, "-i", tb, "-filter_complex",
             f"[0:v][1:v]xfade=transition=fade:duration={X / FPS}:offset=0,trim=end_frame={X}[v]",
             "-map", "[v]", "-frames:v", str(X)] + ENC + [out])
        files.append(out)
with open("vp/list.txt", "w") as f:
    for p in files:
        f.write(f"file '{os.path.basename(p)}'\n")
run(["-f", "concat", "-safe", "0", "-i", "vp/list.txt", "-c", "copy", "-movflags", "+faststart", "recording_new.mp4"])
n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                    "stream=nb_read_frames", "-of", "csv=p=0", "recording_new.mp4"], capture_output=True, text=True).stdout.strip()
print("frames", n, "expected", P["total_frames"])
