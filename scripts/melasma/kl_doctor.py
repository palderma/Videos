#!/usr/bin/env python3
"""doctor clip: raw -> KEEP segments (pauses removed only) -> kl_grade -> pkg/footage/doctor_graded_cut.mp4 (+ raw voice cut wav)"""
import sys, os, subprocess, cv2, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kl_edit import KEEP, SRC
from kl_grade import grade
cap = cv2.VideoCapture(SRC)
out = "/home/user/klf/pkg/footage/doctor_graded_cut.mp4"
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                      "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
fr = [(int(round(a * 30)), int(round(b * 30))) for a, b in KEEP]
i = n = 0
while True:
    ok, f = cap.read()
    if not ok: break
    if f.shape[0] != 1920: f = cv2.rotate(f, cv2.ROTATE_90_CLOCKWISE)
    if any(a <= i < b for a, b in fr):
        p.stdin.write(grade(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).tobytes()); n += 1
    i += 1
p.stdin.close(); p.wait(); print("frames", n, "src frames", i)
# voice: same segments, 10 ms fade-out / fade-in at every join (joins sit inside real pauses; no overlap -> exact sync)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "2", "-ar", "48000", "/home/user/klf/src48.wav"], check=True)
x, sr = sf.read("/home/user/klf/src48.wav", dtype="float32")
segs = [x[a * sr // 30: b * sr // 30] for a, b in fr]
X = int(0.01 * sr)
for k, s in enumerate(segs):
    s[:] = s.copy()
    if k > 0: s[:X] *= np.linspace(0, 1, X)[:, None]
    if k < len(segs) - 1: s[-X:] *= np.linspace(1, 0, X)[:, None]
outw = np.concatenate(segs)
need = n * sr // 30
outw = np.concatenate([outw, np.zeros((max(0, need - len(outw)), 2), np.float32)])[:need]
sf.write("/home/user/klf/voice_cut_raw.wav", outw, sr); print("voice", len(outw) / sr)
