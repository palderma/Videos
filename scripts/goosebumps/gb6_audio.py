#!/usr/bin/env python3
"""Music + sound design for «جلد الأوزة: 3 أفكار غلط» v6 (gb6.py), 2026-11-10: through-composed music (no loop).
Custom track composed to the picture (120 BPM, A minor -> F -> resolves on Cmaj9 under the logo) + mechanical
split-flap foley generated from the SAME event list the picture uses (gb.py --sfx -> work/sfx.json):
every flap that starts falling = a soft paper flip, every flap that lands = a small mechanical click,
cascade steps = lighter ticks, big moves = the user's approved whoosh. No voice-over.
-> work/mix.wav (48 kHz stereo); loudness is set to -14 LUFS when muxing."""
import numpy as np, os, sys, wave, subprocess, json
SR = 48000
WORK = os.environ.get("GB_WORK", "/home/user/gb/work")
DUR = float(os.environ.get("GB_DUR", "17.0")); N = int(SR * DUR)
rng = np.random.default_rng(1109)
BEAT = 0.5
def mf(m): return 440.0 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(int(d * SR)) / SR
def env(t, a, d): return np.minimum(t / max(a, 1e-4), 1) * np.exp(-np.maximum(t - a, 0) * d)
L = np.zeros(N); R = np.zeros(N); RV = np.zeros(N)
def add(x, t, gain=1.0, pan=0.0, rev=0.0, bus=None):
    i = int(round(t * SR))
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i] * gain
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    L[i:i + len(x)] += x * gl; R[i:i + len(x)] += x * gr
    RV[i:i + len(x)] += x * rev

def hp(x, k=8): return x - np.convolve(x, np.ones(k) / k, mode="same")
def lp(x, k=8): return np.convolve(x, np.ones(k) / k, mode="same")
def bp(x, k1=3, k2=20): return lp(x, k1) - lp(x, k2)
def noise_band(d, fc, bw):
    n = int(d * SR); x = rng.standard_normal(n); f = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    f *= np.exp(-((fr - fc) / bw) ** 2); x = np.fft.irfft(f, n); return x / (np.abs(x).max() + 1e-9)

# ---------------- instruments ----------------
def pluck(m, d=0.9, bright=0.5):
    f = mf(m); P = max(2, int(round(SR / f))); n = int(d * SR)
    out = np.zeros(n + P + 1); burst = rng.uniform(-1, 1, P)
    burst = np.convolve(burst, np.ones(3) / 3, mode="same") * (1 - bright) + burst * bright
    out[:P] = burst; kk = 0.996 if m < 70 else 0.993; i = P
    while i < n:
        j = min(n, i + P); prev = out[i - P:j - P + 1]
        out[i:j] = kk * 0.5 * (prev[:-1] + prev[1:])[: j - i]; i = j
    x = out[:n]; t = tt(d)[:n]
    x = x + 0.35 * np.sin(2 * np.pi * f * t) * np.exp(-t * 5)
    return x * np.minimum(1, (d - t) / 0.05) * np.minimum(1, t / 0.002)
def glock(m, d=1.4):
    f = mf(m); t = tt(d)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 3.0) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 7) \
        + 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 14)
    return x * np.minimum(1, t / 0.0015) * np.minimum(1, (d - t) / 0.05)
def pad(ms, d, att=0.5, rel=0.6):
    t = tt(d); x = np.zeros(len(t))
    for m in ms:
        for det in (-0.07, 0.0, 0.07):
            f = mf(m + det); n = 1
            while f * n < 2200 and n <= 9:
                x += np.sin(2 * np.pi * f * n * t + rng.uniform(0, 6.28)) / n ** 1.5 / 3; n += 1
    return x * np.clip(t / att, 0, 1) * np.clip((d - t) / rel, 0, 1) / max(1, len(ms))
def keys_ep(m, d=1.6):
    """soft electric-piano tone"""
    f = mf(m); t = tt(d)
    mod = np.sin(2 * np.pi * f * t) * 1.2 * np.exp(-t * 4)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 1.6) + 0.2 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 5)
    return x * np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.08)
def bass(m, d):
    f = mf(m); t = tt(d)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 8)
    return x * env(t, 0.008, 1.8) * np.clip((d - t) / 0.05, 0, 1)
def kick(v=1.0):
    t = tt(0.4); f = 46 + 95 * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    return x * v
