#!/usr/bin/env python3
"""«جلد الأوزة: 3 أفكار غلط» - Palderma kinetic typography (2026-11-09).

One scene description drives BOTH outputs:
  * the MP4 render here (numpy/OpenCV, true 3D planes through a 1800 px camera, 8-sample motion blur), and
  * build_project.jsx, which rebuilds the same scene in After Effects with native layers:
    every face (card + Arabic text) is a precomp with a live text layer; every flap / strip is a 3D layer of
    that precomp with a rectangle mask (the WHOLE word is always rendered, then sliced -> Arabic shaping is
    never broken), parented to a 3D null per tile, X / Y rotation keyframes, AE motion blur, a camera.

Usage: python3 gb.py [--t=SECONDS] [--frames=a:b] [--out=DIR] [--jsx=PATH]
"""
import math, os, sys, json
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kf
from kf import K, val

W, H, FPS = 1080, 1920, 30
CAM = 1800.0                    # AE camera zoom (px)
VLEN = 14.6
BRAND = "/home/user/Videos/brand"
WINE = (108, 13, 43); PINK = (243, 165, 189); WHITE = (255, 255, 255)
TILE = (80, 8, 31)              # deep wine card
TILE_STROKE = (125, 38, 66)
PALE = (196, 120, 147)          # «wrong» words: pink, muted toward the card
INK = (108, 13, 43)

def mix(a, b, t): return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))

# ------------------------------------------------------------------ keys
def k(t, v, i=70, o=70, hold=False): return K(t, v, i, o, hold=hold)
def const(v): return v
def ext(prop, new):
    """append keys to a (possibly static) property"""
    if isinstance(prop, list) and prop and isinstance(prop[0], K): return prop + new
    return [K(new[0].t - 0.001, prop, 70, 70)] + new

