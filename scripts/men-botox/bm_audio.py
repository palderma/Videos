#!/usr/bin/env python3
"""Audio for «بوتوكس الرجال»: doctor voice (uncut; de-clip for the hot recording, high-pass, light denoise, de-ess,
gentle compression, loudness), calm music bed (sequence-04) ducked ~19 dB under the voice from frame 1, a few soft SFX.
Writes pkg/audio/{voice_doctor,music_bed,sfx,mix_final}.wav (48 kHz stereo, full length)."""
import os, sys, subprocess, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bm_edit as E
BM = "/home/user/bm/"
SR = 48000; A = E.PKG + "/audio/"; os.makedirs(A, exist_ok=True)
N = int(E.DUR * SR)
def ff(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)
rd = lambda p: sf.read(p, dtype="float32")[0]
def movavg(x, n):
    c = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)]); h_ = n // 2
    i = np.arange(len(x)); a = np.clip(i - h_, 0, len(x)); b = np.clip(i - h_ + n, 0, len(x))
    return ((c[b] - c[a]) / n).astype(np.float32)
ff(["-i", BM + "voice_cut_raw.wav", "-af",
    "volume=-3dB,adeclip,highpass=f=80,afftdn=nr=5:nf=-50,deesser=i=0.3,equalizer=f=3000:t=q:w=1.2:g=1.5,"
    "acompressor=threshold=-21dB:ratio=2:attack=10:release=140:makeup=1.5,loudnorm=I=-16:TP=-2:LRA=8",
    "-ar", "48000", "-ac", "2", BM + "voice_proc.wav"])
vp = rd(BM + "voice_proc.wav")
voice = np.zeros((N, 2), np.float32); n = min(N, len(vp)); voice[:n] = vp[:n]
i0 = int((E.SPEECH_END + 0.25) * SR); i1 = int(E.T_OUTRO * SR)
voice[i0:i1] *= np.linspace(1, 0, i1 - i0)[:, None] ** 2; voice[i1:] = 0
voice[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))[:, None]

ff(["-i", "/mnt/project-files/style-guide/assets/music/sequence-04.mp3", "-t", str(E.DUR + 1), "-ar", "48000", "-ac", "2", BM + "music_raw.wav"])
m = rd(BM + "music_raw.wav")
if len(m) < N: m = np.concatenate([m, m])
mus = m[:N].copy(); mus /= np.sqrt(np.mean(mus ** 2)) + 1e-9
env = np.sqrt(movavg(np.mean(voice ** 2, 1), int(0.25 * SR)))
vr = np.sqrt(np.mean(voice[np.abs(voice[:, 0]) > 1e-4] ** 2))
sm = movavg(np.clip(env / (vr * 0.35), 0, 1), int(0.6 * SR))
t = np.arange(N) / SR
g_db = -19.0 + (1 - sm) * 4.0
gain = 10 ** (g_db / 20) * vr * (0.6 + 0.4 * np.clip(t / 1.0, 0, 1))
se = E.SPEECH_END + 0.15
gain *= np.where(t > se, 1 + 0.41 * np.clip((t - se) / 0.8, 0, 1), 1)
gain *= np.clip((E.DUR - t) / 1.5, 0, 1)
mus *= gain[:, None]

sfx = np.zeros((N, 2), np.float32)
wh, sr0 = sf.read("/mnt/project-files/style-guide/assets/sfx/whoosh-dig_whoosh_06.wav", dtype="float32")
if wh.ndim == 1: wh = np.stack([wh, wh], 1)
if sr0 != SR:
    idx = np.arange(int(len(wh) * SR / sr0)) * sr0 / SR
    wh = np.stack([np.interp(idx, np.arange(len(wh)), wh[:, c]) for c in range(2)], 1).astype(np.float32)
wh /= np.abs(wh).max() + 1e-9
PEAK = 0.31
def put(x, at, g):
    i = int(at * SR)
    if i < 0: x = x[-i:]; i = 0
    k = min(len(x), N - i)
    if k > 0: sfx[i:i + k] += x[:k] * g
tt = np.arange(int(0.9 * SR)) / SR
x = np.tanh((np.sin(2 * np.pi * (48 + 60 * np.exp(-tt * 14)) * tt) * np.exp(-tt * 5.5) + np.sin(2 * np.pi * 196 * tt) * np.exp(-tt * 9) * 0.12) * 1.3) * np.clip(tt / 0.004, 0, 1)
imp = np.stack([x, x], 1).astype(np.float32)
db = lambda d: 10 ** (d / 20); vg = vr * 0.9
put(imp, E.T["end1"] - 0.02, vg * db(-6))                          # hook title «بوتوكس»
for tin in (E.M1_IN, E.M2_IN): put(wh, tin + 0.2 - PEAK, vg * db(-10))    # scene entries (soft)
for tp in (E.M1_OUT, E.M2_OUT): put(wh, tp + 0.15 - PEAK, vg * db(-13))   # soft return to the doctor
put(imp, E.T["khams"] - 0.02, vg * db(-9))                         # «5 دقائق»
put(imp, E.T["rijal"] - 0.02, vg * db(-9))                         # «للرجال»
put(wh, E.T_WIPE + 0.2 - PEAK, vg * db(-10))                       # outro circle
for nm, xx in (("voice_doctor", voice), ("music_bed", mus), ("sfx", sfx)): sf.write(A + nm + ".wav", xx, SR)
sf.write(BM + "mix_pre.wav", voice + mus + sfx, SR)
ff(["-i", BM + "mix_pre.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", A + "mix_final.wav"])
print("audio ok", E.DUR)
