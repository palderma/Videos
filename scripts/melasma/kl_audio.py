#!/usr/bin/env python3
"""Audio for «أسباب فشل علاج الكلف»: doctor voice (cut at pauses only, light clean), calm music bed ducked ~18 dB under
the voice, 6 restrained SFX. Writes pkg/audio/{voice_doctor,music_bed,sfx,mix_final}.wav (48 kHz stereo, comp length)."""
import os, sys, subprocess, numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_edit as E
SR = 48000; A = "/home/user/klf/pkg/audio/"; os.makedirs(A, exist_ok=True)
N = int(E.DUR * SR)
def ff(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)

# voice: high-pass, gentle denoise (<= 6 dB), de-ess, 2:1 compression, loudness
ff(["-i", "/home/user/klf/voice_cut_raw.wav", "-af",
    "highpass=f=80,afftdn=nr=6:nf=-45,deesser=i=0.35,acompressor=threshold=-21dB:ratio=2:attack=10:release=140:makeup=1.5,loudnorm=I=-16:TP=-2:LRA=8",
    "-ar", "48000", "-ac", "2", "/home/user/klf/voice_proc.wav"])
v, _ = sf.read("/home/user/klf/voice_proc.wav", dtype="float32")
voice = np.zeros((N, 2), np.float32); n = min(N, len(v)); voice[:n] = v[:n]
i0 = int((E.SPEECH_END + 0.25) * SR); i1 = int((E.T_OUTRO) * SR)
voice[i0:i1] *= np.linspace(1, 0, i1 - i0)[:, None] ** 2; voice[i1:] = 0      # room tone fades after his last word

# music bed (the reels bed from the user's library)
ff(["-i", "/mnt/project-files/style-guide/assets/music/sequence-04.mp3", "-t", str(E.DUR + 1), "-ar", "48000", "-ac", "2", "/home/user/klf/music_raw.wav"])
m, _ = sf.read("/home/user/klf/music_raw.wav", dtype="float32")
mus = np.zeros((N, 2), np.float32); n = min(N, len(m)); mus[:n] = m[:n]
mus /= (np.sqrt(np.mean(mus ** 2)) + 1e-9)
env = np.sqrt(np.convolve(np.mean(voice ** 2, 1), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same"))
vr = np.sqrt(np.mean(voice[np.abs(voice[:, 0]) > 1e-4] ** 2))
speech = np.clip(env / (vr * 0.35), 0, 1)
sm = np.convolve(speech, np.ones(int(0.6 * SR)) / int(0.6 * SR), "same")       # slow: no pumping
g_db = -19.0 + (1 - sm) * 4.0
t = np.arange(N) / SR
g_db = g_db - 2.0 * np.exp(-((t - E.T["khate"]) / 0.6) ** 2)                    # small dip on «الخاطئ»
gain = 10 ** (g_db / 20) * vr
gain *= 0.55 + 0.45 * np.clip(t / 1.0, 0, 1)                                     # present from frame 1, settles in 1 s
gain *= np.where(t > E.SPEECH_END + 0.15, 1 + 0.41 * np.clip((t - E.SPEECH_END - 0.15) / 0.6, 0, 1), 1)   # +3 dB after his last word
gain *= np.clip((E.DUR - t) / 1.0, 0, 1)
mus *= gain[:, None]

# SFX (approved whoosh + home-made soft impact / paper swish: no third-party rights)
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
def soft_impact():
    tt = np.arange(int(0.9 * SR)) / SR
    x = np.sin(2 * np.pi * (48 + 60 * np.exp(-tt * 14)) * tt) * np.exp(-tt * 5.5)
    body = np.sin(2 * np.pi * 196 * tt) * np.exp(-tt * 9) * 0.12
    y = np.tanh((x + body) * 1.3) * np.clip(tt / 0.004, 0, 1)
    return np.stack([y, y], 1).astype(np.float32)
def swish():
    rng = np.random.default_rng(7); tt = np.arange(int(0.32 * SR)) / SR
    nz = rng.normal(0, 1, len(tt)); nz = np.convolve(nz, np.ones(6) / 6, "same") - np.convolve(nz, np.ones(60) / 60, "same")
    env_ = np.sin(np.pi * np.clip(tt / 0.32, 0, 1)) ** 2
    y = nz * env_ * 0.5
    return np.stack([y, y * 0.9], 1).astype(np.float32)
vg = vr * 0.9
db = lambda d: 10 ** (d / 20)
put(soft_impact(), E.T["kalaf"] - 0.02, vg * db(-6))           # hook title
put(wh, E.T["min"] + 0.05 - PEAK, vg * db(-8))                  # list header «3 أسباب»
put(swish(), E.T["taqsheer"] + 0.08, vg * db(-12))              # fast peel
put(soft_impact(), E.T["khate"] - 0.02, vg * db(-7))            # «الخاطئ»
put(wh, E.T_FLASH - PEAK, vg * db(-10))                         # user's flash
put(soft_impact(), E.T["mish"] - 0.02, vg * db(-5))             # «مش للتجربة»
put(wh, E.T_WIPE + 0.2 - PEAK, vg * db(-8))                     # outro circle

for nm, x in (("voice_doctor", voice), ("music_bed", mus), ("sfx", sfx)): sf.write(A + nm + ".wav", x, SR)
sf.write("/home/user/klf/mix_pre.wav", voice + mus + sfx, SR)
ff(["-i", "/home/user/klf/mix_pre.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", A + "mix_final.wav"])
print("audio ok", E.DUR)
