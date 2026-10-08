import re, sys, shutil, os
src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst + "/assets", exist_ok=True)
for f in ["assets/gsap.min.js", "assets/logo.png", "assets/audio.m4a", "hyperframes.json", "AGENTS.md", "CLAUDE.md"]:
    shutil.copy(f"{src}/{f}", f"{dst}/{f}")
open(f"{dst}/package.json", "w").write(open(f"{src}/package.json").read().replace("architect-compare", "architect-compare-916"))
open(f"{dst}/meta.json", "w").write('{\n  "id": "architect-compare-916",\n  "name": "architect-compare-916",\n  "createdAt": "2026-10-08T12:00:00.000Z"\n}\n')
s = open(f"{src}/index.html").read()
s = s.replace('content="width=1920, height=1080"', 'content="width=1080, height=1920"')
s = s.replace('data-width="1920" data-height="1080"', 'data-width="1080" data-height="1920"')
s = re.sub(r"width: 1920px;\n(\s+)height: 1080px;", r"width: 1080px;\n\1height: 1920px;", s)
css = open(os.path.join(os.path.dirname(__file__), "v916.css")).read()
s = s.replace("    </style>", css + "    </style>", 1)
open(f"{dst}/index.html", "w").write(s)
print("ok", s.count("1920px"))
