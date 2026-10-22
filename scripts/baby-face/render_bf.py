#!/usr/bin/env python3
"""Palderma reel renderer: «البيبي فيس - جلسة الدراكولا» (raw «Comp 1.mp4»), built in the approved
«احدث 3 معلومات عن البوتوكس» style: doctor on his original (user-keyed) clinic background, PiP hook card, three motion
chapters (الجلسة / التوقيت / النقاهة) with a chapter pill + progress dots, drifting brand gradient, ghost number and the
user's wine 6-petal flower; hand-drawn circles for emphasis (no underlines); the user's flash file for returns to the
doctor; messages overlay held on the clicked button, then the pink outro. New model: Pexels 19959613 (pexels-hijab6).
Usage: render_bf.py [--sq] [--t=1.0,2.5] [--range=a,b --out=file]"""
import subprocess, sys, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bf_timeline import RAW, OFF, RAW_END, WORDS, GROUPS, gfind, wfind, T_PIP_IN, T_PIP_OUT, TB, T_MSG, MSG_HOLD, T_OUT, OUTRO_LEN, DUR

SQ = "--sq" in sys.argv
ONLY = None; RANGE = None; OUT = None
for a in sys.argv:
    if a.startswith("--t="): ONLY = [float(x) for x in a[4:].split(",")]
    if a.startswith("--range="): RANGE = [int(x) for x in a[8:].split(",")]
    if a.startswith("--out="): OUT = a[6:]
W, H, FPS = (1080, 1080, 30) if SQ else (1080, 1920, 30)
FONT = "/home/user/Videos/brand/fonts/thmanyahsans-%s.otf"
ASSETS = "/mnt/project-files/style-guide/assets"
BROLL = "/mnt/project-files/edits/broll/pexels-hijab"
MSG = "/mnt/project-files/خام الخاتمة رسائل الصفحة مربع.mov" if SQ else "/mnt/project-files/خام الخاتمة رسائل الصفحة.mov"
OUTRO = ASSETS + ("/خاتمة-مربع-1x1.mp4" if SQ else "/خاتمة-عمودي-9x16.mp4")
WORK = os.path.join(HERE, "..", "comp1_work"); os.makedirs(WORK, exist_ok=True)

BURG = (108, 13, 43); PINK = (243, 165, 189); WHITE = (255, 255, 255); DEEP = (74, 6, 28)
if SQ:
    L = dict(cap=905, kw=830, face_y=470, card=(330, 245, 750, 605), title=738, sub=846, nums=605, nfs=86, sfs=58, ngap=118,
             chap=246, pcard=(270, 296, 810, 586), ptitle=645, pfs=54, rows=(752, 866), row_wh=(600, 96), lfs=42,
             f2card=(310, 300, 770, 660), f2t=745, f2s=850, bt=360, bars=(530, 700), bar_wh=(700, 140), bpill=860,
             p3=760, ghost=(820, 560, 640), c2t=380, c2rows=(560, 740), sc_wh=(660, 140), c3t=380, c3rows=(570, 750), ic_y=0, endpill=0, msg_dy=30, kw_msg=222, msg_fy=420, msg_z=1.0)
else:
    L = dict(cap=1505, kw=1385, face_y=700, card=(190, 500, 890, 1100), title=1290, sub=1418, nums=1100, nfs=112, sfs=68, ngap=150,
             chap=410, pcard=(170, 520, 910, 1060), ptitle=1150, pfs=64, rows=(1312, 1468), row_wh=(740, 132), lfs=50,
             f2card=(170, 560, 910, 1120), f2t=1235, f2s=1365, bt=720, bars=(930, 1120), bar_wh=(820, 160), bpill=1300,
             p3=1300, ghost=(820, 900, 900), c2t=660, c2rows=(1150, 1380), sc_wh=(820, 175), c3t=660, c3rows=(1150, 1370), ic_y=900, endpill=1590, msg_dy=0, kw_msg=860, msg_fy=560, msg_z=1.30)
CAP_Y = L["cap"]

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)      # smootherstep
def back_out(x, s=1.1):
    x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def prog(t, a, d): return clamp((t - a) / d)
def ws(w, n=0): return wfind(w, n)["s"]

# ---------------- text ----------------
_fonts = {}
def font(weight, size):
    k = (weight, size)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FONT % weight, size, layout_engine=ImageFont.Layout.RAQM)
    return _fonts[k]
_tc = {}
def text_img(txt, size, weight="Bold", fill=WHITE, shadow=True, grad=None, pad=40):
    k = (txt, size, weight, fill, shadow, grad, pad)
    if k in _tc: return _tc[k]
    f = font(weight, size)
    dr = "ltr" if all(ord(c) < 128 for c in txt) else "rtl"
    asc, desc = f.getmetrics()
    w = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(txt, font=f, direction=dr, language="ar")) + pad * 2
    h = asc + desc + pad * 2
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((pad, pad), txt, font=f, fill=255, direction=dr, language="ar")
    if grad:
        c1, c2 = np.array(grad[0], float), np.array(grad[1], float)
        xs = np.linspace(0, 1, w)[None, :, None]
        col = (c2 * (1 - xs) + c1 * xs) * np.ones((h, 1, 1))
        fg = Image.fromarray(col.astype(np.uint8), "RGB").convert("RGBA")
    else:
        fg = Image.new("RGBA", (w, h), fill + (255,))
    fg.putalpha(mask)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w, h), (30, 0, 12, 0)); sh.putalpha(mask.point(lambda v: v * (0.8 if grad else 0.5)))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14 if grad else 8)), (0, 3))
    out.alpha_composite(fg)
    _tc[k] = np.array(out); return _tc[k]

