#!/usr/bin/env python3
"""After Effects package for «الشد المائي خرافة»: build_project.jsx (every layer + keyframe) + footage + audio + fonts."""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm_edit as E
from kf import export_jsx, audio
PKG = "/home/user/sm/pkg"
C = E.build()
au = [("صوت الدكتور", "voice_doctor.wav", False), ("موسيقى Sequence 04 (منخفضة تحت الصوت)", "music_bed.wav", False),
      ("مؤثرات صوتية (ووش + بوب + ختم)", "sfx.wav", False), ("الميكس النهائي (مرجع - مطفي)", "mix_final.wav", True)]
for nm, f, off in reversed(au):
    C.layers.insert(0, audio(nm, PKG + "/audio/" + f, start=0, audio_off=off))
fmap = {}
for root, _, files in os.walk(PKG):
    for f in files:
        p = os.path.join(root, f); fmap[p] = os.path.relpath(p, PKG).replace(os.sep, "/")
export_jsx(C, PKG + "/build_project.jsx", "الشد المائي خرافة", fmap)
print("jsx ok", os.path.getsize(PKG + "/build_project.jsx"))
