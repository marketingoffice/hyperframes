"""Cut edited4.mp4 per plan.json into recording_new.mp4 (0.2 s dissolves at trims)."""
import json, os, subprocess

P = json.load(open("plan.json"))
FPS, X, fr = P["fps"], P["x"], P["pieces"]
SRC = "/root/.claude/uploads/2ff245cc-a70d-5a5f-a4bf-865a59807a5a/a7aa29b7-Hands_free_experience.mp4"
CROP = "crop=1338:1002:0:78"
os.makedirs("vp", exist_ok=True)
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p",
       "-r", str(FPS), "-video_track_timescale", "15360", "-an"]


def run(args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + args, check=True)


def body(fa, n, out):
    run(["-ss", f"{fa / FPS - 0.02:.6f}", "-i", SRC, "-vf", CROP, "-frames:v", str(n)] + ENC + [out])


files = []
for k, (fa, fb) in enumerate(fr):
    a = fa + (X if k > 0 else 0)
    b = fb - (X if k < len(fr) - 1 else 0)
    out = f"vp/b{k:03d}.mp4"
    body(a, b - a, out)
    files.append(out)
    if k < len(fr) - 1:
        na = fr[k + 1][0]
        out = f"vp/x{k:03d}.mp4"
        run(["-ss", f"{(fb - X) / FPS - 0.02:.6f}", "-i", SRC, "-ss", f"{na / FPS - 0.02:.6f}", "-i", SRC,
             "-filter_complex",
             f"[0:v]trim=end_frame={X},setpts=PTS-STARTPTS[a];[1:v]trim=end_frame={X},setpts=PTS-STARTPTS[b];"
             f"[a]{CROP}[a2];[b]{CROP}[b2];[a2][b2]xfade=transition=fade:duration={X / FPS}:offset=0,trim=end_frame={X}[v]",
             "-map", "[v]", "-frames:v", str(X)] + ENC + [out])
        files.append(out)
with open("vp/list.txt", "w") as f:
    for p in files:
        f.write(f"file '{os.path.basename(p)}'\n")
run(["-f", "concat", "-safe", "0", "-i", "vp/list.txt", "-c", "copy", "-movflags", "+faststart", "recording_new.mp4"])
n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                    "stream=nb_read_frames", "-of", "csv=p=0", "recording_new.mp4"], capture_output=True, text=True).stdout.strip()
print("frames", n, "expected", P["total_frames"])
