#!/usr/bin/env python3
"""doctor clip: raw -> keep segments (sm_edit.KEEP) -> sm_grade -> + 1.5 s freeze of the last frame (no reverse) -> pkg/footage/doctor_graded_cut.mp4"""
import sys, os, subprocess, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sm_edit import KEEP
from sm_grade import grade
cap = cv2.VideoCapture("/mnt/project-files/الشد المائي خرافه.mp4")
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                      "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                      "/home/user/sm/pkg/footage/doctor_graded_cut.mp4"], stdin=subprocess.PIPE)
i = 0; last = None; n = 0
while True:
    ok, f = cap.read()
    if not ok: break
    t = i / 30; i += 1
    if any(a - 1e-6 <= t < b - 1e-6 for a, b in KEEP):
        last = grade(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)); p.stdin.write(last.tobytes()); n += 1
for _ in range(45): p.stdin.write(last.tobytes()); n += 1
p.stdin.close(); p.wait(); print("frames", n)