def clap():
    t = tt(0.3); x = np.zeros(len(t))
    for j, o in enumerate((0.0, 0.010, 0.021, 0.029)):
        i = int(o * SR); n = len(t) - i
        x[i:] += bp(rng.standard_normal(n), 2, 12) * np.exp(-t[:n] * (95 if j < 3 else 20))
    return x
def hat(v=1.0):
    t = tt(0.05); return hp(rng.standard_normal(len(t)), 3) * env(t, 0.001, 110) * v
def riser(d):
    t = tt(d); x = np.zeros(len(t))
    for j in range(24):
        f0 = rng.uniform(300, 900); f = f0 * 2 ** (1.8 * (t / d) ** 1.6)
        x += np.sin(2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 6.28))
    return x / 24 * (t / d) ** 2.2 * np.clip((d - t) / 0.03, 0, 1)

# ---------------- music (v6: through-composed, no loop) ----------------
# 100 BPM, one chord per bar, a 16-bar progression that never repeats a bar; a melody that is generated
# bar by bar (rhythm templates never used twice in a row, notes walk over the scale and land on chord tones);
# layers enter and leave with the picture: explainer = pad + sparse piano; ideas = soft groove; idea 3 = lift;
# ending lines = breakdown (no drums) + riser; outro = resolved Cmaj9 with bells, long fade.
import sys as _s; _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gb5_time import g as G5
BEAT = 0.6; BAR = 4 * BEAT
CH = {"Am9": ([57, 60, 64, 71], 45), "Fmaj7": ([53, 57, 60, 64], 41), "Dm9": ([50, 57, 60, 64], 38),
      "Em7": ([52, 55, 59, 62], 40), "G6": ([55, 59, 62, 64], 43), "Cmaj9": ([48, 55, 62, 64], 36),
      "C": ([48, 55, 60, 64], 36), "Gsus": ([55, 60, 62, 67], 43), "Fadd9": ([53, 57, 60, 67], 41), "Em": ([52, 55, 59, 64], 40)}
PROG = ["Am9", "Fmaj7", "C", "G6", "Dm9", "Am9", "Fadd9", "Em7", "Fmaj7", "G6", "Am9", "Em", "Fmaj7", "Gsus", "Cmaj9", "Cmaj9", "Cmaj9"]
T_IDEAS, T_LIFT, T_END, T_OUT = G5(0.0), G5(9.0), G5(13.15), G5(17.0)
SCALE = [57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81]
RHY = [[(0, 1.5), (1.5, 0.5), (2, 2)], [(0, 1), (1, 1), (2, 1.5), (3.5, 0.5)], [(0.5, 1.5), (2, 1), (3, 1)],
       [(0, 3), (3, 1)], [(0, 0.5), (0.5, 0.5), (1, 2), (3, 1)], [(1, 1), (2, 2)], [(0, 2), (2, 0.5), (2.5, 1.5)]]
