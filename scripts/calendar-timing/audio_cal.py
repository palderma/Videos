#!/usr/bin/env python3
"""Music + paper SFX for «التوقيت قبل المناسبة». 120 BPM grid from 0.3 s so every flip lands on a beat.
Soft felt-piano + warm pad + a quiet clock tick that runs while the pages turn and stops on «التوقيت بيفرق».
Paper flips are synthesised: lift crackle, air swoosh following the page speed, flutter, settle tap.
-> audio/mix.wav (-14 LUFS integrated, approx.)"""
import numpy as np, os, wave
from scipy.signal import butter, sosfilt
import sys; sys.path.insert(0, "/home/user/cal")
from tl import FLIPS, FINAL, DUR, RULE, CTA

SR = 48000; N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N); RV = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def mf(m): return 440 * 2 ** ((m - 69) / 12)
def add(x, t, g=1.0, pan=0.0, rev=0.25):
    i = int(t * SR)
    if i >= N: return
    x = x[:N - i] * g
    L[i:i + len(x)] += x * np.sqrt(0.5 * (1 - pan)); R[i:i + len(x)] += x * np.sqrt(0.5 * (1 + pan)); RV[i:i + len(x)] += x * rev
def filt(x, kind, f, order=2):
    sos = butter(order, f, btype=kind, fs=SR, output="sos"); return sosfilt(sos, x)

# ---------------- instruments
def piano(m, d=2.6, v=1.0):
    f = mf(m); t = tt(d); x = np.zeros(len(t))
    for h, a, dec in ((1, 1.0, 1.6), (2, 0.45, 2.6), (3, 0.18, 3.8), (4, 0.08, 5.0), (5, 0.04, 6.5)):
        x += a * np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * dec * (0.7 + m / 120))
    hammer = filt(rng.standard_normal(len(t)) * np.exp(-t * 180), "bandpass", [800, 4000]) * 0.15
    x = (x + hammer) * np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.2)
    return filt(x, "lowpass", 3800) * v

def pad(ms, d, att=1.2, rel=1.2):
    t = tt(d); x = np.zeros(len(t))
    for m in ms:
        for det in (-0.07, 0, 0.07):
            f = mf(m + det); ph = rng.uniform(0, 6.28)
            x += (np.sin(2 * np.pi * f * t + ph) + 0.25 * np.sin(4 * np.pi * f * t + ph)) / 3
    x = filt(x, "lowpass", 1500) / len(ms)
    return x * np.clip(t / att, 0, 1) * np.clip((d - t) / rel, 0, 1)

def bass(m, d):
    t = tt(d); f = mf(m)
    return (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)) * np.minimum(1, t / 0.03) * np.exp(-t * 0.8) * np.clip((d - t) / 0.3, 0, 1)

def tick(hi=True):
    t = tt(0.06)
    x = filt(rng.standard_normal(len(t)), "bandpass", [3000, 7000] if hi else [1500, 3500]) * np.exp(-t * 260)
    x += np.sin(2 * np.pi * (2100 if hi else 1500) * t) * np.exp(-t * 200) * 0.4
    return x

def glock(m, d=2.5):
    f = mf(m); t = tt(d)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.5) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)) * np.minimum(1, t / 0.002)

def swell(d, lo=200, hi=5000, up=True):
    t = tt(d); x = rng.standard_normal(len(t))
    out = np.zeros(len(t)); seg = 2400
    for i in range(0, len(t), seg):
        k = i / len(t); k = k if up else 1 - k
        fc = lo * (hi / lo) ** k
        out[i:i + seg] = filt(x[i:i + seg + 0], "bandpass", [fc * 0.7, min(fc * 1.4, 20000)])[:len(out[i:i + seg])]
    env = (t / d) ** 2 if up else (1 - t / d) ** 2
    return out * env

def boom():
    t = tt(2.5); f = 42 + 30 * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6) * np.minimum(1, t / 0.01)

