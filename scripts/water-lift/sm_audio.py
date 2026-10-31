#!/usr/bin/env python3
"""Audio for «الشد المائي خرافة»: voice (cut, cleaned), music bed ducked ~18 dB under the voice, SFX on the cuts.
Writes pkg/audio/{voice_doctor.wav, music_bed.wav, sfx.wav, mix_final.wav} (48 kHz stereo, same length as the comp)."""
import os, sys, subprocess, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm_edit as E
SR = 48000; A = "/home/user/sm/pkg/audio/"; os.makedirs(A, exist_ok=True)
N = int(E.DUR * SR)
def ff(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)

# voice: highpass + gentle compression + loudness
ff(["-i", "/home/user/sm/voice_cut_raw.wav", "-af", "highpass=f=80,afftdn=nr=8:nf=-42,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,loudnorm=I=-16:TP=-2:LRA=9", "-ar", "48000", "-ac", "2", "/home/user/sm/voice_proc.wav"])
v, _ = sf.read("/home/user/sm/voice_proc.wav", dtype="float32")
voice = np.zeros((N, 2), np.float32); n = min(N, len(v)); voice[:n] = v[:n]
# fade the doctor's last breath under the outro
i0 = int((E.T_OUTRO + 0.2) * SR); voice[i0:] *= np.linspace(1, 0, N - i0)[:, None] ** 2

# music bed (sequence-04 = the reference bed)
ff(["-i", "/mnt/project-files/style-guide/assets/music/sequence-04.mp3", "-t", str(E.DUR + 1), "-ar", "48000", "-ac", "2", "/home/user/sm/music_raw.wav"])
m, _ = sf.read("/home/user/sm/music_raw.wav", dtype="float32")
mus = np.zeros((N, 2), np.float32); n = min(N, len(m)); mus[:n] = m[:n]
mus /= (np.sqrt(np.mean(mus ** 2)) + 1e-9)
# envelope of the voice -> duck
env = np.sqrt(np.convolve(np.mean(voice ** 2, 1), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same"))
vr = np.sqrt(np.mean(voice[voice[:, 0] != 0] ** 2))
speech = np.clip(env / (vr * 0.35), 0, 1)
sm = np.convolve(speech, np.ones(int(0.5 * SR)) / int(0.5 * SR), "same")    # slow, no pumping
g_db = -18.5 + (1 - sm) * 5.0                                               # -18.5 dB under speech, ~-13.5 in gaps
gain = 10 ** (g_db / 20) * vr
t = np.arange(N) / SR
gain *= np.clip(t / 0.25, 0, 1)                                             # in from frame 1
# a little lift on the pink outro, then fade out
gain *= np.where(t > E.T_OUTRO, 1 + 0.6 * np.clip((t - E.T_OUTRO) / 0.6, 0, 1), 1)
gain *= np.clip((E.DUR - t) / 1.4, 0, 1)
mus *= gain[:, None]

# SFX
sfx = np.zeros((N, 2), np.float32)
def put(x, at, g):
    i = int(at * SR)
    if i < 0: x = x[-i:]; i = 0
    k = min(len(x), N - i)
    if k > 0: sfx[i:i + k] += x[:k] * g
wh, sr0 = sf.read("/mnt/project-files/style-guide/assets/sfx/whoosh-dig_whoosh_06.wav", dtype="float32")
if wh.ndim == 1: wh = np.stack([wh, wh], 1)
if sr0 != SR:
    idx = np.arange(int(len(wh) * SR / sr0)) * sr0 / SR
    wh = np.stack([np.interp(idx, np.arange(len(wh)), wh[:, c]) for c in range(2)], 1).astype(np.float32)
wh /= np.abs(wh).max() + 1e-9
PEAK = 0.31
def pop(f0=880, d=0.09):
    tt = np.arange(int(d * SR)) / SR
    x = np.sin(2 * np.pi * (f0 + 600 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 38)
    return np.stack([x, x], 1).astype(np.float32)
def boom():
    tt = np.arange(int(0.6 * SR)) / SR
    x = np.sin(2 * np.pi * (52 + 90 * np.exp(-tt * 18)) * tt) * np.exp(-tt * 7)
    noise = np.random.default_rng(3).normal(0, 1, len(tt)) * np.exp(-tt * 45) * 0.35
    y = np.tanh((x + noise) * 1.6)
    return np.stack([y, y], 1).astype(np.float32)
vg = vr * 0.9
put(wh, E.M1_IN + 0.18 - PEAK, vg * 0.55)
put(wh, E.M3_IN + 0.18 - PEAK, vg * 0.55)
for tp in (E.M1_OUT, E.M3_OUT): put(wh, tp - PEAK, vg * 0.35)
put(wh, E.T_OUTRO + 0.15 - PEAK, vg * 0.45)
t_st = E.ws("ضحكوا") + 0.9
put(boom(), t_st + 0.12, vg * 0.9); put(wh, t_st + 0.05 - PEAK, vg * 0.3)
for w_ in ("دكتور", "تكلفة", "كيف"): put(pop(900), E.ws(w_) - 0.12 + 0.18, vg * 0.22)
put(pop(1250, 0.07), E.ws("بتوصلنا") + 0.2, vg * 0.2)
put(pop(700, 0.1), E.ws("الفيلر", 1) + 0.18, vg * 0.18)
put(pop(700, 0.1), E.ws("حقن") + 0.1, vg * 0.18)

for nm, x in (("voice_doctor", voice), ("music_bed", mus), ("sfx", sfx)): sf.write(A + nm + ".wav", x, SR)
mix = voice + mus + sfx
sf.write("/home/user/sm/mix_pre.wav", mix, SR)
ff(["-i", "/home/user/sm/mix_pre.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", A + "mix_final.wav"])
print("audio ok", E.DUR)
