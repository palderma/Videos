#!/usr/bin/env python3
"""v4 audio: hook voice (doctor's own uncut sentence) + v3 stems shifted by H; one continuous ducked music bed."""
import os, sys, subprocess, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl4_edit as E
SR = 48000; A3 = "/home/user/klf/pkg2/audio/"; A = os.environ.get("KL_PKG", "/home/user/klf/pkg4") + "/audio/"; os.makedirs(A, exist_ok=True)
N = int(E.DUR * SR); h = int(E.H * SR)
def ff(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)
rd = lambda p: sf.read(p, dtype="float32")[0]
vp = rd("/home/user/klf/voice_proc.wav")
hv = vp[int(E.SRC0 * SR): int((E.SRC0 + E.VOICE_END) * SR)].copy()
f = int(0.04 * SR); hv[-f:] *= np.linspace(1, 0, f)[:, None]; hv[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))[:, None]
voice = np.zeros((N, 2), np.float32); voice[:len(hv)] = hv
v3 = rd(A3 + "voice_doctor.wav"); voice[h:h + len(v3)] += v3[:N - h]
# music: same bed, same ducking law, continuous from frame 1
m = rd("/home/user/klf/music_raw.wav")
if len(m) < N:
    ff(["-i", "/mnt/project-files/style-guide/assets/music/sequence-04.mp3", "-t", str(E.DUR + 1), "-ar", "48000", "-ac", "2", "/home/user/klf/music_raw4.wav"])
    m = rd("/home/user/klf/music_raw4.wav")
mus = m[:N].copy(); mus /= np.sqrt(np.mean(mus ** 2)) + 1e-9
env = np.sqrt(np.convolve(np.mean(voice ** 2, 1), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same"))
vr = np.sqrt(np.mean(voice[np.abs(voice[:, 0]) > 1e-4] ** 2))
sm = np.convolve(np.clip(env / (vr * 0.35), 0, 1), np.ones(int(0.6 * SR)) / int(0.6 * SR), "same")
t = np.arange(N) / SR
g_db = -19.0 + (1 - sm) * 4.0 - 2.0 * np.exp(-((t - E.T["khate"]) / 0.6) ** 2)
gain = 10 ** (g_db / 20) * vr * (0.55 + 0.45 * np.clip(t / 1.0, 0, 1))
gain *= np.where(t > E.SPEECH_END + 0.15, 1 + 0.41 * np.clip((t - E.SPEECH_END - 0.15) / 0.6, 0, 1), 1)
gain *= np.clip((E.DUR - t) / 1.0, 0, 1)
mus *= gain[:, None]
# sfx: v3 sfx shifted + hook: soft impact on «3 أسباب», small pops for badges, approved whoosh on the flash
sfx = np.zeros((N, 2), np.float32); s3 = rd(A3 + "sfx.wav"); sfx[h:h + len(s3)] += s3[:N - h]
wh, sr0 = sf.read("/mnt/project-files/style-guide/assets/sfx/whoosh-dig_whoosh_06.wav", dtype="float32")
if wh.ndim == 1: wh = np.stack([wh, wh], 1)
if sr0 != SR:
    idx = np.arange(int(len(wh) * SR / sr0)) * sr0 / SR
    wh = np.stack([np.interp(idx, np.arange(len(wh)), wh[:, c]) for c in range(2)], 1).astype(np.float32)
wh /= np.abs(wh).max() + 1e-9
def put(x, at, g):
    i = max(0, int(at * SR)); k = min(len(x), N - i); sfx[i:i + k] += x[:k] * g
tt = np.arange(int(0.9 * SR)) / SR
x = np.tanh((np.sin(2 * np.pi * (48 + 60 * np.exp(-tt * 14)) * tt) * np.exp(-tt * 5.5) + np.sin(2 * np.pi * 196 * tt) * np.exp(-tt * 9) * 0.12) * 1.3) * np.clip(tt / 0.004, 0, 1)
imp = np.stack([x, x], 1).astype(np.float32)
tp = np.arange(int(0.09 * SR)) / SR; y = np.sin(2 * np.pi * (900 + 600 * np.exp(-tp * 40)) * tp) * np.exp(-tp * 38); pop = np.stack([y, y], 1).astype(np.float32)
db = lambda d: 10 ** (d / 20); vg = vr * 0.9
put(imp, E.HT["thalath"] - 0.06, vg * db(-7))
put(wh, E.H - 0.31, vg * db(-10))
for nm, xx in (("voice_doctor", voice), ("music_bed", mus), ("sfx", sfx)): sf.write(A + nm + ".wav", xx, SR)
sf.write("/home/user/klf/mix_pre4.wav", voice + mus + sfx, SR)
ff(["-i", "/home/user/klf/mix_pre4.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", A + "mix_final.wav"])
print("audio4 ok", E.DUR)
