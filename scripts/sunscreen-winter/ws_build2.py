#!/usr/bin/env python3
"""After Effects package v2: only the files the project uses + build_project.jsx + fonts + audio stems."""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ws_edit2 as E
from kf import export_jsx, audio
OUT = sys.argv[1]
C = E.build_main()
A = E.PKG + "/audio/"
au = [("صوت الدكتور (منظف)", "voice_doctor.wav", False), ("موسيقى Sequence 04 (تحت الصوت)", "music_bed.wav", False),
      ("مؤثرات صوتية (ووش + إمباكت ناعم)", "sfx.wav", False), ("الميكس النهائي (مرجع - مطفي)", "mix_final.wav", True)]
for nm, f, off in reversed(au): C.layers.insert(0, audio(nm, A + f, start=0, audio_off=off))
used = set()
def walk(c):
    for L in c.layers:
        for X in (L, L.kw.get("matte")):
            if X is None: continue
            if X.kind == "precomp": walk(X.kw["comp"])
            elif "path" in X.kw: used.add(X.kw["path"])
walk(C)
fmap = {}
for d in ("footage", "audio", "fonts"): os.makedirs(os.path.join(OUT, d), exist_ok=True)
for p in sorted(used):
    sub = "audio" if p.startswith(A) else "footage"
    shutil.copy(p, os.path.join(OUT, sub, os.path.basename(p))); fmap[p] = sub + "/" + os.path.basename(p)
for f in os.listdir("/home/user/Videos/brand/fonts"): shutil.copy("/home/user/Videos/brand/fonts/" + f, os.path.join(OUT, "fonts"))
export_jsx(C, os.path.join(OUT, "build_project.jsx"), "ضرورة واقي الشمس بالشتاء v3", fmap)
print("jsx ok", len(used), "files")
