#!/usr/bin/env python3
"""Square 1x1 from the user's own finished 9x16 «الشد المائي خرافة - جاهز.mp4» (keeps every edit they made):
doctor parts = a crisp 1:1 window (y 420-1500, no scaling); motion scene «كثير مسجات» and the messenger ending =
a wider window (y 400-1700) scaled down, sides filled with a soft blur of the same frame; window changes glide under
the scene fades; square brand frame on top; ends in the square pink outro. Audio = the user's mix, untouched."""
import subprocess, numpy as np, cv2
SRC = "/mnt/project-files/الشد المائي خرافة - جاهز.mp4"
OUTRO = "/mnt/project-files/style-guide/assets/خاتمة-مربع-1x1.mp4"
FRAME = "/mnt/project-files/style-guide/assets/templates/frame-1x1.png"
OUT = "/home/user/sm/sq_noaudio.mp4"
S = 1080
# window = (top y in the 9x16, height, top offset in the square); the window is scaled to fill 1080 - offset
D = (360.0, 1160.0, 0.0)          # doctor
W1 = (340.0, 1360.0, 60.0)        # «كثير مسجات» scene: keep its title clear of the logo band
W3 = (400.0, 1100.0, 110.0)       # «بمسمّياتها» scene: its logo sits under the brand band
WM = (380.0, 1300.0, 0.0)         # messenger button + cursor
KEYS = [(0, D), (5.95, D), (6.75, W1), (12.92, W1), (13.32, D), (20.41, D), (21.11, W3), (24.41, W3), (24.81, D), (31.2, D), (31.95, WM), (99, WM)]
T_OUT, FADE = 33.36, 0.7
def ss(x): x = min(max(x, 0), 1); return x * x * x * (x * (6 * x - 15) + 10)
def win(t):
    for (a, pa), (b, pb) in zip(KEYS, KEYS[1:]):
        if a <= t < b:
            q = ss((t - a) / (b - a)) if pa != pb else 0
            return tuple(x + (y - x) * q for x, y in zip(pa, pb))
    return KEYS[-1][1]
fr = cv2.imread(FRAME, cv2.IMREAD_UNCHANGED).astype(np.float32); fa = fr[..., 3:4] / 255; fc = fr[..., :3]
ys = np.arange(S, dtype=np.float32)[:, None, None]
top = (1 - np.clip((ys - 40) / 300, 0, 1)) ** 1.6 * 0.5          # soft top shade for the logo band
def square(f):
    y0, h, off = win(cur_t)
    sc = (S - off) / h; w = S * sc                                # foreground size
    reg = f[int(round(y0)):int(round(y0 + h))]
    if w >= S - 0.5 and off < 0.5:
        out = cv2.resize(reg, (S, S), interpolation=cv2.INTER_AREA if h > S else cv2.INTER_LINEAR).astype(np.float32)
    else:
        c = max(0, int((h - S) / 2)); bg = reg[c:c + S] if h >= S else reg
        bg = cv2.resize(cv2.resize(bg, (S // 4, S // 4), interpolation=cv2.INTER_AREA), (S // 4, S // 4))
        bg = cv2.resize(cv2.GaussianBlur(bg, (0, 0), 7), (S, S)).astype(np.float32) * 0.85
        fw = min(S, int(round(w))); fg = cv2.resize(reg, (int(round(w)), S - int(round(off))), interpolation=cv2.INTER_AREA).astype(np.float32)
        if fg.shape[1] > S: c2 = (fg.shape[1] - S) // 2; fg = fg[:, c2:c2 + S]
        x0 = (S - fg.shape[1]) // 2; yo = int(round(off))
        m = np.ones(fg.shape[:2], np.float32); e = 22
        ramp = np.linspace(0, 1, e, dtype=np.float32)
        if fg.shape[1] < S: m[:, :e] *= ramp; m[:, -e:] *= ramp[::-1]
        if yo > 0: m[:e, :] *= ramp[:, None]
        out = bg; sub = out[yo:yo + fg.shape[0], x0:x0 + fg.shape[1]]
        sub[:] = sub * (1 - m[..., None]) + fg * m[..., None]
    out = out * (1 - top) + np.array((9, 2, 22), np.float32) * top
    return out
cap = cv2.VideoCapture(SRC); oc = cv2.VideoCapture(OUTRO)
N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{S}x{S}", "-r", "30", "-i", "-",
                      "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
held = None
for i in range(N):
    cur_t = t = i / 30
    ok, f = cap.read()
    if not ok: break
    if t <= T_OUT or held is None:
        sq = square(f)
        if t <= T_OUT: held = sq
    else:
        sq = held
    if t > T_OUT:
        ok2, o = oc.read()
        k = ss((t - T_OUT) / FADE)
        sq = sq * (1 - k) + o.astype(np.float32) * k
        fa_k = 1 - k
    else:
        fa_k = 1
    sq = sq * (1 - fa * fa_k) + fc * fa * fa_k
    p.stdin.write(np.clip(sq, 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait(); print("frames", i + 1)
