#!/usr/bin/env python3
"""doctor clip: raw -> KEEP segments (6-frame dissolve at the one pause cut) -> gentle face stabilisation (very slow,
keeps the face near the centre line) -> bm_grade -> pkg/footage/doctor_graded_cut.mp4 + voice_cut_raw.wav"""
import sys, os, subprocess, json, cv2, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm_cuts import KEEP_F, STARTS, XF, DOC_FRAMES, SRC, FPS
from bm_grade import grade
BM = "/home/user/bm"
cap = cv2.VideoCapture(SRC); raw = []
while True:
    ok, f = cap.read()
    if not ok: break
    if f.shape[0] != 1920: f = cv2.rotate(f, cv2.ROTATE_90_CLOCKWISE)
    raw.append(f)
NR = len(raw); print("raw frames", NR)
# face track -> per-raw-frame offset (gaussian sigma 1.6 s), max ±30 px
fa = np.array(json.load(open(BM + "/face.json")))
tt = np.arange(NR) / FPS
fx = np.interp(tt, fa[:, 0], fa[:, 1]); fy = np.interp(tt, fa[:, 0], fa[:, 2])
def gsm(x, s):
    k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); k /= k.sum()
    return np.convolve(np.pad(x, 3 * s, mode="edge"), k, "valid")
s = int(1.6 * FPS)
DX = np.clip(505 - gsm(fx, s), -30, 30); DY = np.clip(645 - gsm(fy, s), -30, 30)
np.save(BM + "/stab.npy", np.stack([DX, DY], 1))
def stab(i):
    M = np.float32([[1, 0, DX[i]], [0, 1, DY[i]]])
    return cv2.warpAffine(raw[i], M, (1080, 1920), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
out = BM + "/pkg/footage/doctor_graded_cut.mp4"
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                      "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
def frame_at(i):
    hits = []
    for k, (a, b) in enumerate(KEEP_F):
        j = i - STARTS[k]
        if 0 <= j < b - a: hits.append((k, min(a + j, NR - 1)))
    if len(hits) == 1: return stab(hits[0][1])
    (k0, f0), (k1, f1) = hits[0], hits[1]
    w = (i - STARTS[k1] + 0.5) / XF; w = w * w * (3 - 2 * w)
    return stab(f0) * (1 - w) + stab(f1) * w
for i in range(DOC_FRAMES):
    f = frame_at(i).clip(0, 255).astype(np.uint8)
    p.stdin.write(grade(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).tobytes())
p.stdin.close(); p.wait(); print("frames", DOC_FRAMES)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "2", "-ar", "48000", BM + "/src48.wav"], check=True)
x, sr = sf.read(BM + "/src48.wav", dtype="float32")
spf = sr // FPS; N = DOC_FRAMES * spf; v = np.zeros((N, 2), np.float32); X = XF * spf
for k, (a, b) in enumerate(KEEP_F):
    seg = x[a * spf: b * spf].copy()
    if k > 0: seg[:X] *= np.sin(np.linspace(0, np.pi / 2, X))[:, None]
    if k < len(KEEP_F) - 1: seg[-X:] *= np.cos(np.linspace(0, np.pi / 2, X))[:, None]
    i0 = STARTS[k] * spf; n = min(len(seg), N - i0); v[i0:i0 + n] += seg[:n]
sf.write(BM + "/voice_cut_raw.wav", v, sr); print("voice", N / sr)