mrng = np.random.default_rng(2026)
kicks = []
nbars = int(np.ceil(DUR / BAR))
mi = 9; last_r = -1
for b in range(nbars):
    t0 = b * BAR; name = PROG[min(b, len(PROG) - 1)]; notes, root = CH[name]
    sec = "intro" if t0 < T_IDEAS - 0.01 else "ideas" if t0 < T_LIFT - 0.01 else "lift" if t0 < T_END - 0.01 else "end" if t0 < T_OUT - 0.3 else "outro"
    last = b == nbars - 1 or PROG[min(b + 1, len(PROG) - 1)] != name or sec == "outro"
    # pad: one long note per bar, overlapping cross-fade (no restart clicks); voicing inverts every other bar
    vo = notes if b % 2 == 0 else [n + 12 if i == 0 else n for i, n in enumerate(notes)]
    add(pad(vo, BAR + 0.9, 0.7, 0.9), t0 - 0.2, 0.15 if sec != "outro" else 0.17, rev=0.65)
    if sec != "intro":
        add(bass(root, BAR * 0.9), t0, 0.26 if sec in ("ideas", "lift") else 0.18)
        if sec in ("ideas", "lift"): add(bass(root + 7, BEAT * 0.9), t0 + 2.5 * BEAT, 0.16)
    # melody (piano), sparser in the intro / outro
    r = mrng.integers(len(RHY))
    while r == last_r: r = mrng.integers(len(RHY))
    last_r = r
    for j, (ob, dl) in enumerate(RHY[r]):
        if sec in ("intro", "outro") and j % 2 == 1: continue
        mi = int(np.clip(mi + mrng.choice([-2, -1, -1, 1, 1, 2, 0]), 3, len(SCALE) - 3))
        m = SCALE[mi]
        if ob in (0, 2):         # strong beats -> nearest chord tone
            ct = [n + 12 * o for n in notes for o in (0, 1, 2)]
            m = min(ct, key=lambda c: abs(c - m)); mi = int(np.argmin([abs(s_ - m) for s_ in SCALE]))
        gm = 0.10 if sec in ("ideas", "lift") else 0.12
        add(keys_ep(m + 12 if sec == "outro" else m, dl * BEAT + 0.9), t0 + ob * BEAT, gm, pan=0.15 * np.sin(b + j), rev=0.55)
    # soft arpeggio texture, a different contour per bar (never the same 8-step loop)
    if sec in ("ideas", "lift"):
        order = list(mrng.permutation(4)) + list(mrng.permutation(4))
        for st in range(8):
            add(pluck(notes[order[st]] + 12, 0.7, 0.35), t0 + st * BEAT / 2, (0.07 if st % 2 else 0.10) * (1.15 if sec == "lift" else 1),
                pan=0.3 * (1 if st % 2 else -1), rev=0.4)
    # drums: half-time feel in the ideas, a little more in the lift, none in the explainer / ending / outro
    if sec in ("ideas", "lift"):
        for bb in (0, 2):
            kicks.append(t0 + bb * BEAT); add(kick(0.6), t0 + bb * BEAT, 0.45)
        if sec == "lift" or b % 2 == 1:
            add(kick(0.4), t0 + 3.5 * BEAT, 0.3)
        add(clap(), t0 + 3 * BEAT, 0.07 if sec == "ideas" else 0.11, rev=0.5)
        for s8 in range(8):
            add(hat(0.4 + 0.5 * (s8 % 2) + mrng.uniform(-0.1, 0.1)), t0 + s8 * BEAT / 2 + mrng.uniform(0, 0.008), 0.04, pan=0.35)
add(riser(1.6), T_OUT - 1.6, 0.06, rev=0.5)
for j, m in enumerate((76, 79, 83, 86, 88)): add(glock(m, 2.4), T_OUT + 1.3 + j * 0.11, 0.06, pan=-0.5 + 0.25 * j, rev=0.75)
for j, m in enumerate((84, 83, 79, 76)): add(glock(m, 2.6), T_OUT + 3.4 + j * 0.3, 0.045, pan=0.4 - 0.25 * j, rev=0.8)
duck = np.ones(N)
for kt in kicks:
    i = int(kt * SR); n = min(N - i, int(0.3 * SR))
    if n > 0: duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.28 * np.exp(-np.arange(n) / SR / 0.1))
L *= duck; R *= duck
def reverb(x, seed, dec=0.5):
    r = np.random.default_rng(seed); n = int(2.0 * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / dec); ir = hp(ir, 6); ir /= np.sqrt((ir ** 2).sum())
    M = 1 << int(np.ceil(np.log2(len(x) + n)))
    return np.fft.irfft(np.fft.rfft(x, M) * np.fft.rfft(ir, M), M)[:len(x)]
L += reverb(RV, 1) * 0.5; R += reverb(RV, 2) * 0.5
t = np.arange(N) / SR
fade = np.clip((DUR - t) / 3.0, 0, 1) ** 1.5 * np.clip(t / 0.01, 0, 1)
music = np.stack([L, R], 1) * fade[:, None]
music = np.tanh(music / (np.abs(music).max() + 1e-9) * 1.3) * 0.75

# ---------------- foley from the picture's events ----------------
SL = np.zeros(N); SR_ = np.zeros(N); SRV = np.zeros(N)
def addf(x, t0, gain, pan=0.0, rev=0.0):
    i = int(round(t0 * SR))
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i] * gain
    SL[i:i + len(x)] += x * np.sqrt(0.5 * (1 - pan)); SR_[i:i + len(x)] += x * np.sqrt(0.5 * (1 + pan)); SRV[i:i + len(x)] += x * rev
def click(v=1.0):
    """split-flap landing: soft transient + small plastic body + low knock (no harsh top)"""
    n = int(SR * 0.09); x = np.arange(n) / SR
    tr = bp(rng.standard_normal(n), 2, 9) * np.exp(-x * 520) * 0.7
    body = (np.sin(2 * np.pi * 1650 * x) * 0.5 + np.sin(2 * np.pi * 2900 * x) * 0.25) * np.exp(-x * 160)
    knock = np.sin(2 * np.pi * 210 * x) * np.exp(-x * 60) * 0.6
    return (tr + body + knock) * v * np.minimum(1, x / 0.0005)