def ink(t):
    ys, xs = np.nonzero(t[..., 3] > 8); return t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def box_img(txt, size, bg, fg, weight="Bold", padx=46, pady=12, radius=26, minw=0):
    """rounded box, text centred on its ink box both ways; same height for every box of this size"""
    k = ("box", txt, size, bg, fg, weight, padx, pady, radius, minw)
    if k in _tc: return _tc[k]
    t = ink(text_img(txt, size, weight, fill=fg, shadow=False, pad=20))
    th, tw = t.shape[:2]
    h = int(round(size * 1.05)) + pady * 2
    w = max(tw + padx * 2, minw)
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), radius * 2, fill=bg + (255,))
    im = im.resize((w, h), Image.LANCZOS)
    im.alpha_composite(Image.fromarray(t), ((w - tw) // 2, (h - th) // 2))
    _tc[k] = np.array(im); return _tc[k]

def shadowed(img, r=18, a=0.35, dy=10, cache=True):
    """soft drop shadow under a card/pill (cache=False for per-frame images: id() gets reused)"""
    k = ("sh", id(img), r, a, dy)
    if cache and k in _tc: return _tc[k]
    h, w = img.shape[:2]; p = r * 3
    out = np.zeros((h + 2 * p, w + 2 * p, 4), np.uint8)
    sh = np.zeros((h + 2 * p, w + 2 * p), np.float32); sh[p + dy:p + dy + h, p:p + w] = img[..., 3] / 255.0 * a
    sh = cv2.GaussianBlur(sh, (0, 0), r)
    out[..., :3] = np.array(DEEP, np.uint8); out[..., 3] = (sh * 255).astype(np.uint8)
    o = Image.fromarray(out); o.alpha_composite(Image.fromarray(img), (p, p))
    if not cache: return np.array(o)
    _tc[k] = np.array(o); return _tc[k]

# ---------------- compositing (sub-pixel) ----------------
def over(dst, src, cx, cy, alpha=1.0, scale=1.0, blur=0.0, anchor="c"):
    if alpha <= 0.003 or scale <= 0.01: return
    h, w = src.shape[:2]
    if anchor == "c": x0, y0 = cx - w * scale / 2, cy - h * scale / 2
    else: x0, y0 = cx, cy
    bx0, by0 = int(math.floor(x0)) - 2, int(math.floor(y0)) - 2
    bx1, by1 = int(math.ceil(x0 + w * scale)) + 2, int(math.ceil(y0 + h * scale)) + 2
    xa, ya, xb, yb = max(0, bx0), max(0, by0), min(W, bx1), min(H, by1)
    if xa >= xb or ya >= yb: return
    M = np.float32([[scale, 0, x0 - xa], [0, scale, y0 - ya]])
    s = cv2.warpAffine(src, M, (xb - xa, yb - ya), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if blur > 0.3:
        pad = int(blur * 3)
        xa2, ya2, xb2, yb2 = max(0, xa - pad), max(0, ya - pad), min(W, xb + pad), min(H, yb + pad)
        big = np.zeros((yb2 - ya2, xb2 - xa2, 4), np.uint8); big[ya - ya2:yb - ya2, xa - xa2:xb - xa2] = s
        s = cv2.GaussianBlur(big, (0, 0), blur); xa, ya, xb, yb = xa2, ya2, xb2, yb2
    sub = s.astype(np.float32); a = sub[..., 3:4] / 255.0 * alpha
    dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + sub[..., :3] * a

_rm = {}
def rounded_mask(w, h, r):
    k = (w, h, r)
    if k not in _rm:
        m = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=255)
        _rm[k] = np.array(m.resize((w, h), Image.LANCZOS), np.float32)[..., None] / 255
    return _rm[k]

def put_card(fr, img, x0, y0, r=40, shadow=0.35):
    """paste an RGB float image as a rounded card with a soft shadow"""
    h, w = img.shape[:2]; x0, y0 = int(round(x0)), int(round(y0))
    if shadow > 0:
        sh = np.zeros((H, W), np.float32)
        sh[max(0, y0 + 22):min(H, y0 + h + 22), max(0, x0 + 8):min(W, x0 + w - 8)] = shadow
        fr *= 1 - cv2.GaussianBlur(sh, (0, 0), 24)[..., None]
    m = rounded_mask(w, h, r)
    ya, yb, xa, xb = max(0, y0), min(H, y0 + h), max(0, x0), min(W, x0 + w)
    reg = fr[ya:yb, xa:xb]; mm = m[ya - y0:yb - y0, xa - x0:xb - x0]; src = img[ya - y0:yb - y0, xa - x0:xb - x0]
    fr[ya:yb, xa:xb] = reg * (1 - mm) + src * mm

def load_rgba(p, width=None):
    im = Image.open(p).convert("RGBA")
    if width: im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    return np.array(im)

# ---------------- static layers ----------------
FRAME = load_rgba(f"{ASSETS}/templates/frame-1x1.png" if SQ else f"{ASSETS}/templates/frame-9x16.png")
yy = np.linspace(0, 1, H)[:, None, None].astype(np.float32)
if SQ:
    BOTTOM_DARK = (np.clip((yy - 0.5) / 0.48, 0, 1) ** 1.3 * 0.78).astype(np.float32)
    TOP_DARK = (np.clip((0.25 - yy) / 0.25, 0, 1) * 0.35).astype(np.float32)
else:
    BOTTOM_DARK = (np.clip((yy - 0.47) / 0.45, 0, 1) ** 1.3 * 0.86).astype(np.float32)
    TOP_DARK = (np.clip((0.2 - yy) / 0.2, 0, 1) * 0.3).astype(np.float32)

def load_bg():
    im = cv2.cvtColor(cv2.imread(os.path.join(HERE, "bg_gradient.png")), cv2.COLOR_BGR2RGB).astype(np.float32)
    if not SQ: return cv2.resize(im, (W, H))
    full = cv2.resize(im, (1080, 1920)); sq = full[:H].copy()
    want = cv2.resize(full, (W, H), interpolation=cv2.INTER_AREA).mean(1, keepdims=True)
    return np.clip(sq + (want - sq.mean(1, keepdims=True)), 0, 255)
BG = load_bg()

def grade(img):
    """warm, slightly deeper photo grade so the stock shots sit with the brand colours"""
    x = img.astype(np.float32) / 255
    x = np.clip((x - 0.5) * 1.08 + 0.5 - 0.02, 0, 1) ** 1.04
    x[..., 0] *= 1.04; x[..., 2] *= 0.94
    return np.clip(x * 255, 0, 255)

class Photo:
    def __init__(self, name, fx=0.5, fy=0.5):
        im = cv2.cvtColor(cv2.imread(os.path.join(BROLL, name + ".jpg")), cv2.COLOR_BGR2RGB)  # absolute names pass through join
        self.img = grade(im).astype(np.uint8); self.fx, self.fy = fx, fy
        self.h, self.w = self.img.shape[:2]
    def cover(self, dw, dh, z=1.0, dx=0.0, dy=0.0):
        s = max(dw / self.w, dh / self.h) * z
        cx, cy = self.fx * self.w * s, self.fy * self.h * s
        tx = min(0.0, max(dw - self.w * s, dw / 2 - cx)) + dx
        ty = min(0.0, max(dh - self.h * s, dh / 2 - cy)) + dy
        M = np.float32([[s, 0, tx], [0, s, ty]])
        return cv2.warpAffine(self.img, M, (dw, dh), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT).astype(np.float32)

BROLL2 = "/mnt/project-files/edits/broll/pexels-hijab6"   # new model for this video (Pexels shoot 19959608-25)
P = dict(face=Photo(BROLL2 + "/19959613", 0.52, 0.42), look=Photo(BROLL2 + "/19959621", 0.60, 0.35))

# ---------------- doctor ----------------
# raw reads correctly («Dr. Musa / Palderma»), already keyed by the user onto the clinic set: light grade only
GRADE = ("eq=contrast=1.05:saturation=1.03:gamma=0.98,"
         "curves=all='0/0 0.08/0.06 0.5/0.49 1/0.97',unsharp=5:5:0.35")
RW, RH = 1080, 1920
class Pipe:
    def __init__(self, cmd, shape):
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE); self.shape = shape; self.i = -1; self.last = None
    def get(self, idx):
        n = int(np.prod(self.shape))
        while self.i < idx:
            b = self.p.stdout.read(n)
            if len(b) < n: break
            self.last = np.frombuffer(b, np.uint8).reshape(self.shape); self.i += 1
        return self.last
def Doctor(start=0):
    p = Pipe(["ffmpeg", "-loglevel", "error", "-ss", f"{OFF + start / FPS:.4f}", "-i", RAW, "-vf", f"fps={FPS},{GRADE}",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], (RH, RW, 3))
    p.i = start - 1; return p
def Msg(start=0):
    ss = ["-ss", f"{start / FPS:.4f}"] if start else []
    p = Pipe(["ffmpeg", "-loglevel", "error"] + ss + ["-i", MSG, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgba", "-"], (H, W, 4))
    p.i = start - 1; return p

_ft = np.load(os.path.join(WORK, "face.npz"))       # template-tracked face centre, 10 fps, raw time
def _smooth(x, n):
    k = np.ones(n) / n; xp = np.pad(x, (n, n), mode="edge"); return np.convolve(xp, k, "same")[n:-n]
FT = _ft["T"]; FX = _smooth(_ft["X"], 21); FY = _smooth(_ft["Y"], 21) + 25; FXF = _smooth(_ft["X"], 7); FYF = _smooth(_ft["Y"], 7) + 25
FACE = {"x": 535.0, "y": 450.0}     # doctor's face in the raw frame, follows the smoothed track
TX_FREE = 160 if SQ else 0         # square: the doctor may sit smaller than the frame width (gap filled softly)
def doc_offsets(s):
    FACE_X, FACE_Y = FACE["x"], FACE["y"]
    tx = W / 2 - s * FACE_X; tx = min(TX_FREE, max(W - s * RW - TX_FREE, tx))
    mk = ease_io(prog(DOC["t"], T_MSG - 0.2, 0.8))
    ty = L["face_y"] + (L["msg_fy"] - L["face_y"]) * mk - s * FACE_Y; ty = min(0.0, max(H - s * RH, ty))
    return tx, ty
def doc_transform(img, s):
    tx, ty = doc_offsets(s)
    M = np.float32([[s, 0, tx], [0, s, ty]])
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    # square: when the smaller doctor leaves a side gap, fill it with a soft blur of the mirrored wall
    for x0, x1, gap in ((0, int(tx) + 60, tx), (int(tx + s * RW) - 60, W, W - (tx + s * RW))):
        if gap <= 0.5: continue
        x0, x1 = max(0, x0), min(W, x1)
        if x1 <= x0: continue
        reg = out[:, x0:x1]; bl = cv2.GaussianBlur(reg, (0, 0), 22) * 0.94
        xs = np.arange(x0, x1, dtype=np.float32)
        a = np.clip((tx + 40 - xs) / 60, 0, 1) if x0 == 0 else np.clip((xs - (tx + s * RW - 40)) / 60, 0, 1)
        out[:, x0:x1] = reg * (1 - a[None, :, None]) + bl * a[None, :, None]
    return out

Z0 = 1.45
T_PUNCH = ws("أهم") - 0.15
OPEN_D, SETTLE_D, PUSH_D = (1.0, 1.3, 1.8) if SQ else (0.45, 0.7, 1.2)     # square moves slower and softer
def settle(t, T, a=0.08): return a * (1 - (ease_io if SQ else ease_out)(prog(t, T, SETTLE_D)))
def zoom_v(t):
    if t < TB[1]:
        # opening glide in, slow creep while he explains, one soft push on «أهم شي» that holds
        return (Z0 + 0.30 * (1 - (ease_io if SQ else ease_out)(t / OPEN_D)) + 0.06 * ease_io(prog(t, T_PIP_OUT + 0.6, T_PUNCH - T_PIP_OUT - 0.6))
                + 0.10 * ease_io(prog(t, T_PUNCH - 0.25, PUSH_D)))
    return Z0 + 0.06 + settle(t, TB[4])
def zoom_at(t):
    z = zoom_v(t)
    if SQ: z = 1.12 + (z - Z0) * 0.55              # square: doctor a bit smaller, every zoom move gentler
    k = ease_io(prog(t, T_MSG - 0.5, 1.6))          # long glide out for the messages overlay
    return z * (1 - k) + L["msg_z"] * k
DOC = {"img": None, "t": 0.0}
def doctor(t):
    DOC["t"] = t; return doc_transform(DOC["img"], zoom_at(t))

# ---------------- living background ----------------
def bg_at(t, seed=0):
    """brand gradient with a slow drift + two soft light orbs, so motion scenes never sit still"""
    z = 1.05 + 0.015 * math.sin(t * 0.5 + seed)
    fr = shift(BG, dx=14 * math.sin(t * 0.35 + seed), dy=18 * math.cos(t * 0.3 + seed), z=z)
    o1 = blob(int(W * (0.25 + 0.06 * math.sin(t * 0.4 + seed))) // 8 * 8, int(H * 0.22) // 8 * 8, 300 if SQ else 420)
    o2 = blob(int(W * (0.8 - 0.05 * math.sin(t * 0.33))) // 8 * 8, int(H * 0.7) // 8 * 8, 340 if SQ else 480)
    glow = o1 * np.array([255, 214, 228], np.float32) * 0.22 + o2 * np.array([255, 190, 170], np.float32) * 0.14
    return 255 - (255 - fr) * (255 - glow) / 255

def ghost(fr, t, txt, t0):
    """huge translucent chapter number drifting behind the content"""
    _, y, size = L["ghost"]
    p = ease_out(prog(t, t0, 0.8))
    over(fr, ink(text_img(txt, size, "Black", shadow=False, pad=10)), W / 2, y + 10 * math.sin(t * 0.5), scale=0.96 + 0.04 * p,
         alpha=0.07 * p)

# ---- shared pieces (from render_col.py) ----
def mark(kind, size, bg, fg):
    """round badge with a drawn check or cross"""
    k = ("mark", kind, size, bg, fg)
    if k in _tc: return _tc[k]
    S2 = 4; n = size * S2; im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, n - 1, n - 1), fill=bg + (255,)); lw = int(n * 0.1)
    if kind == "ok": d.line((n * .28, n * .52, n * .44, n * .68, n * .74, n * .36), fill=fg + (255,), width=lw, joint="curve")
    else:
        d.line((n * .32, n * .32, n * .68, n * .68), fill=fg + (255,), width=lw); d.line((n * .68, n * .32, n * .32, n * .68), fill=fg + (255,), width=lw)
    _tc[k] = np.array(im.resize((size, size), Image.LANCZOS)); return _tc[k]

def mark_pill(kind, txt, size, bg, fg, mbg, mfg):
    """pill: [text  (mark)] , mark on the right (RTL reading start), whole content centred"""
    k = ("mpill", kind, txt, size, bg, fg)
    if k in _tc: return _tc[k]
    t = ink(text_img(txt, size, "Bold", fill=fg, shadow=False, pad=20)); th, tw = t.shape[:2]
    ms = int(size * 1.05); gap = int(size * 0.35); padx = int(size * 0.55)
    h = int(round(size * 1.05)) + 28; w = padx * 2 + tw + gap + ms
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), h, fill=bg + (255,))
    im = im.resize((w, h), Image.LANCZOS)
    im.alpha_composite(Image.fromarray(t), (padx, (h - th) // 2))
    im.alpha_composite(Image.fromarray(mark(kind, ms, mbg, mfg)), (w - padx - ms + int(size * 0.2), (h - ms) // 2))
    _tc[k] = shadowed(np.array(im), r=14, a=0.35, dy=8, cache=False); return _tc[k]

def white_card(w, h, r=44):
    k = ("wc", w, h, r)
    if k in _tc: return _tc[k]
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=WHITE + (255,))
    _tc[k] = np.array(im.resize((w, h), Image.LANCZOS)); return _tc[k]

# ---------------- graphic pieces ----------------
def chap_pill(n):
    """burgundy pill: three progress dots (left) + «المعلومة …» (right), whole content centred"""
    k = ("chap", n)
    if k in _tc: return _tc[k]
    fs = 44 if SQ else 50
    t = ink(text_img(CHAP[n], fs, "Bold", fill=WHITE, shadow=False, pad=20)); th, tw = t.shape[:2]
    d = int(fs * 0.36); gap = int(fs * 0.3); dots_w = 3 * d + 2 * gap; sep = int(fs * 0.7); padx = int(fs * 0.7)
    h = int(fs * 1.05) + 26; w = padx * 2 + tw + sep + dots_w
    S2 = 2; im = Image.new("RGBA", (w * S2, h * S2), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, w * S2 - 1, h * S2 - 1), h * S2 // 2, fill=BURG + (255,))
    x = padx
    for i in range(3):                       # RTL progress: the first fact is the right-most dot
        on = (2 - i) <= n
        cx = (x + d / 2) * S2; cy = h / 2 * S2; r = d / 2 * S2 * (1.0 if (2 - i) == n else 0.8)
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(PINK if on else (196, 120, 152)) + (255,))
        x += d + gap
    im = im.resize((w, h), Image.LANCZOS)
    im.alpha_composite(Image.fromarray(t), (w - padx - tw, (h - th) // 2))
    _tc[k] = shadowed(np.array(im), r=14, a=0.4, dy=8, cache=False); return _tc[k]

def chapter(fr, t, n, t0):
    p = back_out(prog(t, t0, 0.5))
    if p > 0: over(fr, chap_pill(n), W / 2, L["chap"] - 20 * (1 - min(1, p)), scale=0.85 + 0.15 * p, alpha=min(1, p * 2.5))

def arrow_badge(size):
    k = ("arr", size)
    if k in _tc: return _tc[k]
    S2 = 4; n = size * S2; im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, n - 1, n - 1), fill=BURG + (255,)); lw = int(n * 0.1)
    d.line((n * .5, n * .74, n * .5, n * .28), fill=WHITE + (255,), width=lw)
    d.line((n * .3, n * .46, n * .5, n * .26, n * .7, n * .46), fill=WHITE + (255,), width=lw, joint="curve")
    _tc[k] = np.array(im.resize((size, size), Image.LANCZOS)); return _tc[k]

def bar_card(label, frac, w, h, fs, arrow=0.0, note=None):
    """white card: label at the right; a track with a gradient fill growing right->left; arrow badge at the left"""
    im = Image.fromarray(white_card(w, h, r=min(36, h // 2)).copy())
    t = Image.fromarray(ink(text_img(label, fs, "Bold", fill=BURG, shadow=False, pad=20)))
    pad = int(h * 0.3)
    if note is None:                                # one line: [arrow][track ......][label]
        im.alpha_composite(t, (w - pad - t.width, (h - t.height) // 2))
        ab = int(h * 0.56); tx0 = pad + ab + int(pad * 0.6); tx1 = w - pad - t.width - int(pad * 0.9); ty = h // 2
    else:                                           # two lines: label on top, track below
        im.alpha_composite(t, (w - pad - t.width, int(h * 0.30) - t.height // 2))
        ab = int(h * 0.36); tx0 = pad + ab + int(pad * 0.5); tx1 = w - pad; ty = int(h * 0.70)
    th = max(12, int(h * 0.16)); S2 = 2
    tr = Image.new("RGBA", ((tx1 - tx0) * S2, th * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(tr)
    d.rounded_rectangle((0, 0, (tx1 - tx0) * S2 - 1, th * S2 - 1), th * S2 // 2, fill=(248, 222, 231, 255))
    fw = int((tx1 - tx0) * S2 * clamp(frac))
    if fw > th * S2:
        g = np.zeros((th * S2, fw, 4), np.uint8); xs = np.linspace(0, 1, fw)[None, :, None]
        g[..., :3] = (np.array(PINK) * (1 - xs) + np.array((170, 34, 84)) * xs).astype(np.uint8); g[..., 3] = 255
        m = Image.new("L", (fw, th * S2), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, fw - 1, th * S2 - 1), th * S2 // 2, fill=255)
        gi = Image.fromarray(g); gi.putalpha(m); tr.alpha_composite(gi, ((tx1 - tx0) * S2 - fw, 0))
    tr = tr.resize((tx1 - tx0, th), Image.LANCZOS); im.alpha_composite(tr, (tx0, ty - th // 2))
    out = shadowed(np.array(im), r=16, a=0.35, dy=10, cache=False)
    if arrow > 0:
        a = arrow_badge(ab); sc = back_out(arrow, 1.8)
        p = (out.shape[1] - w) // 2
        over_rgba(out, a, p + pad + ab / 2, p + ty, sc)
    return out

def over_rgba(dst, src, cx, cy, scale):
    """composite RGBA onto an RGBA layer (small badges inside cards)"""
    if scale <= 0.02: return
    s = cv2.resize(src, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = s.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    a = s[..., 3:4].astype(np.float32) / 255; reg = dst[y0:y0 + h, x0:x0 + w].astype(np.float32)
    rgb = reg[..., :3] * (1 - a) + s[..., :3] * a; al = reg[..., 3:4] + (255 - reg[..., 3:4]) * a
    dst[y0:y0 + h, x0:x0 + w] = np.concatenate([rgb, al], 2).astype(np.uint8)

_face = {}
def face_icon(r, lines, relax):
    """white disc with a line-art face; forehead lines fade (lines 1->0), brows relax (relax 0->1)"""
    k = (r, round(lines * 20), round(relax * 20))
    if k in _face: return _face[k]
    S2 = 3; n = 2 * r * S2; im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, n - 1, n - 1), fill=WHITE + (255,))
    u = n / 200; lw = max(2, int(5.5 * u)); C = BURG + (255,)
    def P(*xs): return [x * u for x in xs]
    d.ellipse(P(52, 34, 148, 166), outline=C, width=lw)                         # head
    by = 82 - 6 * (1 - relax)                                                   # brows lift when tense
    d.arc(P(66, by - 4, 94, by + 14), 200, 340, fill=C, width=lw)
    d.arc(P(106, by - 4, 134, by + 14), 200, 340, fill=C, width=lw)
    d.arc(P(70, 92, 92, 104), 20, 160, fill=C, width=lw)                        # closed, calm eyes
    d.arc(P(108, 92, 130, 104), 20, 160, fill=C, width=lw)
    d.arc(P(95, 112, 105, 122), 300, 60, fill=C, width=lw)                     # nose
    d.arc(P(84, 126, 116, 146), 20, 160, fill=C, width=lw)                       # soft smile
    if lines > 0.02:
        lay = Image.new("RGBA", (n, n), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for i, y in enumerate((50, 59, 68)):
            pts = []
            for j in range(13):
                x = 74 + j * 4.3; pts += [x, y + 2.2 * math.sin(j * 1.2 + i)]
            dl.line(P(*pts), fill=PINK[:3] + (255,) if i == 1 else C, width=max(2, int(4 * u)), joint="curve")
        a = np.array(lay); a[..., 3] = (a[..., 3] * lines).astype(np.uint8); im.alpha_composite(Image.fromarray(a))
    _face[k] = shadowed(np.array(im.resize((2 * r, 2 * r), Image.LANCZOS)), r=20, a=0.4, dy=12, cache=False); return _face[k]

def sparkle(fr, cx, cy, p, size):
    """four-point twinkle that pops and fades"""
    if not (0 < p < 1): return
    a = math.sin(p * math.pi); s = size * (0.5 + 0.7 * ease_out(p))
    k = ("spk",)
    if k not in _tc:
        S2 = 400; im = Image.new("RGBA", (S2, S2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = S2 / 2
        d.polygon([(c, 0), (c + 26, c - 26), (S2, c), (c + 26, c + 26), (c, S2), (c - 26, c + 26), (0, c), (c - 26, c - 26)], fill=(255, 255, 255, 255))
        _tc[k] = np.array(im.filter(ImageFilter.GaussianBlur(3)))
    over(fr, _tc[k], cx, cy, alpha=a, scale=s / 400)


def bar_card2(label, frac, w, h, fs):
    """white card: label centred on top, a centred track below whose gradient fill grows right->left (RTL),
    with a soft glowing head; everything symmetric about the card centre"""
    S2 = 2; im = Image.fromarray(white_card(w, h, r=min(36, h // 3)).copy())
    t = Image.fromarray(ink(text_img(label, fs, "Bold", fill=BURG, shadow=False, pad=20)))
    im.alpha_composite(t, ((w - t.width) // 2, int(h * 0.34) - t.height // 2))
    pad = int(w * 0.09); tx0, tx1 = pad, w - pad; ty = int(h * 0.76); th = max(10, int(h * 0.11))
    tw = tx1 - tx0
    tr = Image.new("RGBA", (tw * S2, th * S2), (0, 0, 0, 0)); d = ImageDraw.Draw(tr)
    d.rounded_rectangle((0, 0, tw * S2 - 1, th * S2 - 1), th * S2 // 2, fill=(248, 222, 231, 255))
    fw = int(tw * S2 * clamp(frac))
    if fw > th * S2:
        g = np.zeros((th * S2, fw, 4), np.uint8); xs = np.linspace(0, 1, fw)[None, :, None]
        g[..., :3] = (np.array((170, 34, 84)) * (1 - xs) + np.array(PINK) * xs).astype(np.uint8); g[..., 3] = 255
        m = Image.new("L", (fw, th * S2), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, fw - 1, th * S2 - 1), th * S2 // 2, fill=255)
        gi = Image.fromarray(g); gi.putalpha(m); tr.alpha_composite(gi, (tw * S2 - fw, 0))
    tr = tr.resize((tw, th), Image.LANCZOS); im.alpha_composite(tr, (tx0, ty - th // 2))
    if frac > 0.03:                                  # glowing head at the end of the fill
        hx = tx1 - tw * clamp(frac) + th / 2; R = th * 1.5
        gl = Image.new("RGBA", (int(R * 4), int(R * 4)), (0, 0, 0, 0))
        ImageDraw.Draw(gl).ellipse((R, R, R * 3, R * 3), fill=PINK + (200,)); gl = gl.filter(ImageFilter.GaussianBlur(R * 0.45))
        im.alpha_composite(gl, (int(hx - R * 2), int(ty - R * 2)))
        dot = Image.new("RGBA", (th * 4, th * 4), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((0, 0, th * 4 - 1, th * 4 - 1), fill=WHITE + (255,))
        dot = dot.resize((int(th * 1.5), int(th * 1.5)), Image.LANCZOS); im.alpha_composite(dot, (int(hx - dot.width / 2), int(ty - dot.height / 2)))
    return shadowed(np.array(im), r=16, a=0.35, dy=10, cache=False)

_ex = {}
def expr_card(w, h, sig, flat, glow):
    """«brain forgets the expression»: signal-strength bars fade out (top), three expression lines
    relax from waves to straight lines (middle), then a soft light sweep; all centred"""
    k = (w, h, round(sig * 8), round(flat * 30), round(glow * 24))
    if k in _ex: return _ex[k]
    S2 = 2; n = (w * S2, h * S2)
    im = Image.new("RGBA", n, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, n[0] - 1, n[1] - 1), 44 * S2, fill=WHITE + (255,))
    # top: «إشارة الدماغ» + 4 signal bars, centred as one group
    fs = int(h * 0.075)
    txt = Image.fromarray(ink(text_img("إشارة الدماغ", fs * S2, "Bold", fill=BURG, shadow=False, pad=20)))
    bw, bg_ = int(fs * 0.34) * S2, int(fs * 0.2) * S2; bh = int(fs * 1.0) * S2; icw = 4 * bw + 3 * bg_; gap = int(fs * 0.6) * S2
    gw = icw + gap + txt.width; gx = (n[0] - gw) // 2; cy = int(h * 0.17) * S2
    for i in range(4):
        hh = int(bh * (0.4 + 0.2 * i)); x = gx + i * (bw + bg_)
        on = clamp(sig - i)
        col = tuple(int(c1 * on + c2 * (1 - on)) for c1, c2 in zip(BURG, (238, 214, 224)))
        d.rounded_rectangle((x, cy + bh // 2 - hh, x + bw, cy + bh // 2), bw // 3, fill=col + (255,))
    im.alpha_composite(txt, (gx + icw + gap, cy - txt.height // 2))
    # divider
    d.line((int(n[0] * 0.2), int(h * 0.31) * S2, int(n[0] * 0.8), int(h * 0.31) * S2), fill=(244, 226, 233, 255), width=2 * S2)
    # middle: three expression lines, waves -> straight
    amp = h * 0.045 * (1 - flat) * S2; x0, x1 = n[0] * 0.2, n[0] * 0.8
    for j, (yy, col) in enumerate(((0.47, BURG), (0.60, (214, 102, 142)), (0.73, BURG))):
        pts = []
        for q in range(81):
            x = x0 + (x1 - x0) * q / 80; ph = q / 80 * math.pi * 4 + j * 0.9
            env = math.sin(q / 80 * math.pi) ** 0.8
            pts.append((x, h * yy * S2 + amp * env * math.sin(ph)))
        d.line(pts, fill=col + (255,), width=int(h * 0.022) * S2, joint="curve")
        r = int(h * 0.011) * S2
        for (ex, ey) in (pts[0], pts[-1]): d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=col + (255,))
    # bottom label fades from «تعبير» to «ناعم» as the lines relax
    for word, a in (("خطوط التعبير", 1 - flat), ("بشرة مرتاحة", flat)):
        if a < 0.02: continue
        tw = Image.fromarray(ink(text_img(word, int(fs * 0.95) * S2, "Bold", fill=(184, 120, 146), shadow=False, pad=20)))
        arr = np.array(tw); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
        im.alpha_composite(Image.fromarray(arr), ((n[0] - tw.width) // 2, int(h * 0.88) * S2 - tw.height // 2))
    im = im.resize((w, h), Image.LANCZOS)
    if 0 < glow < 1:                                 # diagonal soft light sweep, clipped to the card
        a = np.array(im).astype(np.float32); yy_, xx_ = np.mgrid[0:h, 0:w]
        c = -0.3 * w + glow * 1.6 * w; band = np.exp(-(((xx_ + yy_ * 0.5) - c) / (w * 0.12)) ** 2) * math.sin(glow * math.pi)
        a[..., :3] = a[..., :3] * (1 - band[..., None] * 0.35) + np.array((255, 205, 222)) * band[..., None] * 0.35
        im = Image.fromarray(a.astype(np.uint8))
    _ex[k] = shadowed(np.array(im), r=22, a=0.4, dy=14, cache=False); return _ex[k]

def rise(fr, img, y, p, scale0=0.94):
    """centred entry: fade + small rise + scale, never off the centre line"""
    if p <= 0: return
    e = ease_out(p); over(fr, img, W / 2, y + 26 * (1 - e), alpha=min(1, p * 1.6), scale=scale0 + (1 - scale0) * e)

# ---------------- scenes ----------------
def Ly(v, sq): return sq if SQ else v
ICONS = os.path.join(WORK, "icons")
def icon_img(name, size, color=BURG, stroke=1.8):
    k = ("ic", name, size, color, stroke)
    if k in _tc: return _tc[k]
    import cairosvg, io
    svg = open(os.path.join(ICONS, name + ".svg")).read()
    svg = svg.replace("currentColor", "#%02x%02x%02x" % color).replace('stroke-width="2"', f'stroke-width="{stroke}"')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size * 2, output_height=size * 2)
    _tc[k] = np.array(Image.open(io.BytesIO(png)).convert("RGBA").resize((size, size), Image.LANCZOS)); return _tc[k]

def disc(size, fill):
    k = ("disc", size, fill)
    if k in _tc: return _tc[k]
    im = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=fill + (255,))
    _tc[k] = np.array(im.resize((size, size), Image.LANCZOS)); return _tc[k]

def hand_circle(fr, cx, cy, rw, rh, t0, t, fo=1.0, dur=0.5, col=WHITE, th=6):
    """hand-drawn emphasis loop (user rule: circle the key words, never underline)"""
    p = ease_io(prog(t, t0, dur))
    if p <= 0 or fo <= 0: return
    n = 140; ang0 = -2.6
    ang = ang0 - np.linspace(0, 2 * math.pi * 1.08 * p, max(2, int(n * p)))
    wob = 1 + 0.035 * np.sin(ang * 3 + 1.3) + 0.05 * (ang0 - ang) / (2 * math.pi)
    pts = np.stack([cx + np.cos(ang) * rw * wob, cy + np.sin(ang) * rh * wob], 1)
    x0, y0 = int(pts[:, 0].min() - 30), int(pts[:, 1].min() - 30)
    x1, y1 = int(pts[:, 0].max() + 30), int(pts[:, 1].max() + 30)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x0 >= x1 or y0 >= y1: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    q = np.round((pts - [x0, y0]) * 8).astype(np.int32)
    cv2.polylines(m, [q], False, 255, int(th), cv2.LINE_AA, shift=3)
    a = m.astype(np.float32) / 255; gl = cv2.GaussianBlur(a, (0, 0), 8) * 0.7
    sub = fr[y0:y1, x0:x1]
    sub[:] = sub * (1 - gl[..., None] * fo) + np.array(PINK, np.float32) * gl[..., None] * fo
    sub[:] = sub * (1 - a[..., None] * fo) + np.array(col, np.float32) * a[..., None] * fo

FLOWER_PNG = ASSETS + "/وردة-6-بتلات.png"     # the user's 6-petal flower, coloured wine, slow soft motion
def make_flower(size=1200):
    im = np.array(Image.open(FLOWER_PNG).convert("RGBA"), np.float32) / 255
    m = im[..., 3] * np.clip((0.85 - im[..., :3].mean(-1)) / 0.5, 0, 1)
    ys, xs = np.nonzero(m > 0.5); cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    half = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 * 1.04
    M = np.float32([[size / (2 * half), 0, size / 2 - cx * size / (2 * half)], [0, size / (2 * half), size / 2 - cy * size / (2 * half)]])
    return cv2.GaussianBlur(cv2.warpAffine(m, M, (size, size), flags=cv2.INTER_AREA), (0, 0), 1.2)
FLOWER = make_flower()
def flowers(fr, t):
    s = 0.62 if SQ else 0.9
    for px, py, a0, sp, ph in ((W + 40, -60, 12, 1.0, 0.0), (-60, H + 40, 40, -0.8, 1.7)):
        br = 1 + 0.035 * math.sin(t * 0.9 + ph)
        M = cv2.getRotationMatrix2D((600, 600), a0 + sp * t, s * br)
        M[0, 2] += px + 14 * math.sin(t * 0.5 + ph) - 600; M[1, 2] += py + 10 * math.cos(t * 0.45 + ph) - 600
        a = cv2.warpAffine(FLOWER, M, (W, H))[..., None] * 0.30
        fr[:] = fr * (1 - a) + np.array(DEEP, np.float32) * a

def motion_bg(t, seed, num, t0):
    fr = bg_at(t, seed); flowers(fr, t); ghost(fr, t, num, t0); return fr

def sparkles(fr, t, t0, pts, size):
    for i, (x, y) in enumerate(pts): sparkle(fr, x, y, prog(t, t0 + i * 0.12, 0.9), size)

def pip_scene(t):
    """hook: doctor shrinks into a rounded card (face centred, headroom); «البيبي فيس» title and the
    «حلم كل صبية» pill below with twinkles; one centred column"""
    doc = doctor(t); fr = bg_at(t); flowers(fr, t)
    k = ease_io(prog(t, T_PIP_IN, 0.6)) if t < T_PIP_OUT else 1 - ease_io(prog(t, T_PIP_OUT, 0.6))
    CARD = L["card"]; cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    full = (0.0, 0.0, float(W), float(H))
    z = zoom_at(t); tt_ = t + OFF
    tx, ty = doc_offsets(z)
    fx = tx + z * float(np.interp(tt_, FT, FXF)); fy = ty + z * float(np.interp(tt_, FT, FYF))
    s_ = 2.3 * z / 1.45 if SQ else 1.25
    src = (fx - cw / 2 * s_, fy - ch * 0.42 * s_, fx + cw / 2 * s_, fy + ch * 0.58 * s_)
    Li = lambda a, b: [a[i] + (b[i] - a[i]) * k for i in range(4)]
    d0, d1 = Li(full, CARD), Li(full, src)
    dw, dh = int(round(d0[2] - d0[0])), int(round(d0[3] - d0[1]))
    sx, sy = (d1[2] - d1[0]) / dw, (d1[3] - d1[1]) / dh
    M = np.float32([[1 / sx, 0, -d1[0] / sx], [0, 1 / sy, -d1[1] / sy]])
    crop = cv2.warpAffine(doc, M, (dw, dh), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)
    put_card(fr, crop, d0[0], d0[1], r=int(44 * k) + 1, shadow=0.32 * k)
    o = 1 - ease_io(prog(t, T_PIP_OUT - 0.25, 0.35))
    if o > 0:
        p = ease_out(prog(t, T_PIP_IN + 0.15, 0.55))
        if p > 0: over(fr, ink(text_img("البيبي فيس", L["nfs"] + 8, "Black", grad=((170, 34, 84), (243, 165, 189)))), W / 2,
                       L["title"] + 22 * (1 - p), alpha=p * o, blur=(1 - p) * 8)
        p = back_out(prog(t, ws("حلم") - 0.1, 0.5))
        if p > 0: over(fr, shadowed(box_img("حلم كل صبية", L["sfs"], PINK, BURG, radius=40), r=12, a=0.35, dy=6),
                       W / 2, L["sub"] + 16 * (1 - min(1, p)), alpha=min(1, p * 2.5) * o, scale=0.9 + 0.1 * p)
        x0, y0, x1, y1 = CARD
        sparkles(fr, t, ws("صبية") - 0.1, [(x1 - 30, y0 + 40), (x0 + 40, y0 + (y1 - y0) * 0.55), (x1 - 70, y1 - 30)], 70 if SQ else 90)
    return fr

def doc_scene0(t):
    if T_PIP_IN <= t < T_PIP_OUT + 0.6: return pip_scene(t)
    return doctor(t)
def doc_scene(t): return doctor(t)

def photo_card(fr, t, ph, t0, t1, zoom=0.07):
    x0, y0, x1, y1 = L["pcard"]; cw, ch = x1 - x0, y1 - y0
    p = ease_out(prog(t, t0 + 0.05, 0.6))
    z = 1.02 + zoom * ease_io(prog(t, t0 - 0.4, t1 - t0 + 0.8))
    img = ph.cover(cw, ch, z)
    put_card(fr, img, x0, y0 + 40 * (1 - p), r=44)
    return y0 + 40 * (1 - p)

def sweep(fr, x0, y0, w, h, g):
    """soft diagonal light sweep over a card area (glow of the result)"""
    if not 0 < g < 1: return
    y0 = int(y0); yy_, xx_ = np.mgrid[0:h, 0:w]
    c = -0.3 * w + g * 1.6 * w; band = (np.exp(-(((xx_ + yy_ * 0.45) - c) / (w * 0.13)) ** 2) * math.sin(g * math.pi) * 0.45).astype(np.float32)
    m = rounded_mask(w, h, 44)[..., 0] * band
    ya, yb = max(0, y0), min(H, y0 + h); m = m[ya - y0:yb - y0]
    reg = fr[ya:yb, x0:x0 + w]; reg[:] = reg * (1 - m[..., None]) + np.array((255, 236, 242), np.float32) * m[..., None]

CHAP = ["الجلسة", "التوقيت", "النقاهة"]

# --- chapter 1: the Dracula session gives the baby-face result ---
def scene_F1(t):
    fr = motion_bg(t, 1.0, "1", TB[1]); chapter(fr, t, 0, TB[1] + 0.1)
    yc = photo_card(fr, t, P["face"], TB[1], TB[2], zoom=0.08)
    x0, y0, x1, y1 = L["pcard"]
    sweep(fr, x0, yc, x1 - x0, y1 - y0, prog(t, ws("البيبي", 1) - 0.1, 1.1))
    sparkles(fr, t, ws("البيبي", 1), [(x1 - 50, y0 + 60), (x0 + 60, y0 + (y1 - y0) * 0.6), (x1 - 110, y1 - 50)], 80 if SQ else 100)
    rise(fr, shadowed(box_img("جلسة الدراكولا", L["pfs"] + 6, BURG, WHITE)), L["ptitle"], prog(t, ws("الدراكولا") - 0.3, 0.5))
    p = back_out(prog(t, ws("البيبي", 1) - 0.15, 0.5))
    if p > 0: over(fr, mark_pill("ok", "بتعطيكِ نتيجة البيبي فيس", 46 if SQ else 54, PINK, BURG, BURG, WHITE),
                   W / 2, L["p3"] + 24 * (1 - min(1, p)), scale=0.9 + 0.1 * p, alpha=min(1, p * 2.5))
    return fr

# --- chapter 2: best time = winter or late autumn ---
def season_card(icon, label, w, h, fs, ok):
    k = ("season", icon, label, w, h, round(ok * 16))
    if k in _tc: return _tc[k]
    im = Image.fromarray(white_card(w, h, r=min(40, h // 3)).copy())
    pad = int(h * 0.2); dz = h - 2 * pad
    im.alpha_composite(Image.fromarray(disc(dz, (252, 232, 239))), (w - pad - dz, pad))
    ic = Image.fromarray(icon_img(icon, int(dz * 0.58), BURG, 1.9))
    im.alpha_composite(ic, (w - pad - dz + (dz - ic.width) // 2, pad + (dz - ic.height) // 2))
    t = Image.fromarray(ink(text_img(label, fs, "Bold", fill=BURG, shadow=False, pad=20)))
    im.alpha_composite(t, (w - pad - dz - int(pad * 1.1) - t.width, (h - t.height) // 2))
    if ok > 0.02:
        ms = int(dz * 0.62 * back_out(ok, 1.8)); 
        if ms > 4:
            mk = Image.fromarray(mark("ok", ms, BURG, WHITE)); im.alpha_composite(mk, (pad + (int(dz * 0.62) - ms) // 2 + 10, (h - ms) // 2))
    _tc[k] = shadowed(np.array(im), r=16, a=0.35, dy=10, cache=False); return _tc[k]

def scene_F2(t):
    fr = motion_bg(t, 2.0, "2", TB[2]); chapter(fr, t, 1, TB[2] + 0.1)
    rise(fr, shadowed(box_img("أفضل وقت للجلسة", 64 if SQ else 78, BURG, WHITE)), L["c2t"], prog(t, TB[2] + 0.3, 0.5))
    p = ease_out(prog(t, TB[2] + 0.5, 0.6))
    if p > 0 and not SQ:
        over(fr, shadowed(disc(170, WHITE), r=16, a=0.35, dy=10, cache=True), W / 2, L["ic_y"] + 20 * (1 - p), alpha=p, scale=0.85 + 0.15 * p)
        over(fr, icon_img("calendar-days", 92, BURG, 1.8), W / 2, L["ic_y"] + 20 * (1 - p), alpha=p, scale=0.85 + 0.15 * p)
    w, h = L["sc_wh"]
    for (ic, lab, ts), y in zip((("snowflake", "موسم الشتاء", ws("الشتاء")), ("leaf", "آخر الخريف", ws("آخر"))), L["c2rows"]):
        q = prog(t, ts - 0.3, 0.45)
        if q <= 0: continue
        rise(fr, season_card(ic, lab, w, h, L["lfs"] + 6, prog(t, ts + 0.35, 0.4)), y, q)
    p = back_out(prog(t, ws("الخريف") + 0.3, 0.5))
    if p > 0 and not SQ: over(fr, shadowed(box_img("الوقت المثالي للجلسة", 56, PINK, BURG, radius=40), r=12, a=0.35, dy=6),
                              W / 2, L["endpill"], scale=0.85 + 0.15 * p, alpha=min(1, p * 2.5))
    return fr

# --- chapter 3: recovery from five days to a week ---
def scene_F3(t):
    fr = motion_bg(t, 3.0, "3", TB[3]); chapter(fr, t, 2, TB[3] + 0.1)
    rise(fr, shadowed(box_img("فترة نقاهة", 68 if SQ else 84, BURG, WHITE)), L["c3t"], prog(t, ws("نقاهة") - 0.45, 0.5))
    p = ease_out(prog(t, ws("نقاهة") - 0.2, 0.6))
    if p > 0 and not SQ:
        y = L["ic_y"] + 6 * math.sin(t * 1.1)
        over(fr, shadowed(disc(170, WHITE), r=16, a=0.35, dy=10, cache=True), W / 2, y + 20 * (1 - p), alpha=p, scale=0.85 + 0.15 * p)
        over(fr, icon_img("moon-star", 92, BURG, 1.8), W / 2, y + 20 * (1 - p), alpha=p, scale=0.85 + 0.15 * p)
    w, h = L["bar_wh"]
    for (lab, ts, fr_), y in zip((("من 5 أيام", ws("خمسة"), 0.7), ("لأسبوع", ws("لأسبوع"), 1.0)), L["c3rows"]):
        q = prog(t, ts - 0.3, 0.45)
        if q <= 0: continue
        f = ease_io(prog(t, ts - 0.1, 1.0)) * fr_
        rise(fr, bar_card2(lab, f, w, h, L["lfs"] + 4), y, q)
    p = back_out(prog(t, ws("لأسبوع") + 0.45, 0.5))
    if p > 0 and not SQ: over(fr, shadowed(box_img("5 - 7 أيام راحة", 60, PINK, BURG, radius=40), r=12, a=0.35, dy=6),
                              W / 2, L["endpill"], scale=0.85 + 0.15 * p, alpha=min(1, p * 2.5))
    return fr

SCENES = [doc_scene0, scene_F1, scene_F2, scene_F3, doc_scene]
DOCS = {0, 4}                                   # scenes that get the bottom dark gradient
TRANS = {1: ("leak", 0.6), 2: ("soft", 0.6), 3: ("soft", 0.6), 4: ("flash", 0.8)}
def scene_index(t):
    i = 0
    for j, T in enumerate(TB):
        if t >= T: i = j
    return i

# ---------------- transitions ----------------
_blob = {}
def blob(cx, cy, r):
    k = (cx, cy, r)
    if k not in _blob:
        yy_, xx_ = np.mgrid[0:H:8, 0:W:8]
        g = np.exp(-(((xx_ - cx) ** 2 + (yy_ - cy) ** 2) / (2 * r * r))).astype(np.float32)
        _blob[k] = cv2.resize(g, (W, H))[..., None]
        if len(_blob) > 400: _blob.clear()
    return _blob[k]
def light_leak(fr, d, amt=1.0):
    """soft pink/peach light leak around the cut (no synthesized flash: user rule)"""
    a1 = math.exp(-((d + 0.12) / 0.25) ** 2) * 0.6 * amt; a2 = math.exp(-((d - 0.1) / 0.3) ** 2) * 0.55 * amt
    leak = blob(int(W * 0.8) // 8 * 8, int(H * 0.35) // 8 * 8, 380 if SQ else 520) * np.array([235, 120, 170], np.float32) * a1 \
        + blob(int(W * 0.25) // 8 * 8, int(H * 0.68) // 8 * 8, 440 if SQ else 640) * np.array([255, 185, 140], np.float32) * a2
    fr[:] = 255 - (255 - fr) * (255 - np.clip(leak, 0, 255)) / 255

def shift(img, dx=0.0, dy=0.0, z=1.0):
    M = np.float32([[z, 0, W / 2 * (1 - z) + dx], [0, z, H / 2 * (1 - z) + dy]])
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)

FLASH_DIR = os.path.join(WORK, "flash"); FLASH_N = 24; FLASH_PEAK = 15
_fl = {}
def flash_frame(i):
    """the user's flash transition (style-guide/assets/انتقال-فلاش.mov), fully covers at frame 15"""
    i = max(0, min(i, FLASH_N - 1))
    if i not in _fl:
        im = np.array(Image.open(os.path.join(FLASH_DIR, "%03d.png" % (i + 1))).convert("RGBA"))
        if SQ: im = im[(1920 - 1080) // 2:(1920 + 1080) // 2]
        _fl[i] = im
    return _fl[i]

def pip_dark(t):
    if T_PIP_IN <= t < T_PIP_OUT: return 1 - ease_io(prog(t, T_PIP_IN, 0.6))
    if T_PIP_OUT <= t < T_PIP_OUT + 0.6: return ease_io(prog(t, T_PIP_OUT, 0.6))
    return 1.0

def compose(t):
    i = scene_index(t); fr = SCENES[i](t)
    dark = (pip_dark(t) if i == 0 else 1.0) if i in DOCS else 0.0
    for j, (kind, d) in TRANS.items():
        T = TB[j]
        if kind == "flash":
            a0 = T - FLASH_PEAK / FPS
            if not (a0 <= t < a0 + FLASH_N / FPS): continue
            m = ease_io(prog(t, T - 0.1, 0.2))
            fr = SCENES[j - 1](t) * (1 - m) + SCENES[j](t) * m if 0 < m < 1 else (SCENES[j - 1](t) if m <= 0 else SCENES[j](t))
            over(fr, flash_frame(int(round((t - a0) * FPS))), W / 2, H / 2)
            dark = m
            break
        if not (T - d / 2 <= t < T + d / 2): continue
        A, B = SCENES[j - 1](t), SCENES[j](t)
        m = ease_io((t - (T - d / 2)) / d)
        if kind == "leak":
            fr = shift(A, z=1 + 0.04 * m) * (1 - m) + shift(B, z=1.04 - 0.04 * m) * m
            b = 6 * math.sin(m * math.pi)
            if b > 0.3: fr = cv2.GaussianBlur(fr, (0, 0), b)
            light_leak(fr, t - T)
        else:                                           # soft: short upward push + cross-fade + light blur
            fr = shift(A, dy=-60 * m, z=1 + 0.03 * m) * (1 - m) + shift(B, dy=60 * (1 - m), z=1.03 - 0.03 * m) * m
            b = 5 * math.sin(m * math.pi)
            if b > 0.3: fr = cv2.GaussianBlur(fr, (0, 0), b)
            light_leak(fr, t - T, 0.5)
        da = 1.0 if j - 1 in DOCS else 0.0; db = 1.0 if j in DOCS else 0.0
        dark = da + (db - da) * m
        break
    return fr, dark

# ---------------- captions ----------------
def group_span(gi):
    g = GROUPS[gi]; s = g["s"] - 0.06; e = g["e"] + 0.3
    for g2 in GROUPS[gi + 1:]:
        if g2["style"] != "-": e = min(e, g2["s"] - 0.08); break
    if g["text"] == "البيبي فيس": e = min(e, T_PIP_IN + 0.15)
    if g["text"] == "بمركز بالديرما": e = MSG_HOLD[1] + 0.05
    else: e = min(e, T_MSG - 0.05)
    for T in TB[1:]:
        if s < T - 0.25 < e and e - T < 0.5: e = min(e, T + 0.2)
    return s, e

_bounds = {}
def word_bounds(words, size, weight, pad=40):
    k = (tuple(words), size, weight)
    if k in _bounds: return _bounds[k]
    f = font(weight, size); d = ImageDraw.Draw(Image.new("L", (1, 1)))
    Lf = lambda txt: d.textlength(txt, font=f, direction="rtl", language="ar")
    tw = Lf(" ".join(words))
    b = [pad + tw - (Lf(" ".join(words[:j]) + " ") if j else 0) for j in range(len(words))] + [pad]
    b[0] = pad + tw; _bounds[k] = b; return b

NFS, KFS = (58, 100) if SQ else (68, 120)
DISP = {"أهم شي": "أهــــم شي"}
CIRC = {"بجلسة بسيطة جداً": (1, 2), "الوقت اللي نختاره": (0, 0)}   # word span to circle inside the group
def draw_captions(fr, t):
    for gi, g in enumerate(GROUPS):
        if g["style"] == "-": continue
        s, e = group_span(gi)
        if not (s <= t < e): continue
        a_in = ease_out(prog(t, s, 0.18)); a_out = 1 - ease_io(prog(t, e - 0.14, 0.14))
        if g["style"] == "k":
            p = ease_out(prog(t, s, 0.45))
            if g["text"] == "بمركز بالديرما":
                q = back_out(prog(t, s, 0.5))
                over(fr, shadowed(box_img("مركز بالديرما", 52 if SQ else KFS - 34, PINK, BURG, weight="Black", radius=48), r=14, a=0.4, dy=8),
                     W / 2, L["kw_msg"] - 18 * (1 - min(1, q)), alpha=min(1, q * 2.5) * a_out, scale=0.9 + 0.1 * q)
                continue
            img = text_img(DISP.get(g["text"], g["text"]), KFS, "Black", grad=((255, 255, 255), (243, 165, 189)))
            over(fr, img, W / 2, L["kw"] + 30 - 24 * (1 - p), alpha=p * a_out, blur=(1 - p) * 10)
        else:
            wl = [WORDS[i]["w"] for i in g["words"]]
            img = text_img(g["text"], NFS, "Bold").copy(); b = word_bounds(wl, NFS, "Bold"); w = img.shape[1]
            fac = np.ones(w, np.float32)
            for j, i in enumerate(g["words"]):
                p = ease_out(prog(t, WORDS[i]["s"] - 0.06, 0.2))
                x0 = 0 if j == len(wl) - 1 else int(b[j + 1]); x1 = w if j == 0 else int(b[j])
                fac[x0:x1] = p
            fac = np.convolve(fac, np.ones(9) / 9, "same")
            img[..., 3] = (img[..., 3] * fac[None, :]).astype(np.uint8)
            over(fr, img, W / 2, CAP_Y + 8 * (1 - a_in), alpha=a_in * a_out)
            if g["style"] == "c":
                j0, j1 = CIRC[g["text"]]
                left, right = b[j1 + 1], b[j0]
                cx = W / 2 - w / 2 + (left + right) / 2
                t0 = WORDS[g["words"][j1]]["s"] + 0.05
                hand_circle(fr, cx, CAP_Y + 6, (right - left) / 2 + 34, NFS * 0.78, t0, t, fo=a_out, col=WHITE, th=6)


# ---------------- frame ----------------
PAGE0 = 65                                          # overlay turns into the full FB page (measured)
HOLD_J, HOLD_T = MSG_HOLD
def msg_index(t):
    return min(int(round((t - T_MSG) * FPS)), HOLD_J)   # held on the clicked button; the FB page part is never shown
def Outro(start=0):
    p = Pipe(["ffmpeg", "-loglevel", "error", "-ss", f"{start / FPS:.4f}", "-i", OUTRO, "-vf", f"fps={FPS},scale={W}:{H}",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], (H, W, 3))
    p.i = start - 1; return p
OUT_SRC = {"p": None}
WIPE = 0.7
def circle_mask(r):
    yy_, xx_ = np.ogrid[0:H, 0:W]
    d = np.sqrt((xx_ - W / 2) ** 2 + (yy_ - H / 2) ** 2)
    return np.clip((r - d) / 40 + 0.5, 0, 1).astype(np.float32)[..., None]
def msg_layer(fr, m, j):
    a = m[..., 3:4].astype(np.float32) / 255
    if j < PAGE0:
        if L["msg_dy"]:
            a = np.roll(a, L["msg_dy"], 0); a[:L["msg_dy"]] = 0; rgb = np.roll(m[..., :3], L["msg_dy"], 0)
        else: rgb = m[..., :3]
        return fr * (1 - a) + rgb.astype(np.float32) * a
    k = ease_io(clamp((j - PAGE0 + 1) / 8))
    return fr * (1 - k) + m[..., :3].astype(np.float32) * k

def render_frame(i, doc_src, msg_src):
    t = i / FPS
    DOC["img"] = doc_src.get(min(i, int(RAW_END * FPS) - 2))
    FACE["x"] = float(np.interp(t + OFF, FT, FX)); FACE["y"] = float(np.interp(t + OFF, FT, FY))
    j = msg_index(t)
    oi = int(round((t - T_OUT) * FPS))
    if t >= T_OUT + WIPE:
        fr = OUT_SRC["p"].get(oi).astype(np.float32)
    else:
        fr, dark = compose(t)
        fr = fr.astype(np.float32)
        if dark > 0: fr *= (1 - BOTTOM_DARK * dark); fr *= (1 - TOP_DARK * dark)
        else: fr *= (1 - TOP_DARK * 0.5)
        draw_captions(fr, t)
        over(fr, FRAME, 0, 0, anchor="tl")
        if t >= T_MSG: fr = msg_layer(fr, msg_src.get(j), j)
        if t >= T_OUT:                               # pink circle wipe into our outro (style guide)
            p = ease_io((t - T_OUT) / WIPE); R = p * math.hypot(W, H) / 2 * 1.05
            m = circle_mask(R); fr = fr * (1 - m) + OUT_SRC["p"].get(oi).astype(np.float32) * m
    if t > DUR - 0.5: fr *= 0.6 + 0.4 * max(0, (DUR - t) / 0.5)
    return np.clip(fr, 0, 255).astype(np.uint8)

def main():
    tag = "sq" if SQ else "v"
    if ONLY:
        for tt in ONLY:
            i = int(round(tt * FPS))
            doc_src = Doctor(i); msg_src = Msg(max(0, msg_index(tt)) if tt >= T_MSG else 0)
            OUT_SRC["p"] = Outro(max(0, int(round((tt - T_OUT) * FPS))))
            Image.fromarray(render_frame(i, doc_src, msg_src)).save(os.path.join(WORK, f"{tag}_{tt:05.2f}.png"))
        return
    n = int(DUR * FPS); a, b = RANGE if RANGE else (0, n)
    doc_src = Doctor(a); msg_src = Msg(max(0, msg_index(a / FPS)) if a / FPS >= T_MSG else 0)
    OUT_SRC["p"] = Outro(max(0, int(round((a / FPS - T_OUT) * FPS))))
    out = OUT or os.path.join(WORK, f"{tag}_noaudio.mp4")
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(a, min(b, n)):
        enc.stdin.write(render_frame(i, doc_src, msg_src).tobytes())
        if i % 90 == 0: print(f"{tag} {i}/{n}", flush=True)
    enc.stdin.close(); enc.wait(); print("done", out)

if __name__ == "__main__":
    main()
