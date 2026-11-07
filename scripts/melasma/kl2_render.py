#!/usr/bin/env python3
"""render frames a..b-1 of the main comp to an mp4 chunk: sm_render.py a b out.mp4"""
import sys, os, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl2_edit as E
from kf import render_comp
C = E.build(); a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                      "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
for i in range(a, b):
    p.stdin.write(render_comp(C, i / 30).clip(0, 255).astype(np.uint8).tobytes())
    if i % 60 == 0: print(i, flush=True)
p.stdin.close(); p.wait(); print("done", out)
