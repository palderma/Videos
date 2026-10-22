#!/usr/bin/env python3
"""Audio for «البيبي فيس - جلسة الدراكولا» (Comp 1): doctor voice cleaned and levelled (only the leading 1.2 s of
silence trimmed, never cut mid-sentence), Sequence 04 bed ducked under speech, the user's whoosh on transitions,
soft pops/shimmers on graphics, music fades smoothly into the outro, -14 LUFS, TP <= -1 dB."""
import numpy as np, subprocess, wave, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bf_timeline import RAW, OFF, SPEECH_END, RAW_END, TB, T_MSG, MSG_HOLD, T_OUT, DUR, T_PIP_IN, wfind, gfind
WORK = os.path.join(HERE, "..", "comp1_work"); os.makedirs(WORK, exist_ok=True)
SR = 48000; N = int(SR * DUR)
rng = np.random.default_rng(11)

def run(cmd): subprocess.run(cmd, check=True)
def read_wav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a.reshape(-1, w.getnchannels())
def write_wav(p, a):
    a = np.clip(a, -1, 1); w = wave.open(p, "wb"); w.setnchannels(a.shape[1]); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((a * 32767).astype(np.int16).tobytes()); w.close()
def db(x): return 10 ** (x / 20)
def ws(w, n=0): return wfind(w, n)["s"]

# ---- voice ----
run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(OFF), "-i", RAW, "-vn", "-ac", "1", "-ar", str(SR),
     "-af", "highpass=f=80,afftdn=nf=-35:nr=8,equalizer=f=3000:t=q:w=1.2:g=1.5,"
            "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=120:makeup=1.5,loudnorm=I=-16:TP=-2:LRA=7",
     os.path.join(WORK, "voice.wav")])
voice = read_wav(os.path.join(WORK, "voice.wav"))[:, 0]
voice[:int(0.15 * SR)] *= np.linspace(0, 1, int(0.15 * SR))
e0, e1 = int((SPEECH_END + 0.08) * SR), int((SPEECH_END + 0.35) * SR)
voice = voice[:e1]; voice[e0:e1] *= np.linspace(1, 0, e1 - e0)
voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]

# ---- music bed, ducked ----
run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "1", "-i", "/mnt/project-files/style-guide/assets/music/sequence-04.mp3",
     "-t", str(DUR), "-ac", "2", "-ar", str(SR), os.path.join(WORK, "music.wav")])
music = read_wav(os.path.join(WORK, "music.wav")); music = np.pad(music, ((0, max(0, N - len(music))), (0, 0)))[:N]
hop = 480; env = np.sqrt(np.convolve(voice ** 2, np.ones(hop * 4) / (hop * 4), "same"))
talking = (env > db(-38)).astype(np.float32)
k = np.ones(int(SR * 0.25)) / int(SR * 0.25); talking = np.clip(np.convolve(talking, k, "same") * 1.5, 0, 1)
t = np.arange(N) / SR
gain_db = np.full(N, 0.0) - 4.0 * talking
gain_db += 9.0 * np.clip((t - SPEECH_END - 0.2) / 0.8, 0, 1)      # lift the bed under the page outro
g = db(gain_db); g *= np.clip((DUR - t) / 1.6, 0, 1); g *= np.clip(t / 0.15, 0, 1)
music = music * g[:, None]

# ---- SFX ----
def bandnoise(n, f0, f1, q=6):
    out = np.zeros(n); chunks = 24; Lc = n // chunks
    for c in range(chunks):
        fc = f0 * (f1 / f0) ** (c / (chunks - 1))
        seg = rng.standard_normal(Lc + 512); Sg = np.fft.rfft(seg); ff = np.fft.rfftfreq(len(seg), 1 / SR)
        Sg *= np.exp(-((np.log(ff + 1) - np.log(fc)) ** 2) * q)
        y = np.fft.irfft(Sg, len(seg))[:Lc]; out[c * Lc:(c + 1) * Lc] = y * np.hanning(Lc) ** 0.3
    return out / (np.abs(out).max() + 1e-9)
def whoosh(dur=0.5):
    n = int(SR * dur); return bandnoise(n, 300, 3500, 3) * np.sin(np.linspace(0, np.pi, n)) ** 2.2
def env_ad(n, a, d):
    e = np.ones(n); na = int(a * SR); e[:na] = np.linspace(0, 1, na); e[na:] = np.exp(-np.linspace(0, d, n - na)); return e
