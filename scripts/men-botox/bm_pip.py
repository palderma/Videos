#!/usr/bin/env python3
"""doctor PiP cards for the motion scenes: rounded-corner alpha clips cut from doctor_graded_cut.mp4
-> PNG sequence (render) + ProRes 4444 .mov (After Effects)"""
import os, sys, subprocess, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bm_edit as E
SRC = E.PK + "doctor_graded_cut.mp4"
def make(name, t_in, dur, w, h, r=48, cx=505, cy=760, cw=600):
    ch = cw * h / w
    d = "/home/user/bm/" + name; os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    qx = np.maximum(np.abs(xx - w / 2) - (w / 2 - r), 0); qy = np.maximum(np.abs(yy - h / 2) - (h / 2 - r), 0)
    a = np.clip(r - np.hypot(qx, qy) + 0.5, 0, 1)
    cap = cv2.VideoCapture(SRC); f0 = int(round(t_in * 30)); cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
    n = int(round(dur * 30)); last = None
    for i in range(n):
        ok, fr = cap.read()
        if not ok: fr = last
        last = fr
        x0, y0 = cx - cw / 2, cy - ch / 2
        M = np.float32([[w / cw, 0, -x0 * w / cw], [0, h / ch, -y0 * h / ch]])
        im = cv2.warpAffine(fr, M, (w, h), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
        cv2.imwrite(f"{d}/{i:04d}.png", np.dstack([im, (a * 255).astype(np.uint8)]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{d}/%04d.png", "-c:v", "prores_ks", "-profile:v", "4444",
                    "-pix_fmt", "yuva444p10le", E.PK + name + ".mov"], check=True)
    print(name, n)
make("pip_m1", E.M1_IN, E.M1_OUT - E.M1_IN + 0.6, 512, 572)
make("pip_m2", E.M2_IN, E.M2_OUT - E.M2_IN + 0.6, 440, 492)
