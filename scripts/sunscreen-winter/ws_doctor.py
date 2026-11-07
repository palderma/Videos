#!/usr/bin/env python3
"""doctor clip: raw -> KEEP segments with 6-frame cross-dissolves -> ws_grade -> pkg/footage/doctor_graded_cut.mp4 + voice_cut_raw.wav"""
import sys, os, subprocess, cv2, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ws_cuts import KEEP_F, STARTS, XF, DOC_FRAMES, SRC, FPS
from ws_grade import grade
cap = cv2.VideoCapture(SRC); raw = []
while True:
    ok, f = cap.read()
    if not ok: break
    if f.shape[0] != 1920: f = cv2.rotate(f, cv2.ROTATE_90_CLOCKWISE)
    raw.append(f)
print("raw frames", len(raw))
out = "/home/user/ws/pkg/footage/doctor_graded_cut.mp4"
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                      "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
def frame_at(i):
    """timeline frame i -> blended raw frame"""
    hits = []
    for k, (a, b) in enumerate(KEEP_F):
        j = i - STARTS[k]
        if 0 <= j < b - a: hits.append((k, a + j))
    if len(hits) == 1: return raw[min(hits[0][1], len(raw) - 1)].astype(np.float32)
    (k0, f0), (k1, f1) = hits[0], hits[1]
    w = (i - STARTS[k1] + 0.5) / XF; w = w * w * (3 - 2 * w)
    return raw[f0].astype(np.float32) * (1 - w) + raw[min(f1, len(raw) - 1)].astype(np.float32) * w
for i in range(DOC_FRAMES):
    f = frame_at(i).clip(0, 255).astype(np.uint8)
    p.stdin.write(grade(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).tobytes())
p.stdin.close(); p.wait(); print("frames", DOC_FRAMES)
x, sr = sf.read("/home/user/ws/src48.wav", dtype="float32")
spf = sr // FPS; N = DOC_FRAMES * spf; v = np.zeros((N, 2), np.float32); X = XF * spf
for k, (a, b) in enumerate(KEEP_F):
    s = x[a * spf: b * spf].copy()
    if k > 0: s[:X] *= np.sin(np.linspace(0, np.pi / 2, X))[:, None]
    if k < len(KEEP_F) - 1: s[-X:] *= np.cos(np.linspace(0, np.pi / 2, X))[:, None]
    i0 = STARTS[k] * spf; n = min(len(s), N - i0); v[i0:i0 + n] += s[:n]
sf.write("/home/user/ws/voice_cut_raw.wav", v, sr); print("voice", N / sr)
