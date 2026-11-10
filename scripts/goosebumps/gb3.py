#!/usr/bin/env python3
"""«جلد الأوزة: 3 أفكار غلط» v3 (2026-11-10): MYTH -> FLIP -> FACT.
Same engine as gb.py (true 3D planes, motion blur, AE export), new direction:
  opening title + three numbered units 01 02 03 that become the progress row;
  each myth = small label «الفكرة الغلط» + number chip, big DARK card with the myth;
  the card turns 180 degrees (scene 1 Y, scene 2 X tumble, scene 3 split-flap) to reveal the PINK fact card on its back;
  the label then flips to «الصح»; one idea per screen, carousel exit to the next.
Ending: «الفحص بحدد السبب» / «وفيه خيارات مناسبة» -> «إذا بتعانوا منها» / «احجزوا فحصكم» -> pink disc -> official logo.
Usage: python3 gb3.py [--t=..] [--frames=a:b --out=DIR] [--sfx] [--jsx=PKGDIR]"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault("GB_WORK", "/home/user/gb/work3")
import numpy as np
import gb, kf
from gb import k, ext, Face, ShadowFace, ImgFace, Piece, Shape, null, piece, add, sfx, flap_tile, fold_out, mix, FACES
from kf import K

WINE, PINK, WHITE, INK = gb.WINE, gb.PINK, gb.WHITE, gb.INK
MYTH_CARD = (66, 6, 25)                 # deep wine: the myth side
MYTH_TXT = mix(PINK, WHITE, 0.35)        # light pink on dark: readable, but «not the truth»
MYTH_STROKE = (110, 30, 58)
PINK_STROKE = mix(PINK, WHITE, 0.35)
VLEN = 18.4

class MultiFace(Face):
    """card + several texts / inner pills (AE: one precomp with several native layers)"""
    def __init__(self, name, w, h, items, **kw):
        kw.setdefault("hinge", False)
        Face.__init__(self, name, w, h, None, **kw)
        self.items = items
    def raster(self):
        if self._r is not None: return self._r
        self._r = None
        txt, self.txt = self.txt, None
        img = Face.raster(self).copy(); self._r = None
        h, w = img.shape[:2]
        for it in self.items:
            if it["kind"] == "rect":
                pw, ph, r = it["w"], it["h"], it["r"]
                ys, xs = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
                qx = np.abs(xs - it["x"]) - (pw / 2 - r); qy = np.abs(ys - it["y"]) - (ph / 2 - r)
                d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
                a = np.clip(0.5 - d, 0, 1)[..., None]
                img = img * (1 - a) + np.concatenate([np.array(it["fill"], np.float32) * a, a * 255], -1)
            else:
                t, cx, by = kf.text_raster(it["s"], it["size"], it.get("weight", "Bold"), it["col"])
                ox, oy = int(round(it["x"] - cx)), int(round(it["base"] - by))
                th, tw = t.shape[:2]
                x0, y0 = max(0, ox), max(0, oy); x1, y1 = min(w, ox + tw), min(h, oy + th)
                s = t[y0 - oy:y1 - oy, x0 - ox:x1 - ox]; a = s[..., 3:4] / 255
                img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + s
        self._r = img
        return img

def T(s, size, col, x, base, weight="Bold"): return {"kind": "text", "s": s, "size": size, "col": col, "x": x, "base": base, "weight": weight}
def base_for(cy, size, digits=False): return cy + size * (0.35 if digits else 0.26)

def tilt_rise(name, face, x, y, a, out_t, dy=70, exit_dy=-80):
    """title-style word entrance: rises from below with a 3D tilt + blur, exits tilting back"""
    return add(piece(name, face, pos=[k(a, [x, y + dy, 0], 70, 15), k(a + 0.62, [x, y, 0], 85, 70),
                                      k(out_t, [x, y, 0], 70, 60), k(out_t + 0.32, [x, y + exit_dy, -120], 25, 70)],
                     rx=[k(a, 62, 70, 15), k(a + 0.62, 0, 85, 70), k(out_t, 0, 70, 60), k(out_t + 0.32, -50, 25, 70)],
                     op=[k(a, 0, 70, 30), k(a + 0.35, 100, 70, 70), k(out_t + 0.08, 100), k(out_t + 0.32, 0)],
                     blur=[k(a, 18, 70, 20), k(a + 0.45, 0, 80, 70), k(out_t, 0), k(out_t + 0.32, 14)],
                     inp=a, outp=out_t + 0.4, shade=False))

def word_line(prefix, words, size, y, a0, step, out_t, gap=None):
    """words = [(text, colour)] in reading order (RTL: first word on the right)"""
    gap = gap if gap is not None else size * 0.32
    ws = [kf.text_width(s, size, "Bold") for s, _ in words]
    L = sum(ws) + gap * (len(ws) - 1); x = 540 + L / 2
    for i, ((s, c), w_) in enumerate(zip(words, ws)):
        fn = "%s %d" % (prefix, i)
        Face(fn, int(w_ + size * 0.9), int(size * 1.7), s, size, "Bold", c, fill=None, hl=False, base=size * 0.85 + size * 0.26)
        tilt_rise("%s - %s" % (prefix, s), fn, x - w_ / 2, y, a0 + i * step, out_t + i * 0.04)
        sfx(a0 + i * step + 0.05, "air", 0.45)
        x -= w_ + gap

def build3():
    gb.FACES.clear(); gb.NULLS.clear(); gb.PIECES.clear(); gb.SHAPES.clear(); gb.LAYERS.clear(); gb.SFX.clear()
    TT = {}
    # ======================= opening (0 - 2.3) =======================
    Face("ع جلد", 300, 230, "جلد", 175, "Bold", WHITE, fill=None, hinge=False, hl=False, base=230 * 0.5 + 175 * 0.26)
    Face("ع الأوزة", 540, 230, "الأوزة:", 175, "Bold", WHITE, fill=None, hinge=False, hl=False, base=230 * 0.5 + 175 * 0.26)
    w1, w2, gap1 = kf.text_width("جلد", 175, "Bold"), kf.text_width("الأوزة:", 175, "Bold"), 50
    xr = 540 + (w1 + gap1 + w2) / 2
    for i, (fn, x) in enumerate((("ع جلد", xr - w1 / 2), ("ع الأوزة", xr - w1 - gap1 - w2 / 2))):
        a = -0.12 + i * 0.13
        add(piece("عنوان - " + FACES[fn].txt, fn, pos=[k(a, [x, 720 + 70, 0], 70, 15), k(a + 0.62, [x, 720, 0], 85, 70),
                                                       k(1.95, [x, 720, 0], 70, 60), k(2.28, [x, 630, -120], 25, 70)],
                  rx=[k(a, 62, 70, 15), k(a + 0.62, 0, 85, 70), k(1.95, 0, 70, 60), k(2.28, -50, 25, 70)],
                  op=[k(a, 0, 70, 30), k(a + 0.35, 100, 70, 70), k(2.02, 100), k(2.28, 0)],
                  blur=[k(a, 18, 70, 20), k(a + 0.45, 0, 80, 70), k(1.98, 0), k(2.28, 14)], outp=2.32, shade=False))
        sfx(a + 0.05, "air", 0.5)
    th = 210; Y2 = 990
    Face("ع 3 فاضي", 200, th, None, fill=PINK, stroke=PINK_STROKE)
    Face("ع 3", 200, th, "3", 178, "Black", INK, fill=PINK, stroke=PINK_STROKE)
    Face("ع أفكار فاضي", 350, th, None); Face("ع أفكار", 350, th, "أفكار", 124, "Bold", WHITE)
    Face("ع غلط فاضي", 315, th, None); Face("ع غلط", 315, th, "غلط", 124, "Bold", PINK)
    for w_ in (200, 350, 315): ShadowFace("ظل %d" % w_, w_, th)
    g2 = 22; L2 = 200 + 350 + 315 + 2 * g2; xr = 540 + L2 / 2
    xs = [xr - 100, xr - 200 - g2 - 175, xr - 200 - g2 - 350 - g2 - 157.5]
    tiles = []
    for i, (nm, w_, x) in enumerate((("3", 200, xs[0]), ("أفكار", 350, xs[1]), ("غلط", 315, xs[2]))):
        a = 0.3 + i * 0.12
        nl = null("مفتاح - " + nm, [k(a, [x, Y2 + 30, 260], 70, 10), k(a + 0.45, [x, Y2, 0], 85, 70)], op=[k(a, 0), k(a + 0.22, 100)])
        add(piece("ظل - " + nm, "ظل %d" % w_, pos=[0, 14, 0], parent=nl, op=[k(a + 0.1, 0), k(a + 0.5, 100), k(1.95, 100), k(2.15, 0)], shade=False, outp=2.25))
        fin = flap_tile(nl, ["ع %s فاضي" % nm, "ع %s" % nm], a + 0.2, strips=1, flip=0.36 if nm != "3" else 0.42,
                        tag="عنوان", start_in=a, bounce=7.0 if nm == "3" else 5.0, click_gain=0.9)
        tiles.append(fin)
        sfx(a, "air", 0.35)
    for i, fin in enumerate(tiles): fold_out(fin, 1.95 + i * 0.05, delay=0.0, dur=0.3, drop=30)
    sfx(1.93, "whoosh", 0.7)
    # three numbered units 01 02 03: appear under the title, then become the progress row at the top
    CW, CH = 112, 76
    nums = ["01", "02", "03"]
    for n in nums:
        Face("رقم " + n, CW, CH, n, 46, "Black", MYTH_TXT, fill=MYTH_CARD, stroke=MYTH_STROKE, radius=CH / 2, hl=False)
        Face("رقم فعال " + n, CW, CH, n, 46, "Black", INK, fill=PINK, stroke=PINK_STROKE, radius=CH / 2, hl=False)
        Face("رقم تم " + n, CW, CH, n, 46, "Black", WHITE, fill=MYTH_CARD, stroke=MYTH_STROKE, radius=CH / 2, hl=False)
    TOPY = 330; cg = 24
    S = [2.25, 5.65, 9.0]                 # scene starts
    for i, n in enumerate(nums):
        x0 = 540 + (CW + cg) - i * (CW + cg)            # RTL: 01 on the right
        a = 1.0 + i * 0.1
        nl = null("مفتاح - وحدة " + n, [k(a, [x0, 1235, 200], 70, 10), k(a + 0.4, [x0, 1235, 0], 85, 70),
                                         k(1.98 + i * 0.04, [x0, 1235, 0], 70, 40), k(2.5 + i * 0.04, [540 + (x0 - 540) * 0.8, TOPY, 0], 75, 70),
                                         k(12.95, [540 + (x0 - 540) * 0.8, TOPY, 0], 70, 40), k(13.3, [540 + (x0 - 540) * 0.8, TOPY - 60, 0], 40, 70)],
                  scale=[k(1.98, 100, 70, 40), k(2.5, 80, 75, 70)], op=[k(a, 0), k(a + 0.2, 100), k(13.0, 100), k(13.28, 0)])
        add(piece("وحدة %s" % n, "رقم " + n, parent=nl, rx=[k(a, 70, 70, 10), k(a + 0.4, 0, 80, 70)], inp=a, outp=13.35, shade=False))
        s0 = S[i]; s1 = S[i + 1] if i < 2 else 13.0
        add(piece("وحدة %s - فعالة" % n, "رقم فعال " + n, parent=nl, op=[k(s0 + 0.1, 0), k(s0 + 0.4, 100), k(s1 - 0.1, 100), k(s1 + 0.15, 0)], inp=s0, outp=s1 + 0.2, shade=False))
        if i < 2:
            add(piece("وحدة %s - تمت" % n, "رقم تم " + n, parent=nl, op=[k(s1 - 0.1, 0), k(s1 + 0.15, 100)], inp=s1 - 0.1, outp=13.35, shade=False))
        sfx(a + 0.35, "tick", 0.6)

    # ======================= the three myths =======================
    LH = 84
    def label_faces(n):
        Face("عنوان غلط", 330, LH, "الفكرة الغلط", 50, "Bold", MYTH_TXT, fill=MYTH_CARD, stroke=MYTH_STROKE, radius=LH / 2, hl=False)
        Face("عنوان صح", 190, LH, "الصح", 52, "Bold", INK, fill=WHITE, stroke=None, radius=LH / 2, hl=False)
        Face("رقم عنوان " + n, 96, LH, n, 46, "Black", INK, fill=PINK, stroke=None, radius=LH / 2, hl=False)

    def scene(idx, s0, flip_t, end_t, myth, fact, card_wh, mode, fact_extra=None):
        n = nums[idx]; cw, chh = card_wh; CY = 1010
        label_faces(n)
        ShadowFace("ظل بطاقة %d" % idx, cw, chh, alpha=0.5)
        LY = CY - chh / 2 - 78
        # ---- card null: carousel in from the right, out to the left
        nl = null("مفتاح - بطاقة %s" % n, [k(s0 + 0.1, [540 + 320, CY, 420], 70, 10), k(s0 + 0.72, [540, CY, 0], 85, 70),
                                            k(flip_t - 0.02, [540, CY, 0], 70, 50), k(flip_t + 0.36, [540, CY, -90], 50, 50), k(flip_t + 0.75, [540, CY, 0], 50, 70),
                                            k(end_t, [540, CY, 0], 70, 30), k(end_t + 0.42, [540 - 340, CY, 420], 45, 70)],
                  op=[k(s0 + 0.1, 0), k(s0 + 0.35, 100), k(end_t + 0.15, 100), k(end_t + 0.42, 0)])
        add(piece("ظل - بطاقة %s" % n, "ظل بطاقة %d" % idx, pos=[0, 22, 0], parent=nl,
                  op=[k(s0 + 0.3, 0), k(s0 + 0.7, 100), k(flip_t, 100), k(flip_t + 0.3, 30), k(flip_t + 0.7, 100)], shade=False, inp=s0, outp=end_t + 0.5))
        cin = [k(s0 + 0.1, 38, 70, 10), k(s0 + 0.72, 0, 85, 70)]
        cout = [k(end_t, 0, 70, 30), k(end_t + 0.42, -42, 45, 70)]
        mid = flip_t + 0.36; land = flip_t + 0.72
        if mode == "Y":
            add(piece("الغلط %s - %s" % (n, myth), "غلط %s" % n, parent=nl, ry=cin + [k(flip_t, 0, 70, 60), k(mid, 90, 12, 70)], inp=s0, outp=mid))
            add(piece("الصح %s - %s" % (n, fact), "صح %s" % n, parent=nl,
                      ry=[k(mid, -90, 70, 12), k(land, 0, 35, 70), k(land + 0.1, 5, 50, 50), k(land + 0.22, 0, 60, 70)] + cout, inp=mid, outp=end_t + 0.45))
        elif mode == "X":
            add(piece("الغلط %s - %s" % (n, myth), "غلط %s" % n, parent=nl, ry=cin, rx=[k(flip_t, 0, 70, 60), k(mid, 90, 12, 70)], inp=s0, outp=mid))
            add(piece("الصح %s - %s" % (n, fact), "صح %s" % n, parent=nl,
                      rx=[k(mid, -90, 70, 12), k(land, 0, 35, 70), k(land + 0.1, -5, 50, 50), k(land + 0.22, 0, 60, 70)], ry=cout, inp=mid, outp=end_t + 0.45))
        if mode in ("X", "Y"):
            sfx(mid - 0.06, "flipbig", 1.0); sfx(land, "settle", 1.0)
        if mode == "SPLIT":
            fin = flap_tile(nl, ["غلط %s" % n, "صح %s" % n], flip_t, strips=1, flip=0.9, tag="بطاقة %s" % n, start_in=s0, bounce=6.0, click_gain=0.0)
            # entrance turn for the myth halves, exit turn for the fact halves
            for p in gb.PIECES:
                if p.parent is nl and p.face == "غلط %s" % n: p.ry = cin
            for s_, (tp, bp) in fin.items():
                for p in (tp, bp): p.ry = cout; p.outp = end_t + 0.45
            mid, land = flip_t + 0.45, flip_t + 0.9
            sfx(mid - 0.06, "flipbig", 1.0); sfx(land, "settle", 1.0)
        if fact_extra:
            fact_extra(nl, land)
        # ---- label: [«الفكرة الغلط»][01] -> [«الصح»][01]
        gapc = 14
        Lm = 330 + gapc + 96; xr = 540 + Lm / 2; xm = xr - 165; xc = xr - 330 - gapc - 48
        Lf = 190 + gapc + 96; xrf = 540 + Lf / 2; xf = xrf - 95; xcf = xrf - 190 - gapc - 48
        lt = land - 0.08            # label flips right after the card lands
        nlab = null("مفتاح - عنوان %s" % n, [k(s0, [540, LY + 40, 0], 70, 10), k(s0 + 0.5, [540, LY, 0], 85, 70),
                                             k(end_t + 0.05, [540, LY, 0], 70, 30), k(end_t + 0.42, [540 - 300, LY, 300], 45, 70)],
                    op=[k(s0, 0), k(s0 + 0.3, 100), k(end_t + 0.15, 100), k(end_t + 0.4, 0)])
        add(piece("عنوان - الفكرة الغلط %s" % n, "عنوان غلط", pos=[xm - 540, 0, 0], parent=nlab,
                  rx=[k(s0, 70, 70, 10), k(s0 + 0.5, 0, 80, 70), k(lt, 0, 70, 50), k(lt + 0.16, 90, 15, 70)], inp=s0, outp=lt + 0.16))
        add(piece("عنوان - الصح %s" % n, "عنوان صح", pos=[xf - 540, 0, 0], parent=nlab,
                  rx=[k(lt + 0.16, -90, 70, 15), k(lt + 0.36, 0, 40, 70), k(lt + 0.44, -6, 50, 50), k(lt + 0.52, 0, 60, 70)], inp=lt + 0.16, outp=end_t + 0.45))
        add(piece("عنوان - رقم %s" % n, "رقم عنوان " + n, parent=nlab,
                  pos=[k(s0, [xc - 540, 0, 0]), k(lt + 0.1, [xc - 540, 0, 0], 70, 60), k(lt + 0.42, [xcf - 540, 0, 0], 70, 70)],
                  rx=[k(s0 + 0.08, 70, 70, 10), k(s0 + 0.58, 0, 80, 70)], inp=s0, outp=end_t + 0.45))
        sfx(lt + 0.16, "tick", 0.8)
        sfx(s0 + 0.1, "whoosh_soft", 0.45)
        TT[n] = (s0, flip_t, land, end_t)

    # myth / fact faces
    W1, H1 = 940, 300
    MultiFace("غلط 01", W1, H1, [T("مستحيل تروح", 146, MYTH_TXT, W1 / 2, base_for(H1 / 2, 146))], fill=MYTH_CARD, stroke=MYTH_STROKE, radius=30)
    MultiFace("صح 01", W1, H1, [T("هاي شائعة", 150, INK, W1 / 2, base_for(H1 / 2, 150))], fill=PINK, stroke=PINK_STROKE, radius=30)
    MultiFace("غلط 02", W1, H1, [T("خطيرة", 200, MYTH_TXT, W1 / 2, base_for(H1 / 2, 200))], fill=MYTH_CARD, stroke=MYTH_STROKE, radius=30)
    MultiFace("صح 02", W1, H1, [T("غالبًا عادي", 165, INK, W1 / 2, base_for(H1 / 2, 165))], fill=PINK, stroke=PINK_STROKE, radius=30)
    W3, H3 = 940, 430
    MultiFace("غلط 03", W3, H3, [T("ما إلها حل", 165, MYTH_TXT, W3 / 2, base_for(H3 / 2, 165))], fill=MYTH_CARD, stroke=MYTH_STROKE, radius=34)
    MultiFace("صح 03", W3, H3, [T("إلها خيارات", 140, INK, W3 / 2, base_for(132, 140))], fill=PINK, stroke=PINK_STROKE, radius=34)
    Face("بعد الفحص", 700, 168, "بعد الفحص", 112, "Bold", WHITE, fill=WINE, stroke=None, radius=84, hl=False)

    def stamp(nl, land):
        # «بعد الفحص» = the key: a burgundy pill that stamps into the fact card after it lands
        a = land + 0.25
        add(piece("تمييز - بعد الفحص", "بعد الفحص", pos=[0, 88, -1], parent=nl,
                  scale=[k(a, 70, 70, 10), k(a + 0.42, 100, 80, 70), k(a + 0.5, 103, 50, 50), k(a + 0.62, 100, 60, 70)],
                  rx=[k(a, 55, 70, 10), k(a + 0.42, 0, 80, 70)] + [k(12.95, 0, 70, 30), k(13.37, 0)],
                  ry=[k(12.95, 0, 70, 30), k(13.37, -42, 45, 70)],
                  op=[k(a, 0), k(a + 0.2, 100)], inp=a, outp=13.45))
        sfx(a + 0.42, "settle", 0.8)

    scene(0, S[0], 3.75, 5.5, "مستحيل تروح", "هاي شائعة", (W1, H1), "Y")
    scene(1, S[1], 7.15, 8.85, "خطيرة", "غالبًا عادي", (W1, H1), "X")
    scene(2, S[2], 10.45, 12.95, "ما إلها حل", "إلها خيارات بعد الفحص", (W3, H3), "SPLIT", stamp)

    # ======================= ending =======================
    word_line("خلاصة1", [("الفحص", PINK), ("بحدد", WHITE), ("السبب", WHITE)], 100, 890, 13.15, 0.1, 14.75)
    word_line("خلاصة2", [("وفيه", WHITE), ("خيارات", WHITE), ("مناسبة", WHITE)], 100, 1035, 13.55, 0.1, 14.8)
    word_line("دعوة1", [("إذا", WHITE), ("بتعانوا", WHITE), ("منها", WHITE)], 96, 880, 15.0, 0.08, 16.3)
    word_line("دعوة2", [("احجزوا", PINK), ("فحصكم", PINK)], 136, 1040, 15.25, 0.1, 16.35)
    sfx(14.72, "whoosh_soft", 0.5)
    add(Shape("دائرة وردية", "disc", [540, 960], [k(16.45, [0, 0], 70, 20), k(17.0, [2300, 2300], 75, 70)], PINK, inp=16.43))
    sfx(16.45, "bloom", 0.8)
    lg = os.path.join(gb.BRAND, "logo/arabic-english/png/burgundy.png")
    ImgFace("شعار - وردة", lg, crop=(480, 0, 1314, 800), scale=0.46)
    ImgFace("شعار - اسم", lg, crop=(0, 930, 1794, 1690), scale=0.36)
    ry0 = 960 - 160; L0 = 16.62
    add(piece("شعار - الوردة", "شعار - وردة", pos=[k(L0, [540, ry0, 0])], rz=[k(L0, -140, 70, 10), k(L0 + 0.93, 0, 85, 70)],
              scale=[k(L0, 55, 70, 10), k(L0 + 0.78, 100, 85, 70)], op=[k(L0, 0), k(L0 + 0.28, 100)], inp=L0 - 0.02, shade=False))
    add(piece("شعار - الاسم", "شعار - اسم", pos=[k(L0 + 0.4, [540, 960 + 225, 0], 70, 15), k(L0 + 1.0, [540, 960 + 185, 0], 85, 70)],
              op=[k(L0 + 0.4, 0), k(L0 + 0.8, 100)], blur=[k(L0 + 0.4, 12), k(L0 + 0.9, 0)], inp=L0 + 0.35, shade=False))
    sfx(L0 + 0.88, "chime", 0.8)
    gb.T.update(TT); gb.T["vlen"] = VLEN
    gb.MARKERS = [(0, "الافتتاحية: جلد الأوزة 3 أفكار غلط + 01 02 03"), (S[0], "الفكرة الغلط 01: مستحيل تروح ← الصح: هاي شائعة"),
                  (S[1], "الفكرة الغلط 02: خطيرة ← الصح: غالبًا عادي"), (S[2], "الفكرة الغلط 03: ما إلها حل ← الصح: إلها خيارات بعد الفحص"),
                  (13.15, "الخلاصة: الفحص بحدد السبب / وفيه خيارات مناسبة"), (15.0, "الدعوة: إذا بتعانوا منها احجزوا فحصكم"), (16.45, "الشعار الرسمي")]

gb.build = build3
gb.VLEN = VLEN

if __name__ == "__main__":
    os.makedirs(gb.WORK, exist_ok=True)
    jsx = [a for a in sys.argv[1:] if a.startswith("--jsx=")]
    if jsx:
        sys.argv = [sys.argv[0]]
        import gb_jsx
        gb_jsx.main(jsx[0].split("=", 1)[1])
    else:
        gb.main()