# ---------------- paper flip
def paper_flip(d, size=1.0):
    n = int((d + 0.6) * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    # 1) lift: crisp crackle of the sheet bending off the stack
    m = int(0.28 * SR); cr = np.zeros(m)
    for _ in range(int(40 * size)):
        i = int(rng.beta(1.3, 3.0) * m); cr[i:i + 1] += rng.uniform(-1, 1)
    cr = filt(cr, "bandpass", [2200, 9000]) * 2.2
    cr += filt(rng.standard_normal(m), "bandpass", [2500, 8000]) * np.exp(-np.arange(m) / SR * 14) * 0.25
    out[:m] += cr
    # 2) air swoosh following the page's angular speed (peak around 45 % of the flip)
    x = rng.standard_normal(n)
    sp = np.exp(-((t - d * 0.45) / (d * 0.26)) ** 2)
    lo = filt(x, "bandpass", [250, 1400]); hi = filt(x, "bandpass", [1400, 5500])
    flutter = 1 + 0.35 * np.sin(2 * np.pi * (24 + 10 * sp) * t) * sp
    out += (lo * 0.9 + hi * 0.55 * sp) * sp * flutter * 0.55
    # 3) paper rustle along the flip
    rs = filt(rng.standard_normal(n), "bandpass", [3000, 10000])
    gate = (rng.random(n // 480 + 1) ** 6).repeat(480)[:n]
    out += rs * gate * sp * 0.6
    # 4) settle: the sheet taps the binding / back
    ts = int(d * 0.82 * SR); k = int(0.12 * SR)
    tp = np.arange(k) / SR
    tap = np.sin(2 * np.pi * 170 * tp) * np.exp(-tp * 45) * 0.5 + filt(rng.standard_normal(k), "bandpass", [600, 4000]) * np.exp(-tp * 60) * 0.5
    out[ts:ts + k] += tap[:len(out[ts:ts + k])]
    return out * size

# ---------------- score
B0, BEAT = 0.3, 0.5
def bt(n): return B0 + n * BEAT
CH = [  # (bar start beat, pad notes, bass, piano arpeggio)
    (0, [62, 66, 69, 73], 38, [74, 78, 81, 85]),     # Dmaj7
    (4, [59, 62, 66, 69, 73], 35, [71, 74, 78, 81]),   # Bm9
    (8, [55, 59, 62, 66], 31, [71, 74, 78, 79]),       # Gmaj7
    (12, [57, 61, 64, 66], 33, [69, 73, 76, 78]),      # A6
    (16, [59, 62, 66, 69], 35, [71, 74, 78, 81]),      # Bm7
    (20, [55, 59, 62, 66, 69], 31, [74, 78, 79, 81]),  # Gmaj9
    (24, [59, 62, 66, 69], 35, [71, 74, 78, 81]),      # Bm7   golden rule
    (28, [55, 59, 62, 66], 31, [71, 74, 78, 79]),      # Gmaj7
    (32, [52, 55, 59, 62, 66], 28, [67, 71, 74, 78]),  # Em9
    (36, [57, 61, 64, 66], 33, [69, 73, 76, 78]),      # A6
    (40, [59, 62, 66, 69, 73], 35, [71, 74, 78, 81]),  # Bm9   call to action
    (44, [55, 59, 62, 66, 69], 31, [74, 78, 79, 81]),  # Gmaj9
]
for b, pn, bs, arp in CH:
    add(pad(pn, 2.4, att=0.9 if b else 1.5), bt(b) - 0.2, 0.22, rev=0.4)
    if b >= 4: add(bass(bs, 2.0), bt(b), 0.25, rev=0.05)
    for j, m in enumerate(arp):
        if b == 0 and j < 1: continue
        add(piano(m, 2.4, 0.9 if j == 0 else 0.6), bt(b + j), 0.20, pan=(-0.3, 0.2, -0.1, 0.3)[j], rev=0.35)
# final: Dmaj9 resolves under «التوقيت بيفرق»
tf = FINAL["tin"]
add(pad([50, 62, 66, 69, 73, 76], DUR - tf + 0.2, att=0.4, rel=1.6), tf - 0.1, 0.30, rev=0.5)
add(bass(38, 2.3), tf, 0.32, rev=0.05)
for j, m in enumerate([74, 78, 81, 85, 88]):
    add(piano(m, 2.6, 0.8), tf + 0.06 + j * 0.16, 0.20, pan=(-0.3, 0.3, -0.15, 0.15, 0)[j], rev=0.45)
add(boom(), tf - 0.02, 0.32, rev=0.15)
add(swell(1.1, 400, 7000), tf - 1.1, 0.06, rev=0.3)
for tg in (RULE["tlabel"], RULE["t2"]):
    add(glock(86), tg, 0.08, rev=0.6); add(glock(90), tg + 0.14, 0.06, rev=0.6)
add(swell(0.9, 300, 3000), CTA["tin"] - 0.9, 0.05, rev=0.4)
for j, m in enumerate([93, 97, 100]):
    add(glock(m), FINAL["logo"] + 0.15 + j * 0.12, 0.10, pan=(-0.2, 0.2, 0)[j], rev=0.6)
# clock ticks while time passes: 2.8 .. 12.3
n = 5
while bt(n) < 12.25:
    add(tick(n % 2 == 0), bt(n), 0.09 if n % 2 == 0 else 0.06, pan=0.15, rev=0.1); n += 1
# entrance: airy rise into the calendar landing
add(swell(1.6, 300, 4000), 0.0, 0.07, rev=0.4)
add(piano(74, 2.4, 0.7), 0.3, 0.18, rev=0.45)
# paper flips
for nm, (t0, d) in FLIPS.items():
    add(paper_flip(d, 1.0 if nm != "3" else 0.8), t0, 0.55, pan=0.12, rev=0.12)
# calendar exit whoosh
add(swell(0.9, 1500, 300, up=False), 12.3, 0.05, rev=0.3)

# ---------------- reverb (multi-tap FDN-ish), mix, loudness
def reverb(x):
    y = np.zeros(len(x) + SR * 2)
    for dl, g in ((0.031, 0.5), (0.047, 0.45), (0.071, 0.4), (0.113, 0.35), (0.167, 0.3), (0.229, 0.26), (0.311, 0.2), (0.43, 0.15)):
        i = int(dl * SR); y[i:i + len(x)] += x * g
    y = filt(y, "lowpass", 5000)
    for _ in range(2):
        y2 = y.copy(); i = int(0.37 * SR); y2[i:] += y[:-i] * 0.35; y = y2
    return y[:len(x)]
rv = reverb(RV)
mixL = L + rv; mixR = R + np.roll(rv, int(0.011 * SR))
mix = np.stack([mixL, mixR], 1)
fade = np.clip((DUR - np.arange(N) / SR) / 1.2, 0, 1)[:, None]
mix *= fade
mix *= 0.5 / np.abs(mix).max(); pk = 0.5
os.makedirs("/home/user/cal/audio", exist_ok=True)
with wave.open("/home/user/cal/audio/raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print("ok", pk)