def tick(v=1.0):
    n = int(SR * 0.05); x = np.arange(n) / SR
    return (bp(rng.standard_normal(n), 2, 7) * np.exp(-x * 700) * 0.6 + np.sin(2 * np.pi * 2300 * x) * np.exp(-x * 220) * 0.35) * v
def flip(v=1.0):
    """soft paper / card flap: brushed noise swell"""
    d = 0.16; x = tt(d)
    nz = noise_band(d, 2600, 1500)
    e = np.sin(np.pi * np.clip(x / d, 0, 1)) ** 2 * np.exp(-x * 6)
    return nz * e * v
def air(v=1.0):
    d = 0.4; x = tt(d); return noise_band(d, 1200, 700) * np.sin(np.pi * x / d) ** 2 * v
def thump(v=1.0):
    x = tt(0.35); f = 62 + 40 * np.exp(-x * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 10) * v
def bloom(v=1.0):
    d = 0.9; x = tt(d)
    sw = noise_band(d, 900, 900) * (x / d) ** 2 * np.clip((d - x) / 0.05, 0, 1)
    return sw * v
def read_wav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a.reshape(-1, w.getnchannels())
WH = "/mnt/project-files/style-guide/assets/sfx/whoosh-dig_whoosh_06.wav"; WH_PEAK = 0.31   # user-approved whoosh
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", WH, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", f"{WORK}/whoosh.wav"], check=True)
WHOOSH = read_wav(f"{WORK}/whoosh.wav")[:, 0]; WHOOSH = WHOOSH / (np.abs(WHOOSH).max() + 1e-9)
WHOOSH_SOFT = lp(WHOOSH, 10)
ev = json.load(open(os.path.join(WORK, "sfx.json")))
last = {}
for t0, kind, g, pan in ev:
    # thin out identical events that land within 12 ms (strips landing together) so clicks stay delicate
    key = kind
    if key in last and abs(t0 - last[key]) < 0.012: g *= 0.5
    last[key] = t0
    if kind == "click": addf(click(), t0, 0.30 * g, pan, 0.15)
    elif kind == "flipbig":   # the turn: whoosh peaks on the middle of the rotation + a soft card flap
        addf(WHOOSH_SOFT, t0 + 0.06 - WH_PEAK, 0.34 * g, 0, 0.3); addf(flip(), t0, 0.28 * g, 0, 0.25)
    elif kind == "settle":    # the fact lands: soft click + low body
        addf(click(), t0, 0.30 * g, 0, 0.2); addf(thump(), t0, 0.28 * g)
    elif kind == "tick": addf(tick(), t0, 0.22 * g, pan, 0.1)
    elif kind == "flip": addf(flip(), t0, 0.20 * g, pan, 0.2)
    elif kind == "air": addf(air(), t0, 0.10 * g, pan, 0.3)
    elif kind == "whoosh": addf(WHOOSH, t0 + 0.12 - WH_PEAK, 0.30 * g, 0, 0.25)
    elif kind == "whoosh_soft": addf(WHOOSH_SOFT, t0 + 0.12 - WH_PEAK, 0.30 * g, 0, 0.3)
    elif kind == "thump": addf(thump(), t0, 0.45 * g)
    elif kind == "rise": addf(riser(0.7), t0, 0.12 * g, 0, 0.4)
    elif kind == "bloom": addf(bloom(), t0 - 0.55, 0.22 * g, 0, 0.5); addf(thump(), t0 + 0.3, 0.3 * g)
    elif kind == "chime": pass       # the music carries the logo chord
SL += reverb(SRV, 3, 0.3) * 0.4; SR_ += reverb(SRV, 4, 0.3) * 0.4
fx = np.stack([SL, SR_], 1)
mix = music * 0.62 + fx
mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
def wav(path, x):
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
g = 0.89 / (np.abs(music * 0.62 + fx).max() + 1e-9)
wav(os.path.join(WORK, "music.wav"), music * 0.62 * g); wav(os.path.join(WORK, "sfx.wav"), fx * g)
out = os.path.join(WORK, "mix.wav")
w = wave.open(out, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print("wrote", out, round(N / SR, 2), "s")
