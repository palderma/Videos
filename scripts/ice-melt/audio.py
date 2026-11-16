#!/usr/bin/env python3
"""Sound for «الجليد المنصهر»: music-05 bed + synthesised ice SFX (crack, freeze shimmer, melt trickle/drips, pops).
python3 audio.py out.wav"""
import sys, subprocess, numpy as np
from scipy.signal import butter, sosfilt
sys.path.insert(0, "/home/user/ice")
from scene import EV_SPEC, TOTAL, OUTRO_AT

SR = 48000
N = int(TOTAL * SR) + SR
rng = np.random.default_rng(5)
L = np.zeros(N); R = np.zeros(N)

def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
def hp(x, f): return sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)
def lp(x, f): return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)
def put(sig, t, g=1.0, pan=0.0):
    i = int(t * SR); n = min(len(sig), N - i)
    if n <= 0: return
    L[i:i + n] += sig[:n] * g * (1 - max(pan, 0)); R[i:i + n] += sig[:n] * g * (1 + min(pan, 0))

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def crack():
    n = int(0.9 * SR); s = np.zeros(n)
    t0 = 0.0
    for k in range(9):                               # cascade of micro cracks
        m = int(rng.uniform(0.02, 0.07) * SR); i = int(t0 * SR)
        b = hp(rng.normal(0, 1, m), 1800) * env(m, 0.0005, rng.uniform(0.006, 0.02))
        s[i:i + m] += b * (1.0 if k == 0 else rng.uniform(0.3, 0.7))
        t0 += rng.exponential(0.035)
        if t0 > 0.6: break
    tt = np.arange(n) / SR                            # glassy resonances
    for f in (2350, 3610, 5220):
        s += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.09) * 0.10
    s += lp(rng.normal(0, 1, n), 300) * env(n, 0.001, 0.08) * 0.8   # body thump
    return s / np.abs(s).max()

def shimmer(dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    air = bp(rng.normal(0, 1, n), 4000, 11000) * np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.5 * 0.25
    s = air
    for _ in range(int(dur * 40)):                    # crystal tinkles
        f = rng.uniform(3000, 8000); m = int(0.12 * SR); i = int(rng.uniform(0, dur) * SR)
        if i + m > n: continue
        q = np.arange(m) / SR
        s[i:i + m] += np.sin(2 * np.pi * f * q) * np.exp(-q / 0.03) * rng.uniform(0.05, 0.18)
    return s / np.abs(s).max()

def drip():
    m = int(0.09 * SR); q = np.arange(m) / SR
    f0 = rng.uniform(700, 1300); f = f0 * (1 + 1.4 * q / 0.09)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-q / 0.022)

def trickle(dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    w = bp(rng.normal(0, 1, n), 500, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * tt + rng.uniform(0, 6)))
    e = np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.6)
    return w * e / np.abs(w).max()

def pop(f=660):
    m = int(0.25 * SR); q = np.arange(m) / SR
    return (np.sin(2 * np.pi * f * q) + 0.4 * np.sin(2 * np.pi * 2 * f * q)) * np.exp(-q / 0.06) * np.minimum(1, q / 0.003)

wh = None
try:
    import soundfile as sf
except ImportError:
    sf = None
def whoosh():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "/mnt/project-files/style-guide/assets/sfx/whoosh-dig_whoosh_06.wav",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    w = np.frombuffer(raw, np.float32).astype(float)
    return lp(w, 5000) / np.abs(w).max()

W_ = whoosh()
for kind, a, b, seed, o, ca, co in EV_SPEC:
    if kind == "melt":
        put(crack(), ca, 0.55, pan=(co[0] - 540) / 900)
        put(W_, a - 0.05, 0.30)
        put(trickle(b - a + 0.8), a, 0.10)
        for _ in range(9):
            put(drip(), rng.uniform(a + 0.2, b + 1.2), rng.uniform(0.08, 0.16), pan=rng.uniform(-0.6, 0.6))
    else:
        put(shimmer(b - a + 0.3), a - 0.1, 0.22)
# accents: check, dots, bookmark, send
put(pop(880), EV_SPEC[2][2] - 0.2, 0.18)
for d in range(7): put(pop(700 + d * 60), EV_SPEC[6][2] - 0.15 + d * 0.16, 0.08)
put(pop(780), EV_SPEC[8][2] - 0.05, 0.18)
put(W_[: int(0.6 * SR)] * np.linspace(1, 0, int(0.6 * SR)), EV_SPEC[8][2] + 0.55, 0.15, pan=-0.4)

mx = np.stack([L, R], 1)[: int(TOTAL * SR)].astype(np.float32)
mx /= max(1e-6, np.abs(mx).max()) / 0.9
open("/home/user/ice/work/sfx.f32", "wb").write(mx.tobytes())
out = sys.argv[1] if len(sys.argv) > 1 else "/home/user/ice/work/audio.wav"
fo = TOTAL - 2.5
# music: music-05 bed, soft fade in, dips a little under the outro, long fade to the end
fc = ("[0:a]atrim=0:%.3f,asetpts=N/SR/TB,volume=0.55,afade=t=in:d=1.2,afade=t=out:st=%.3f:d=2.5[m];"
      "[1:a]volume=1.0[s];[m][s]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[o]") % (TOTAL, fo)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "/mnt/project-files/style-guide/assets/music/music-05.mp3",
                "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "/home/user/ice/work/sfx.f32",
                "-filter_complex", fc, "-map", "[o]", "-ar", "48000", out], check=True)
print("ok", out)