# ------------------------------------------------------------------ faces
FACES = {}
class Face:
    def __init__(self, name, w, h, txt=None, size=0, weight="Bold", color=WHITE, fill=TILE, stroke=TILE_STROKE,
                 radius=26, hinge=True, hl=True, base=None):
        self.name, self.w, self.h = name, int(w), int(h)
        if txt: hinge = False      # never a line through words (reads as strike-through)
        self.txt, self.size, self.weight, self.color = txt, size, weight, color
        self.fill, self.stroke, self.radius, self.hinge, self.hl = fill, stroke, radius, hinge, hl
        if base is None and txt:
            base = self.h / 2 + size * (0.35 if txt.isdigit() else 0.26)
        self.base = base
        self._r = None
        FACES[name] = self
    def raster(self):
        if self._r is not None: return self._r
        w, h = self.w, self.h
        img = np.zeros((h, w, 4), np.float32)
        if self.fill is not None:
            ys, xs = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
            r = self.radius
            qx = np.abs(xs - w / 2) - (w / 2 - r); qy = np.abs(ys - h / 2) - (h / 2 - r)
            d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
            a = np.clip(0.5 - d, 0, 1)
            col = np.zeros((h, w, 3), np.float32) + np.array(self.fill, np.float32)
            if self.hl:      # upper flap a touch lighter (AE: white rect 6 % on the top half)
                col[: h // 2] = col[: h // 2] * 0.94 + 255 * 0.06
            if self.stroke is not None:   # 2 px inner stroke
                sa = np.clip(1.0 - np.abs(d + 1.5), 0, 1)
                col = col * (1 - sa[..., None]) + np.array(self.stroke, np.float32) * sa[..., None]
            if self.hinge:   # dark hinge line 4 px
                hy0, hy1 = h / 2 - 2, h / 2 + 2
                ha = np.clip(np.minimum(ys - hy0, hy1 - ys) + 0.5, 0, 1) * 0.55
                col = col * (1 - ha[..., None])
            img[..., :3] = col * a[..., None]; img[..., 3] = a * 255
        if self.txt:
            t, cx, by = kf.text_raster(self.txt, self.size, self.weight, self.color)
            ox, oy = int(round(w / 2 - cx)), int(round(self.base - by))
            th, tw = t.shape[:2]
            x0, y0 = max(0, ox), max(0, oy); x1, y1 = min(w, ox + tw), min(h, oy + th)
            s = t[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
            a = s[..., 3:4] / 255
            img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + s
        self._r = img
        return img

class ImgFace(Face):
    def __init__(self, name, path, crop=None, tint=None, scale=1.0):
        im = Image.open(path).convert("RGBA")
        if crop: im = im.crop(crop)
        if scale != 1.0: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        self.path_png = os.path.join(WORK, "assets", name + ".png"); os.makedirs(os.path.dirname(self.path_png), exist_ok=True)
        im.save(self.path_png)
        a = np.array(im, np.float32); a[..., :3] *= a[..., 3:4] / 255
        self.name, self.w, self.h = name, im.width, im.height
        self.txt = None; self._r = a; self.fill = None
        FACES[name] = self
    def raster(self): return self._r

class ShadowFace(Face):
    """soft drop shadow for a card (AE: same PNG as footage)"""
    def __init__(self, name, w, h, radius=26, soft=22, alpha=0.42):
        pad = int(soft * 3)
        ww, hh = int(w) + 2 * pad, int(h) + 2 * pad
        ys, xs = np.mgrid[0:hh, 0:ww].astype(np.float32) + 0.5
        qx = np.abs(xs - ww / 2) - (w / 2 - radius); qy = np.abs(ys - hh / 2) - (h / 2 - radius)
        d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - radius
        a = np.clip(0.5 - d, 0, 1); a = cv2.GaussianBlur(a, (0, 0), soft) * alpha
        img = np.zeros((hh, ww, 4), np.float32); img[..., :3] = np.array((30, 0, 10), np.float32) * a[..., None]; img[..., 3] = a * 255
        self.name, self.w, self.h = name, ww, hh; self.txt = None; self._r = img; self.fill = None
        self.path_png = os.path.join(WORK, "assets", name + ".png"); os.makedirs(os.path.dirname(self.path_png), exist_ok=True)
        st = np.zeros((hh, ww, 4), np.uint8); st[..., :3] = (30, 0, 10); st[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
        Image.fromarray(st).save(self.path_png)
        FACES[name] = self
    def raster(self): return self._r

# ------------------------------------------------------------------ scene graph
class Null:
    def __init__(self, name, pos, scale=100.0, op=100.0):
        self.name, self.pos, self.scale, self.op = name, pos, scale, op
NULLS = []
def null(name, pos, scale=100.0, op=100.0):
    n = Null(name, pos, scale, op); NULLS.append(n); return n

class Piece:
    """a 3D plane = crop of a face; anchor (face px); pos in parent-null space (null origin = face centre)"""
    def __init__(self, name, face, crop=None, anchor=None, pos=None, rx=0.0, ry=0.0, rz=0.0, op=100.0, blur=0.0,
                 parent=None, inp=-1.0, outp=None, shade=True, scale=100.0):
        f = FACES[face]
        self.name, self.face = name, face
        self.crop = crop or (0, 0, f.w, f.h)
        self.anchor = anchor or ((self.crop[0] + self.crop[2]) / 2, (self.crop[1] + self.crop[3]) / 2)
        if pos is None:
            pos = [self.anchor[0] - f.w / 2, self.anchor[1] - f.h / 2, 0.0]
        self.pos, self.rx, self.ry, self.rz, self.op, self.blur = pos, rx, ry, rz, op, blur
        self.parent, self.inp, self.outp, self.shade, self.scale = parent, inp, outp, shade, scale
PIECES = []
def piece(*a, **kw):
    p = Piece(*a, **kw); PIECES.append(p); return p

class Shape:
    """2D shape layer: kind 'pill' (rounded rect, size keys) or 'disc' (ellipse, size keys)"""
    def __init__(self, name, kind, pos, size, color, op=100.0, inp=-1.0, outp=None):
        self.name, self.kind, self.pos, self.size, self.color, self.op, self.inp, self.outp = name, kind, pos, size, color, op, inp, outp
SHAPES = []      # drawn in order, interleaved with pieces via LAYERS
LAYERS = []      # final stacking order (bottom -> top): Piece | Shape
def add(x):
    LAYERS.append(x); return x

SFX = []         # (t, kind, gain, pan)
def sfx(t, kind, gain=1.0, pan=0.0): SFX.append((round(t, 4), kind, gain, pan))

# ------------------------------------------------------------------ motion recipes
def flap_tile(nl, faces, t0, strips=1, delay=0.0, flip=0.42, gap=0.0, rtl=True, bounce=6.0, tag="", start_in=-1.0,
              click_gain=1.0, cascade=None):
    """split-flap a tile through faces[0] -> faces[1] -> ... ; strips columns (whole word sliced, never re-shaped);
    returns dict strip -> (final top piece, final bottom piece) for later exit keys"""
    f0 = FACES[faces[0]]; fw, fh = f0.w, f0.h
    n = len(faces) - 1; hg = -0.5         # halves overlap 0.5 px: no seam through the words at rest
    bots, tops, finals = [], [], {}
    sw = fw / strips
    for s in range(strips):
        col = (s if not rtl else strips - 1 - s)     # rtl: strip 0 = right-most
        x0 = col * sw + (gap / 2 if col > 0 else 0); x1 = (col + 1) * sw - (gap / 2 if col < strips - 1 else 0)
        cxs = (x0 + x1) / 2
        fd = [flip if cascade is None else cascade[j] for j in range(n)]
        ts = [t0 + s * delay]
        for j in range(n - 1): ts.append(ts[-1] + fd[j] * 0.62)        # cascades overlap a little: rolling feel
        hp = [None] * (n + 1)
        for j, fn in enumerate(faces):
            # ---- top half of face j
            tin = start_in if j == 0 else ts[j - 1]
            pos_top = [cxs - fw / 2, 0.0, 0.0]
            if j < n:
                a, b = ts[j], ts[j] + fd[j] / 2
                rx = [k(a, 0, 70, 55), k(b, 90, 8, 70)]
                tp = Piece("%s %s ↑%d ش%d" % (tag, fn, j, s + 1), fn, (x0, 0, x1, fh / 2 - hg), (cxs, fh / 2), pos_top,
                           rx=rx, parent=nl, inp=tin, outp=b)
                sfx(a, "flip", 0.55 * click_gain, pan=(cxs / fw - 0.5) * 0.6)
            else:
                tp = Piece("%s %s ↑ ش%d" % (tag, fn, s + 1), fn, (x0, 0, x1, fh / 2 - hg), (cxs, fh / 2), pos_top,
                           rx=0.0, parent=nl, inp=tin, outp=None)
            tops.append(tp)
            # ---- bottom half of face j
            if j == 0:
                bp = Piece("%s %s ↓ ش%d" % (tag, fn, s + 1), fn, (x0, fh / 2 + hg, x1, fh), (cxs, fh / 2), [cxs - fw / 2, 0.0, 0.0],
                           rx=0.0, parent=nl, inp=start_in, outp=ts[0] + fd[0] + 0.25)
            else:
                a, b = ts[j - 1] + fd[j - 1] / 2, ts[j - 1] + fd[j - 1]
                bb = bounce if j == n else bounce * 0.4
                rx = [k(a, -90, 70, 10), k(b, 0, 30, 70), k(b + 0.07, -bb, 50, 50), k(b + 0.16, 0, 60, 70)]
                outp = (ts[j] + fd[j] + 0.25) if j < n else None
                bp = Piece("%s %s ↓%d ش%d" % (tag, fn, j, s + 1), fn, (x0, fh / 2 + hg, x1, fh), (cxs, fh / 2), [cxs - fw / 2, 0.0, 0.0],
                           rx=rx, parent=nl, inp=a, outp=outp)
                sfx(b, "click" if j == n else "tick", (1.0 if j == n else 0.6) * click_gain, pan=(cxs / fw - 0.5) * 0.6)
            bots.append(bp)
            hp[j] = (tp, bp)
        finals[s] = hp[n]
    for p in bots: add(p); PIECES.append(p)
    for p in reversed(tops): add(p); PIECES.append(p)
    return finals

def fold_out(pairs, t0, delay=0.04, dur=0.36, drop=40, rtl=True, fade=True):
    """rigid strip fold-away: top & bottom halves share the hinge, rotate together 0 -> 90 (top toward camera)"""
    for i, (s, (tp, bp)) in enumerate(sorted(pairs.items())):
        a = t0 + i * delay; b = a + dur
        for p in (tp, bp):
            p.rx = ext(p.rx, [k(a, 0, 70, 45), k(b, 88, 20, 70)])
            p0 = val(p.pos, a)
            p.pos = ext(p.pos, [k(a, list(p0), 70, 60), k(b, [p0[0], p0[1] + drop, p0[2] - 60], 30, 70)])
            p.op = ext(p.op, [k(a + dur * 0.35, 100), k(b, 0)])
            p.outp = b
        sfx(a, "flip", 0.35)

# ------------------------------------------------------------------ build the scene
WORK = os.environ.get("GB_WORK", "/home/user/gb/work")
T = {}
def build():
    global FACES, NULLS, PIECES, SHAPES, LAYERS, SFX
    FACES, NULLS, PIECES, SHAPES, LAYERS, SFX = {}, [], [], [], [], []
    # ================= scene 1: title =================
    # line 1 «جلد الأوزة:» as two words (white, editorial) ; line 2 = three flip tiles
    Face("ع جلد", 300, 230, "جلد", 175, "Bold", WHITE, fill=None, hinge=False, hl=False, base=230 * 0.5 + 175 * 0.26)
    Face("ع الأوزة", 540, 230, "الأوزة:", 175, "Bold", WHITE, fill=None, hinge=False, hl=False, base=230 * 0.5 + 175 * 0.26)
    w1, w2, gap1 = kf.text_width("جلد", 175, "Bold"), kf.text_width("الأوزة:", 175, "Bold"), 50
    L1 = w1 + gap1 + w2; xr = 540 + L1 / 2
    xj = xr - w1 / 2; xa = xr - w1 - gap1 - w2 / 2
    Y1 = 735
    for i, (fn, x) in enumerate((("ع جلد", xj), ("ع الأوزة", xa))):
        a = -0.12 + i * 0.13
        p = add(piece("عنوان - " + fn[2:], fn, pos=[k(a, [x, Y1 + 70, 0], 70, 15), k(a + 0.62, [x, Y1, 0], 85, 70),
                                                      k(1.86, [x, Y1, 0], 70, 60), k(2.2, [x, Y1 - 90, -120], 25, 70)],
                      rx=[k(a, 62, 70, 15), k(a + 0.62, 0, 85, 70), k(1.86, 0, 70, 60), k(2.2, -50, 25, 70)],
                      op=[k(a, 0, 70, 30), k(a + 0.35, 100, 70, 70), k(1.95, 100), k(2.2, 0)],
                      blur=[k(a, 18, 70, 20), k(a + 0.45, 0, 80, 70), k(1.9, 0), k(2.2, 14)], outp=2.25))
        sfx(a + 0.05, "air", 0.5)
    # line 2 tiles, height 176
    th = 210; Y2 = 1005
    Face("ع 3 فاضي", 200, th, None, fill=PINK, stroke=mix(PINK, WHITE, 0.35))
    Face("ع 3", 200, th, "3", 178, "Black", INK, fill=PINK, stroke=mix(PINK, WHITE, 0.35))
    Face("ع أفكار فاضي", 350, th, None)
    Face("ع أفكار", 350, th, "أفكار", 124, "Bold", WHITE)
    Face("ع غلط فاضي", 315, th, None)
    Face("ع غلط", 315, th, "غلط", 124, "Bold", PINK)
    ShadowFace("ظل 200", 200, th); ShadowFace("ظل 350", 350, th); ShadowFace("ظل 315", 315, th)
    g2 = 22; L2 = 200 + 350 + 315 + 2 * g2; xr = 540 + L2 / 2
    xs = [xr - 100, xr - 200 - g2 - 175, xr - 200 - g2 - 350 - g2 - 157.5]
    T["title_tiles"] = []
    for i, (nm, w_, x) in enumerate((("3", 200, xs[0]), ("أفكار", 350, xs[1]), ("غلط", 315, xs[2]))):
        a = 0.34 + i * 0.12
        if nm != "غلط":
            nl = null("مفتاح - " + nm, [k(a, [x, Y2 + 30, 260], 70, 10), k(a + 0.45, [x, Y2, 0], 85, 70)],
                      op=[k(a, 0), k(a + 0.22, 100)])
        else:
            # «غلط» glides to the centre, grows and flips away into the scene-2 tile
            nl = null("مفتاح - غلط", [k(a, [x, Y2 + 30, 260], 70, 10), k(a + 0.45, [x, Y2, 0], 85, 70),
                                      k(1.9, [x, Y2, 0], 70, 40), k(2.22, [540, 960, -40], 40, 70)],
                      scale=[k(1.9, 100, 70, 40), k(2.22, 200, 40, 70)], op=[k(a, 0), k(a + 0.22, 100)])
        add(piece("ظل - " + nm, "ظل %d" % w_, pos=[0, 14, 0], parent=nl, op=[k(a + 0.1, 0), k(a + 0.5, 100), k(1.9, 100), k(2.15, 0)], shade=False, outp=2.2))
        fin = flap_tile(nl, ["ع %s فاضي" % nm, "ع %s" % nm], a + 0.2, strips=1, flip=0.36 if nm != "3" else 0.42,
                        tag="عنوان", start_in=a, bounce=7.0 if nm == "3" else 5.0, click_gain=0.9)
        T["title_tiles"].append((nm, nl, fin))
        sfx(a, "air", 0.35)
    # exit of «3» and «أفكار»: fold away ; «غلط» flips (whole tile, edge-on) and the big tile takes over
    for i, (nm, nl, fin) in enumerate(T["title_tiles"][:2]):
        fold_out(fin, 1.72 + i * 0.06, delay=0.0, dur=0.3, drop=30)
    nm, nl, fin = T["title_tiles"][2]
    tp, bp = fin[0]
    for p in (tp, bp):
        p.rx = ext(p.rx, [k(1.95, 0, 70, 50), k(2.22, 90, 10, 70)]); p.outp = 2.22
    tp.shade = bp.shade = True
    sfx(1.84, "whoosh", 0.8)
    # ================= scene 2: «مستحيل» -> «شائعة» (7 strips, RTL wave) =================
    FW, FH = 940, 330
    Face("مستحيل", FW, FH, "مستحيل", 220, "Bold", PALE)
    Face("شائعة", FW, FH, "شائعة", 220, "Bold", INK, fill=PINK, stroke=mix(PINK, WHITE, 0.35))
    ShadowFace("ظل كبير", FW, FH)
    n2 = null("مفتاح - المشهد 2", [k(2.2, [540, 960, -40], 40, 30), k(2.6, [540, 960, 0], 60, 70)])
    add(piece("ظل - المشهد 2", "ظل كبير", pos=[0, 18, 0], parent=n2, op=[k(2.25, 0), k(2.55, 100), k(5.3, 100), k(5.6, 0)], shade=False, inp=2.2, outp=5.7))
    # entry: the big «مستحيل» tile lands from edge-on (continues the «غلط» flip)
    sw7 = FW / 7
    ent = {}
    for s in range(7):
        col = 6 - s
        x0 = col * sw7 + (-0.5 if col > 0 else 0); x1 = (col + 1) * sw7 - (-0.5 if col < 6 else 0)
        cxs = (x0 + x1) / 2
        rx = [k(2.22, -90, 70, 10), k(2.5, 0, 30, 70), k(2.57, -6, 50, 50), k(2.66, 0, 60, 70)]
        bp = Piece("دخول مستحيل ↓ ش%d" % (s + 1), "مستحيل", (x0, FH / 2 - 0.5, x1, FH), (cxs, FH / 2), [cxs - FW / 2, 0, 0], rx=rx, parent=n2, inp=2.22, outp=2.67)
        tpp = Piece("دخول مستحيل ↑ ش%d" % (s + 1), "مستحيل", (x0, 0, x1, FH / 2 + 0.5), (cxs, FH / 2), [cxs - FW / 2, 0, 0], rx=list(rx), parent=n2, inp=2.22, outp=2.67)
        add(bp); PIECES.append(bp); add(tpp); PIECES.append(tpp)
    # the dropping big flap reads as a top half falling: show top statics from 2.22 (under the receding «غلط»)
    sfx(2.5, "click", 1.15); sfx(2.5, "thump", 0.8)
    T["s2_flip"] = 3.55
    fin2 = flap_tile(n2, ["مستحيل", "شائعة"], T["s2_flip"], strips=7, delay=0.065, flip=0.5, gap=-1, tag="م2", start_in=2.66, bounce=7.0)
    sfx(T["s2_flip"] - 0.05, "whoosh_soft", 0.45)
    fold_out(fin2, 5.2, delay=0.035, dur=0.34, drop=50)
    sfx(5.25, "whoosh", 0.6)
    # ================= scene 3: «خطير» -> «غالبًا» | «عادي» (Y turn + split + redistribution) =================
    Face("خطير", 920, 300, "خطير", 215, "Bold", PALE)
    Face("غالبًا", 410, 270, "غالبًا", 175, "Bold", WHITE)
    Face("عادي", 490, 270, "عادي", 175, "Bold", INK, fill=PINK, stroke=mix(PINK, WHITE, 0.35))
    ShadowFace("ظل خطير", 920, 300); ShadowFace("ظل غالبا", 410, 270); ShadowFace("ظل عادي", 490, 270)
    n3 = null("مفتاح - المشهد 3", [540, 960, 0])
    sh3 = add(piece("ظل - خطير", "ظل خطير", pos=[0, 18, 0], parent=n3, op=[k(5.55, 0), k(5.95, 100), k(6.9, 100), k(7.15, 0)], shade=False, inp=5.5, outp=7.2))
    # entry: 6 strips swing up from edge-on, one per 1/16 note (0.0625 s at 120 BPM)
    sw6 = 920 / 6; ent3 = []
    t_in = 5.62
    for s in range(6):
        col = 5 - s
        x0 = col * sw6 + (-0.5 if col > 0 else 0); x1 = (col + 1) * sw6 - (-0.5 if col < 5 else 0); cxs = (x0 + x1) / 2
        a = t_in + s * 0.0625; b = a + 0.34
        for half, (cy0, cy1) in (("↑", (0, 150 + 0.5)), ("↓", (150 - 0.5, 300))):
            p = add(piece("خطير %s ش%d" % (half, s + 1), "خطير", (x0, cy0, x1, cy1), (cxs, 150),
                          [k(a, [cxs - 460, -60, 0], 70, 15), k(b, [cxs - 460, 0, 0], 80, 70)],
                          rx=[k(a, -90, 70, 15), k(b, 0, 45, 70), k(b + 0.07, 5, 50, 50), k(b + 0.15, 0, 60, 70)],
                          op=[k(a, 0), k(a + 0.12, 100)], parent=n3, inp=a, outp=6.9 + 0.32))
            ent3.append(p)
        sfx(b, "click", 0.7, pan=(cxs / 920 - 0.5) * 0.6)
    # turn: right half -> «غالبًا» (right), left half -> «عادي» (left); edge-on swap hides the size change
    tA, tB = 6.92, 7.2         # halves 0 -> 90 ; new tiles -90 -> 0 from tB to tC
    tC = 7.58
    xR, xL = 540 + 432 - 190 + 0, 540 - 432 + 230   # final centres (gap 24 between 380 & 460 cards)
    xR, xL = 540 + 10 + 205, 540 - 10 - 245
    for p in ent3:
        cx_local = p.pos[-1].v[0] if isinstance(p.pos, list) and isinstance(p.pos[0], K) else p.pos[0]
        right = cx_local > 0
        # all strips of one half rotate about that half's centre: emulate by moving to the half-centre pivot
        hc = 230 if right else -230
        target = (xR if right else xL) - 540
        rel = cx_local - hc
        # each strip: its own y-rotation about the HALF centre = rotation of offset vector rel
        ks_pos, ks_ry = [], []
        for tt_, ang, ctr in ((tA, 0, hc), (tB, 90, hc + (target - hc) * 0.55)):
            pass
        p.ry = [k(tA, 0, 70, 50), k(tB, 90, 10, 70)]
        # position follows the pivot: x = pivot + rel*cos(ry), z = rel*sin(ry) - pushed back
        steps = np.linspace(tA, tB, 7)
        pk = [k(tA, list(p.pos[-1].v), 33, 33)]
        for st in steps:
            u = (st - tA) / (tB - tA)
            e = kf._bez(u, 0.5, 0.1)
            ang = math.radians(90 * e)
            piv = hc + (target - hc) * 0.5 * e
            pk.append(K(st, [piv + rel * math.cos(ang), 0.0, -rel * math.sin(ang) + 90 * e], 33, 33, lin=True))
        p.pos = p.pos + pk
        p.outp = tB
    sfx(tA - 0.04, "whoosh", 0.55)
    n3a = null("مفتاح - غالبًا", [k(tB, [540 + (xR - 540) * 1.0 - 40, 960, 90], 70, 10), k(tC, [xR, 960, 0], 80, 70),
                                  k(8.28, [xR, 960, 0], 70, 40), k(8.62, [xR - 60, 960, 1500], 40, 70)],
                op=[k(8.36, 100), k(8.6, 0)])
    n3b = null("مفتاح - عادي", [k(tB, [xL + 40, 960, 90], 70, 10), k(tC, [xL, 960, 0], 80, 70),
                                k(8.32, [xL, 960, 0], 70, 40), k(8.66, [xL + 60, 960, 1500], 40, 70)],
                op=[k(8.4, 100), k(8.64, 0)])
    for nl, fn, sh, d in ((n3a, "غالبًا", "ظل غالبا", 0.0), (n3b, "عادي", "ظل عادي", 0.04)):
        add(piece("ظل - " + fn, sh, pos=[0, 16, 0], parent=nl, op=[k(tC - 0.2, 0), k(tC + 0.1, 100)], shade=False, inp=tB, outp=8.7))
        fw_ = FACES[fn].w
        for half, (cy0, cy1) in (("↑", (0, 135 + 0.5)), ("↓", (135 - 0.5, 270))):
            add(piece("%s %s" % (fn, half), fn, (0, cy0, fw_, cy1), (fw_ / 2, 135), [0, 0, 0],
                      ry=[k(tB + d, -90, 70, 10), k(tC + d, 0, 35, 70), k(tC + d + 0.08, 5, 50, 50), k(tC + d + 0.18, 0, 60, 70)],
                      parent=nl, inp=tB, outp=8.7))
        sfx(tC + d, "click", 0.9, pan=-0.3 if fn == "عادي" else 0.3)
    sfx(8.28, "whoosh_soft", 0.5)
    # ================= scene 4: «ما إله حل» -> «له خيارات» / «بعد الفحص» =================
    th4 = 230; sz4 = 165
    specs = [("ما", "له", 250), ("إله", "خيارات", 520), ("حل", "بعد", 320)]
    for a_, b_, w_ in specs:
        Face("4 " + a_, w_, th4, a_, sz4, "Bold", PALE)
        Face("4 فاضي " + b_, w_, th4, None)
        if b_ == "خيارات":
            Face("4 " + b_, w_, th4, b_, sz4, "Bold", INK, fill=PINK, stroke=mix(PINK, WHITE, 0.35))
        else:
            Face("4 " + b_, w_, th4, b_, sz4, "Bold", WHITE)
        ShadowFace("ظل4 " + b_, w_, th4)
    Face("4 الفحص", 590, th4, "الفحص", sz4, "Bold", WHITE); ShadowFace("ظل4 الفحص", 590, th4)
    so = 0.8; gp = 18
    ws = [250 * so, 520 * so, 320 * so]; tot = sum(ws) + 2 * gp; x = 540 + tot / 2; old = []
    for w_ in ws: old.append(x - w_ / 2); x -= w_ + gp
    R1, R2 = 830, 1090
    new = {"له": (540 + 395 - 125, R1), "خيارات": (540 - 395 + 260, R1), "بعد": (540 + 465 - 160, R2), "الفحص": (540 - 465 + 295, R2)}
    t4 = 8.55; tT = 9.85
    T["s4_flip"] = tT
    finals4 = [None] * 3
    for i in (2, 1, 0):          # «حل» crosses under the others: create it first (lowest in the stack)
        a_, b_, w_ = specs[i]
        ea = t4 + i * 0.09
        nx, ny = new[b_]; ox = old[i]
        spread = [540 + (ox - 540) * 1.16, 960, 160]           # phase A: the words breathe apart, still readable
        tm = tT + 0.38 + i * 0.1                               # phase B: travel + cascade flip into the new slot
        nl = null("مفتاح - %s/%s" % (a_, b_),
                  [k(ea, [ox, 960, 900], 70, 10), k(ea + 0.55, [ox, 960, 0], 85, 70),
                   k(tT + i * 0.04, [ox, 960, 0], 70, 50), k(tm, spread, 60, 45),
                   k(tm + 0.72, [nx, ny, 0], 75, 70)],
                  scale=[k(tm, 100 * so, 70, 40), k(tm + 0.72, 100, 75, 70)],
                  op=[k(ea, 0), k(ea + 0.3, 100)])
        add(piece("ظل4 - " + b_, "ظل4 " + b_, pos=[0, 16, 0], parent=nl, op=[k(ea + 0.2, 0), k(ea + 0.55, 100), k(tm - 0.1, 100), k(tm + 0.1, 25), k(tm + 0.6, 25), k(tm + 0.85, 100)], shade=False, inp=ea))
        fin = flap_tile(nl, ["4 " + a_, "4 فاضي " + b_, "4 " + b_], tm - 0.05, strips=1, cascade=[0.3, 0.42], tag="م4", start_in=ea, bounce=6.5)
        finals4[i] = (nl, fin)
        sfx(ea, "air", 0.4)
    # the new tile «الفحص» swings down from behind its top edge
    nx, ny = new["الفحص"]
    nlf = null("مفتاح - الفحص", [k(10.6, [nx - 40, ny + 40, 160], 70, 10), k(11.05, [nx, ny, 0], 80, 70)], op=[k(10.6, 0), k(10.75, 100)])
    add(piece("ظل4 - الفحص", "ظل4 الفحص", pos=[0, 16, 0], parent=nlf, op=[k(10.8, 0), k(11.1, 100)], shade=False, inp=10.6))
    for half, (cy0, cy1) in (("↓", (th4 / 2 - 0.5, th4)), ("↑", (0, th4 / 2 + 0.5))):
        add(piece("الفحص %s" % half, "4 الفحص", (0, cy0, 590, cy1), (295, 0), [0, -th4 / 2, 0],
                  rx=[k(10.6, 88, 70, 10), k(11.02, 0, 30, 70), k(11.1, -5, 50, 50), k(11.2, 0, 60, 70)], parent=nlf, inp=10.6))
    sfx(11.02, "click", 1.0, pan=-0.35); sfx(9.85, "air", 0.6); sfx(10.2, "whoosh", 0.55)
    # ================= scene 5: typographic collapse -> pink -> official logo =================
    tX = 12.05
    allp = [(nl, fin) for nl, fin in finals4] + [(nlf, None)]
    for i, (nl, fin) in enumerate(allp):
        a = tX + i * 0.05
        p_end = nl.pos[-1].v
        nl.pos = nl.pos + [k(a, list(p_end), 70, 50), k(a + 0.5, [540 + (p_end[0] - 540) * 0.45, 960 + (p_end[1] - 960) * 0.45, 900], 30, 70)]
        nl.op = (nl.op if isinstance(nl.op, list) else [k(0, nl.op)]) + [k(a + 0.22, 100), k(a + 0.5, 0)]
        if fin is not None:
            for s, (tp, bp) in fin.items():
                for p in (tp, bp):
                    p.rx = (p.rx if isinstance(p.rx, list) else [k(0, p.rx)]) + [k(a, 0, 70, 45), k(a + 0.45, 80, 25, 70)]
    for p in PIECES:
        if p.parent in [x[0] for x in allp] and p.outp is None: p.outp = tX + 0.6
    # the «الفحص» halves fold too
    for p in LAYERS:
        if isinstance(p, Piece) and p.parent is nlf and p.face == "4 الفحص":
            p.rx = p.rx + [k(tX + 0.2, 0, 70, 45), k(tX + 0.62, 80, 25, 70)]
    sfx(tX, "whoosh", 0.7)
    # pink disc from the centre
    add(Shape("دائرة وردية", "disc", [540, 960], [k(12.4, [0, 0], 70, 20), k(12.95, [2300, 2300], 75, 70)], PINK, inp=12.38))
    sfx(12.4, "bloom", 0.8)
    # official logo (rosette + wordmark from brand/logo/arabic-english/burgundy.png)
    lg = os.path.join(BRAND, "logo/arabic-english/png/burgundy.png")
    ImgFace("شعار - وردة", lg, crop=(480, 0, 1314, 800), scale=0.46)
    ImgFace("شعار - اسم", lg, crop=(0, 930, 1794, 1690), scale=0.36)
    ry0 = 960 - 160
    add(piece("شعار - الوردة", "شعار - وردة", pos=[k(12.62, [540, ry0, 0])], rz=[k(12.62, -140, 70, 10), k(13.55, 0, 85, 70)],
              scale=[k(12.62, 55, 70, 10), k(13.4, 100, 85, 70)], op=[k(12.62, 0), k(12.9, 100)], inp=12.6, shade=False))
    add(piece("شعار - الاسم", "شعار - اسم", pos=[k(13.05, [540, 960 + 225, 0], 70, 15), k(13.65, [540, 960 + 185, 0], 85, 70)],
              op=[k(13.05, 0), k(13.45, 100)], blur=[k(13.05, 12), k(13.55, 0)], inp=13.0, shade=False))
    sfx(13.5, "chime", 0.8)
    # progress: three pale dots + a pink pill that walks 1 -> 2 -> 3 (scenes 2, 3, 4)
    dy = 1470; dx = [540 + 44, 540, 540 - 44]
    for i in range(3):
        add(Shape("نقطة %d" % (i + 1), "pill", [dx[i], dy], [18, 18], mix(WINE, PINK, 0.35), op=[k(2.45 + i * 0.06, 0), k(2.75 + i * 0.06, 100), k(11.95, 100), k(12.2, 0)], inp=2.4, outp=12.3))
    add(Shape("مؤشر وردي", "pill", [k(2.6, [dx[0], dy]), k(5.5, [dx[0], dy], 70, 70), k(5.9, [dx[1] + 0, dy], 70, 70),
                                     k(8.55, [dx[1], dy], 70, 70), k(8.95, [dx[2], dy], 70, 70)],
              [k(2.6, [18, 18], 70, 20), k(2.95, [56, 18], 80, 70)], PINK,
              op=[k(2.6, 0), k(2.85, 100), k(11.95, 100), k(12.2, 0)], inp=2.55, outp=12.3))
    T["vlen"] = VLEN

# ------------------------------------------------------------------ render
def rot(rx, ry, rz):
    a, b, c = (math.radians(x) for x in (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Y = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Z = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Z @ Y @ X

def piece_quad(p, t):
    """projected 4 corners (tl, tr, br, bl) of the crop, plus effective opacity, or None"""
    if t < p.inp - 1e-6 or (p.outp is not None and t >= p.outp - 1e-6): return None
    op = val(p.op, t) / 100
    if p.parent is not None: op *= val(p.parent.op, t) / 100
    if op <= 0.003: return None
    x0, y0, x1, y1 = p.crop; ax, ay = p.anchor
    C = np.array([[x0 - ax, y0 - ay, 0], [x1 - ax, y0 - ay, 0], [x1 - ax, y1 - ay, 0], [x0 - ax, y1 - ay, 0]], np.float64)
    s = val(p.scale, t) / 100
    rx, ry, rz = val(p.rx, t), val(p.ry, t), val(p.rz, t)
    P = (rot(rx, ry, rz) @ (C * s).T).T + np.array(val(p.pos, t), np.float64)
    if p.parent is not None:
        ps = val(p.parent.scale, t) / 100
        P = P * ps + np.array(val(p.parent.pos, t), np.float64)
    z = P[:, 2]
    if (z <= -CAM + 50).any(): return None
    f = CAM / (CAM + z)
    Q = np.stack([540 + (P[:, 0] - 540) * f, 960 + (P[:, 1] - 960) * f], 1)
    # face normal for shading / back-face
    nz = (rot(rx, ry, 0) @ np.array([0, 0, -1.0]))[2]
    shade = 0.0
    if p.shade: shade = min(1.0, abs(math.sin(math.radians(rx))) + abs(math.sin(math.radians(ry)))) * 0.5
    if nz > -0.02: return None
    return Q.astype(np.float32), op, shade, val(p.blur, t)

_crop_cache = {}
def crop_tex(p, blur):
    key = (p.face, p.crop, round(blur, 1))
    if key in _crop_cache: return _crop_cache[key]
    img = FACES[p.face].raster()
    x0, y0, x1, y1 = p.crop
    xi0, yi0, xi1, yi1 = int(math.floor(x0)), int(math.floor(y0)), int(math.ceil(x1)), int(math.ceil(y1))
    tex = img[yi0:yi1, xi0:xi1].copy()
    pad = 0
    if blur > 0.3:
        sig = kf.blur_sigma(blur); pad = int(sig * 3) + 1
        tex = cv2.copyMakeBorder(tex, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
        tex = cv2.GaussianBlur(tex, (0, 0), sig)
    if len(_crop_cache) > 4000: _crop_cache.clear()
    _crop_cache[key] = (tex, pad, (xi0, yi0, xi1, yi1))
    return _crop_cache[key]

def draw_piece(dst, p, t):
    q = piece_quad(p, t)
    if q is None: return
    Q, op, shade, blur = q
    tex, pad, (xi0, yi0, xi1, yi1) = crop_tex(p, blur)
    x0, y0, x1, y1 = p.crop
    # source points = crop rect inside the (possibly padded) texture
    src = np.float32([[x0 - xi0 + pad, y0 - yi0 + pad], [x1 - xi0 + pad, y0 - yi0 + pad], [x1 - xi0 + pad, y1 - yi0 + pad], [x0 - xi0 + pad, y1 - yi0 + pad]])
    M = cv2.getPerspectiveTransform(src, Q)
    th, tw = tex.shape[:2]
    corners = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]]).reshape(-1, 1, 2)
    cw = cv2.perspectiveTransform(corners, M).reshape(-1, 2)
    bx0, by0 = max(0, int(math.floor(cw[:, 0].min())) - 1), max(0, int(math.floor(cw[:, 1].min())) - 1)
    bx1, by1 = min(W, int(math.ceil(cw[:, 0].max())) + 2), min(H, int(math.ceil(cw[:, 1].max())) + 2)
    if bx0 >= bx1 or by0 >= by1: return
    T_ = np.array([[1, 0, -bx0], [0, 1, -by0], [0, 0, 1]], np.float64) @ M
    s = cv2.warpPerspective(tex, T_, (bx1 - bx0, by1 - by0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if shade > 0.001: s[..., :3] *= (1 - shade)
    s *= op
    a = s[..., 3:4] / 255
    sub = dst[by0:by1, bx0:bx1]
    sub *= (1 - a); sub += s[..., :3]

def draw_shape(dst, S, t):
    if t < S.inp - 1e-6 or (S.outp is not None and t >= S.outp - 1e-6): return
    op = val(S.op, t) / 100
    if op <= 0.003: return
    w, h = val(S.size, t); px, py = val(S.pos, t)
    if w < 0.5 or h < 0.5: return
    x0, x1 = max(0, int(px - w / 2 - 2)), min(W, int(px + w / 2 + 3)); y0, y1 = max(0, int(py - h / 2 - 2)), min(H, int(py + h / 2 + 3))
    if x0 >= x1 or y0 >= y1: return
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
    if S.kind == "disc":
        d = np.hypot((xs - px) / (w / 2), (ys - py) / (h / 2)); d = (d - 1) * min(w, h) / 2
    else:
        r = min(w, h) / 2
        qx = np.abs(xs - px) - (w / 2 - r); qy = np.abs(ys - py) - (h / 2 - r)
        d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    a = (np.clip(0.5 - d, 0, 1) * op)[..., None]
    sub = dst[y0:y1, x0:x1]
    sub *= (1 - a); sub += np.array(S.color, np.float32) * a

_bg = None
def background():
    global _bg
    if _bg is None:
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((xs - 540) / 900, (ys - 880) / 1250)
        c0 = np.array((124, 22, 54), np.float32); c1 = np.array((84, 8, 32), np.float32)
        u = np.clip(r, 0, 1) ** 1.4
        img = c0 * (1 - u[..., None]) + c1 * u[..., None]
        rng = np.random.default_rng(9)
        img += rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)
        _bg = np.clip(img, 0, 255)
        os.makedirs(os.path.join(WORK, "assets"), exist_ok=True)
        Image.fromarray(np.round(_bg).astype(np.uint8)).save(os.path.join(WORK, "assets", "خلفية.png"))
    return _bg

def render_at(t):
    fr = background().copy()
    for L in LAYERS:
        if isinstance(L, Piece): draw_piece(fr, L, t)
        else: draw_shape(fr, L, t)
    return fr

def state_sig(t):
    out = []
    for L in LAYERS:
        if isinstance(L, Piece):
            q = piece_quad(L, t)
            out.append(None if q is None else (np.round(q[0], 2).tobytes(), round(q[1], 3), round(q[2], 3), round(q[3], 2)))
        else:
            out.append((tuple(np.round(val(L.size, t), 2)) if not (t < L.inp or (L.outp is not None and t >= L.outp)) else None,
                        tuple(np.round(val(L.pos, t), 2)), round(val(L.op, t), 2)))
    return out

def render_frame(i, samples=8):
    t = i / FPS
    sh = 0.5 / FPS          # 180-degree shutter, centred (AE phase -90)
    t0, t1 = t - sh / 2, t + sh / 2
    if state_sig(t0) == state_sig(t1):
        return render_at(t)
    acc = np.zeros((H, W, 3), np.float32)
    for j in range(samples):
        acc += render_at(t0 + (j + 0.5) / samples * sh)
    return acc / samples

def main():
    args = dict(a.lstrip("-").split("=", 1) if "=" in a else (a.lstrip("-"), "1") for a in sys.argv[1:])
    build()
    if "t" in args:
        for tt in args["t"].split(","):
            fr = render_frame(int(round(float(tt) * FPS)))
            Image.fromarray(np.clip(np.round(fr), 0, 255).astype(np.uint8)).save(os.path.join(WORK, "still_%s.png" % tt))
        return
    if "frames" in args:
        a, b = (int(x) for x in args["frames"].split(":"))
        out = args.get("out", os.path.join(WORK, "frames")); os.makedirs(out, exist_ok=True)
        for i in range(a, b):
            fr = render_frame(i)
            cv2.imwrite(os.path.join(out, "%05d.png" % i), cv2.cvtColor(np.clip(np.round(fr), 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        return
    if "sfx" in args:
        json.dump(sorted(SFX), open(os.path.join(WORK, "sfx.json"), "w"), ensure_ascii=False, indent=0)
        print(len(SFX), "sfx events")

if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    main()