def pop():
    n = int(SR * 0.12); tt = np.arange(n) / SR; fq = 900 * np.exp(-tt * 25) + 380
    return np.sin(2 * np.pi * np.cumsum(fq) / SR) * env_ad(n, 0.002, 9)
def impact():
    n = int(SR * 0.9); tt = np.arange(n) / SR; fq = 95 * np.exp(-tt * 3) + 42
    return (np.sin(2 * np.pi * np.cumsum(fq) / SR) * np.exp(-tt * 5) + rng.standard_normal(n) * np.exp(-tt * 40) * 0.35) / 1.2
def shimmer():
    n = int(SR * 1.0); tt = np.arange(n) / SR; out = np.zeros(n)
    for i, fq in enumerate((1318, 1760, 2093, 2637)):
        st = int(i * 0.06 * SR); m = n - st; out[st:] += np.sin(2 * np.pi * fq * tt[:m]) * np.exp(-tt[:m] * 5)
    return out / 4
def click():
    n = int(SR * 0.05); tt = np.arange(n) / SR
    return (rng.standard_normal(n) * np.exp(-tt * 300) + np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 120)) / 2

# the user's approved whoosh (dig_whoosh_06, peak at 0.31 s) replaces the synthesized one
WH = "/mnt/project-files/style-guide/assets/sfx/whoosh-dig_whoosh_06.wav"; WH_PEAK = 0.31
run(["ffmpeg", "-loglevel", "error", "-y", "-i", WH, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", os.path.join(WORK, "whoosh.wav")])
WHOOSH = read_wav(os.path.join(WORK, "whoosh.wav"))[:, 0]
events = []
for T in TB[1:4]: events.append((T - WH_PEAK, WHOOSH, -20))
events.append((TB[4] - 0.1 - WH_PEAK, WHOOSH, -21))                       # flash back to the doctor
events.append((T_PIP_IN + 0.3 - WH_PEAK, WHOOSH, -23))
events.append((ws("حلم") - 0.1, pop(), -24)); events.append((ws("صبية") - 0.1, shimmer(), -26))
events.append((ws("بتعرف") - 0.1, pop(), -26))
events.append((ws("جداً") + 0.05, shimmer(), -28))                       # circle drawn
events.append((ws("أهم") - 0.12, impact(), -24))
events.append((ws("الوقت") + 0.05, shimmer(), -28))
for T in TB[1:4]: events.append((T + 0.1, pop(), -25))                    # chapter pills
events.append((ws("الدراكولا") - 0.3, pop(), -24))
events.append((ws("البيبي", 1) - 0.15, pop(), -23)); events.append((ws("البيبي", 1), shimmer(), -24))
events.append((TB[2] + 0.3, pop(), -25))
for w in ("الشتاء", "آخر"): events.append((ws(w) - 0.3, pop(), -23)); events.append((ws(w) + 0.35, pop(), -27))
events.append((ws("الخريف") + 0.3, shimmer(), -27))
events.append((ws("نقاهة") - 0.45, pop(), -24))
for w in ("خمسة", "لأسبوع"): events.append((ws(w) - 0.3, pop(), -23))
events.append((ws("لأسبوع") + 0.45, shimmer(), -27))
events.append((T_MSG + 0.95, pop(), -24))                                 # messenger button pops
events.append((T_MSG + 1.25, click(), -20))                               # cursor click
events.append((gfind("بمركز بالديرما")["s"], pop(), -25))
events.append((T_OUT + 0.35 - WH_PEAK, WHOOSH, -21))                     # circle wipe into our outro
events.append((T_OUT + 1.2, shimmer(), -25))
sfx = np.zeros(N)
for T, x, lvl in events:
    i = int(T * SR); x = x[: N - i] * db(lvl) / (np.abs(x).max() + 1e-9); sfx[i:i + len(x)] += x

mix = music + (voice + sfx)[:, None]
m = talking > 0.9
vr = 20 * np.log10(np.sqrt((voice[m] ** 2).mean())); mr = 20 * np.log10(np.sqrt((music[m] ** 2).mean()))
print(f"voice {vr:.1f} dB, music under voice {mr:.1f} dB, gap {vr - mr:.1f} dB")
write_wav(os.path.join(WORK, "mix_pre.wav"), mix * 0.9)
o = subprocess.run(["ffmpeg", "-hide_banner", "-i", os.path.join(WORK, "mix_pre.wav"), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", o)[-1])
run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(WORK, "mix_pre.wav"),
     "-af", f"volume={-14 - I}dB,alimiter=limit=0.89:attack=3:release=60:level=false", "-ar", str(SR), os.path.join(WORK, "mix.wav")])
print("audio done", DUR)
