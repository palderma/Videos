#!/usr/bin/env python3
"""After Effects package for «أسباب فشل علاج الكلف»: build_project.jsx (every layer + keyframe) + footage + audio + fonts."""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl4_edit as E
from kf import export_jsx, audio
PKG = "/home/user/klf/pkg4"
C = E.build()
au = [("صوت الدكتور (منظف)", "voice_doctor.wav", False), ("موسيقى Sequence 04 (تحت الصوت)", "music_bed.wav", False),
      ("مؤثرات صوتية (ووش + إمباكت ناعم)", "sfx.wav", False), ("الميكس النهائي (مرجع - مطفي)", "mix_final.wav", True)]
for nm, f, off in reversed(au):
    C.layers.insert(0, audio(nm, PKG + "/audio/" + f, start=0, audio_off=off))
os.makedirs(PKG + "/fonts", exist_ok=True)
for f in os.listdir("/home/user/Videos/brand/fonts"): shutil.copy("/home/user/Videos/brand/fonts/" + f, PKG + "/fonts/")
fmap = {}
for root, _, files in os.walk(PKG):
    for f in files:
        p = os.path.join(root, f); fmap[p] = os.path.relpath(p, PKG).replace(os.sep, "/")
export_jsx(C, PKG + "/build_project.jsx", "أسباب فشل علاج الكلف v4", fmap)
print("jsx ok", os.path.getsize(PKG + "/build_project.jsx"), "layers", len(C.layers))
