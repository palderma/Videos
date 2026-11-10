#!/usr/bin/env python3
"""«جلد الأوزة: 3 أفكار غلط» v4 (2026-11-10).
v3 message system kept (label «الفكرة الغلط 0N» -> «الصح», one idea per screen, 01/02/03 progress row, new ending)
but the tiles MOVE like v2 again: strips swing in on 1/16 notes, RTL split-flap cascade, Y-turn split into two tiles,
words spreading apart and cascading into new slots, strips folding away.
New: the brand frame template on top (fades out at the end) and the official pink outro video (6 s) appended.
Usage: python3 gb4.py [--t=..] [--frames=a:b --out=DIR] [--sfx] [--jsx=PKGDIR]"""
import os, sys, math, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ["GB_WORK"] = os.environ.get("GB_WORK", "/home/user/gb/work4")
import numpy as np
from PIL import Image
import gb, kf
from gb import k, ext, Face, ShadowFace, ImgFace, Piece, Shape, null, piece, add, sfx, flap_tile, fold_out, mix, FACES
from kf import K
from gb3 import MultiFace, T, base_for, tilt_rise, word_line, MYTH_CARD, MYTH_TXT, MYTH_STROKE, PINK_STROKE

WINE, PINK, WHITE, INK, PALE = gb.WINE, gb.PINK, gb.WHITE, gb.INK, gb.PALE
MAIN_LEN = 17.0                 # motion part (rendered here)
OUTRO_LEN = 6.0                 # official pink outro appended after it
VLEN = MAIN_LEN + OUTRO_LEN
OUTRO_PINK = (234, 153, 188)    # first frame colour of the official outro (seamless hand-over)
ASSETS = "/home/user/palderma-videos/style-guide/assets"
FRAME_PNG = os.path.join(ASSETS, "templates", "frame-9x16.png")
OUTRO_MP4 = os.path.join(ASSETS, "خاتمة-عمودي-9x16.mp4")
FRAME_OP = [k(0.0, 0), k(0.35, 100), k(16.35, 100), k(16.7, 0)]
CY = 1010; TOPY = 440           # content centre / progress row (clear of the frame header)

def swing_in(nl, face, t_in, step=0.0625, dur=0.34):
    """v2 entrance: every strip of the tile (both halves) swings up from edge-on, one per 1/16 note"""
    f = FACES[face]
    strips = {}
    for p in gb.PIECES:
        if p.parent is nl and p.face == face:
            m = re.search(r"ش(\d+)$", p.name)
            if m: strips.setdefault(int(m.group(1)) - 1, []).append(p)
    for s, ps in strips.items():
        a = t_in + s * step; b = a + dur
        for p in ps:
            x0 = p.pos[0] if not isinstance(p.pos[0], K) else val(p.pos, a)[0]
            p.pos = [k(a, [x0, -60, 0], 70, 15), k(b, [x0, 0, 0], 80, 70)]
            ent = [k(a, -90, 70, 15), k(b, 0, 45, 70), k(b + 0.07, 5, 50, 50), k(b + 0.15, 0, 60, 70)]
            p.rx = ent + (p.rx if isinstance(p.rx, list) else [])
            p.op = [k(a, 0), k(a + 0.12, 100)]
            p.inp = a
        cxs = (ps[0].crop[0] + ps[0].crop[2]) / 2
        sfx(b, "click", 0.7, pan=(cxs / f.w - 0.5) * 0.6)

from kf import val

def build4():
    for L in (gb.FACES,): L.clear()
    for L in (gb.NULLS, gb.PIECES, gb.SHAPES, gb.LAYERS, gb.SFX): del L[:]
    TT = {}
    # ======================= opening (0 - 2.3): as v2/v3 =======================
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
    # 01 02 03 units -> progress row under the frame header
    CW, CH = 112, 76
    nums = ["01", "02", "03"]
    for n in nums:
        Face("رقم " + n, CW, CH, n, 46, "Black", MYTH_TXT, fill=MYTH_CARD, stroke=MYTH_STROKE, radius=CH / 2, hl=False)
        Face("رقم فعال " + n, CW, CH, n, 46, "Black", INK, fill=PINK, stroke=PINK_STROKE, radius=CH / 2, hl=False)
        Face("رقم تم " + n, CW, CH, n, 46, "Black", WHITE, fill=MYTH_CARD, stroke=MYTH_STROKE, radius=CH / 2, hl=False)
    cg = 24
    S = [2.25, 5.65, 9.0]
    END = [5.5, 8.85, 12.95]
    for i, n in enumerate(nums):
        x0 = 540 + (CW + cg) - i * (CW + cg)
        a = 1.0 + i * 0.1
        xt = 540 + (x0 - 540) * 0.8
        nl = null("مفتاح - وحدة " + n, [k(a, [x0, 1235, 200], 70, 10), k(a + 0.4, [x0, 1235, 0], 85, 70),
                                         k(1.98 + i * 0.04, [x0, 1235, 0], 70, 40), k(2.5 + i * 0.04, [xt, TOPY, 0], 75, 70),
                                         k(12.95, [xt, TOPY, 0], 70, 40), k(13.3, [xt, TOPY + 40, -60], 40, 70)],
                  scale=[k(1.98, 100, 70, 40), k(2.5, 80, 75, 70)], op=[k(a, 0), k(a + 0.2, 100), k(13.0, 100), k(13.28, 0)])
        add(piece("وحدة %s" % n, "رقم " + n, parent=nl, rx=[k(a, 70, 70, 10), k(a + 0.4, 0, 80, 70)], inp=a, outp=13.35, shade=False))
        s0 = S[i]; s1 = S[i + 1] if i < 2 else 13.0
        add(piece("وحدة %s - فعالة" % n, "رقم فعال " + n, parent=nl, op=[k(s0 + 0.1, 0), k(s0 + 0.4, 100), k(s1 - 0.1, 100), k(s1 + 0.15, 0)], inp=s0, outp=s1 + 0.2, shade=False))
        if i < 2:
            add(piece("وحدة %s - تمت" % n, "رقم تم " + n, parent=nl, op=[k(s1 - 0.1, 0), k(s1 + 0.15, 100)], inp=s1 - 0.1, outp=13.35, shade=False))
        sfx(a + 0.35, "tick", 0.6)

    # ======================= label «الفكرة الغلط 0N» -> «الصح» =======================
    LH = 84
    Face("عنوان غلط", 330, LH, "الفكرة الغلط", 50, "Bold", MYTH_TXT, fill=MYTH_CARD, stroke=MYTH_STROKE, radius=LH / 2, hl=False)
    Face("عنوان صح", 190, LH, "الصح", 52, "Bold", INK, fill=WHITE, stroke=None, radius=LH / 2, hl=False)
    def label(n, s0, land, end_t, LY):
        Face("رقم عنوان " + n, 96, LH, n, 46, "Black", INK, fill=PINK, stroke=None, radius=LH / 2, hl=False)
        gapc = 14
        Lm = 330 + gapc + 96; xr = 540 + Lm / 2; xm = xr - 165; xc = xr - 330 - gapc - 48
        Lf = 190 + gapc + 96; xrf = 540 + Lf / 2; xf = xrf - 95; xcf = xrf - 190 - gapc - 48
        lt = land - 0.08
        nlab = null("مفتاح - عنوان %s" % n, [k(s0, [540, LY + 40, 0], 70, 10), k(s0 + 0.5, [540, LY, 0], 85, 70),
                                             k(end_t, [540, LY, 0], 70, 60), k(end_t + 0.36, [540, LY + 40, -60], 30, 70)],
                    op=[k(s0, 0), k(s0 + 0.3, 100), k(end_t + 0.12, 100), k(end_t + 0.36, 0)])
        fold = [k(end_t, 0, 70, 45), k(end_t + 0.36, 88, 20, 70)]
        add(piece("عنوان - الفكرة الغلط %s" % n, "عنوان غلط", pos=[xm - 540, 0, 0], parent=nlab,
                  rx=[k(s0, 70, 70, 10), k(s0 + 0.5, 0, 80, 70), k(lt, 0, 70, 50), k(lt + 0.16, 90, 15, 70)], inp=s0, outp=lt + 0.16))
        add(piece("عنوان - الصح %s" % n, "عنوان صح", pos=[xf - 540, 0, 0], parent=nlab,
                  rx=[k(lt + 0.16, -90, 70, 15), k(lt + 0.36, 0, 40, 70), k(lt + 0.44, -6, 50, 50), k(lt + 0.52, 0, 60, 70)] + fold,
                  inp=lt + 0.16, outp=end_t + 0.4))
        add(piece("عنوان - رقم %s" % n, "رقم عنوان " + n, parent=nlab,
                  pos=[k(s0, [xc - 540, 0, 0]), k(lt + 0.1, [xc - 540, 0, 0], 70, 60), k(lt + 0.42, [xcf - 540, 0, 0], 70, 70)],
                  rx=[k(s0 + 0.08, 70, 70, 10), k(s0 + 0.58, 0, 80, 70)] + fold, inp=s0, outp=end_t + 0.4))
        sfx(lt + 0.16, "tick", 0.8)
        sfx(s0 + 0.05, "whoosh_soft", 0.4)

    # ======================= idea 1: «مستحيل تروح» -> «هاي شائعة» (v2: 7-strip RTL split-flap) =======================
    FW, FH = 940, 290
    Face("مستحيل تروح", FW, FH, "مستحيل تروح", 146, "Bold", PALE)
    Face("هاي شائعة", FW, FH, "هاي شائعة", 150, "Bold", INK, fill=PINK, stroke=PINK_STROKE)
    ShadowFace("ظل كبير", FW, FH)
    s0 = S[0]; t_in = s0 + 0.2; f1 = 3.75
    n2 = null("مفتاح - الفكرة 01", [540, CY, 0])
    add(piece("ظل - الفكرة 01", "ظل كبير", pos=[0, 18, 0], parent=n2, op=[k(t_in + 0.2, 0), k(t_in + 0.7, 100), k(END[0] - 0.05, 100), k(END[0] + 0.25, 0)], shade=False, inp=t_in, outp=END[0] + 0.3))
    fin1 = flap_tile(n2, ["مستحيل تروح", "هاي شائعة"], f1, strips=7, delay=0.065, flip=0.5, gap=-1, tag="غ01", start_in=t_in, bounce=7.0)
    swing_in(n2, "مستحيل تروح", t_in)
    sfx(f1 - 0.06, "flipbig", 0.8)
    land1 = f1 + 6 * 0.065 + 0.5
    sfx(land1, "settle", 0.8)
    fold_out(fin1, END[0] - 0.05, delay=0.035, dur=0.34, drop=50)
    sfx(END[0], "whoosh", 0.55)
    label("01", s0, land1, END[0], CY - FH / 2 - 80)
    TT["01"] = (s0, f1, land1, END[0])

    # ======================= idea 2: «خطيرة» -> «غالبًا» | «عادي» (v2: Y-turn split) =======================
    Face("خطيرة", 920, 300, "خطيرة", 205, "Bold", PALE)
    Face("غالبًا", 410, 270, "غالبًا", 175, "Bold", WHITE)
    Face("عادي", 490, 270, "عادي", 175, "Bold", INK, fill=PINK, stroke=PINK_STROKE)
    ShadowFace("ظل خطير", 920, 300); ShadowFace("ظل غالبا", 410, 270); ShadowFace("ظل عادي", 490, 270)
    s0 = S[1]; t_in = s0 + 0.2
    tA, tB = 7.15, 7.43; tC = tB + 0.38; tE = END[1]
    n3 = null("مفتاح - الفكرة 02", [540, CY, 0])
    add(piece("ظل - خطيرة", "ظل خطير", pos=[0, 18, 0], parent=n3, op=[k(t_in + 0.1, 0), k(t_in + 0.5, 100), k(tA - 0.15, 100), k(tA + 0.1, 0)], shade=False, inp=t_in, outp=tA + 0.15))
    sw6 = 920 / 6; ent3 = []
    for s in range(6):
        col = 5 - s
        x0 = col * sw6 + (-0.5 if col > 0 else 0); x1 = (col + 1) * sw6 - (-0.5 if col < 5 else 0); cxs = (x0 + x1) / 2
        a = t_in + s * 0.0625; b = a + 0.34
        for half, (cy0, cy1) in (("↑", (0, 150 + 0.5)), ("↓", (150 - 0.5, 300))):
            p = add(piece("خطيرة %s ش%d" % (half, s + 1), "خطيرة", (x0, cy0, x1, cy1), (cxs, 150),
                          [k(a, [cxs - 460, -60, 0], 70, 15), k(b, [cxs - 460, 0, 0], 80, 70)],
                          rx=[k(a, -90, 70, 15), k(b, 0, 45, 70), k(b + 0.07, 5, 50, 50), k(b + 0.15, 0, 60, 70)],
                          op=[k(a, 0), k(a + 0.12, 100)], parent=n3, inp=a, outp=tB))
            ent3.append(p)
        sfx(b, "click", 0.7, pan=(cxs / 920 - 0.5) * 0.6)
    xR, xL = 540 + 10 + 205, 540 - 10 - 245
    for p in ent3:
        cx_local = p.pos[-1].v[0]
        right = cx_local > 0
        hc = 230 if right else -230
        target = (xR if right else xL) - 540
        rel = cx_local - hc
        p.ry = [k(tA, 0, 70, 50), k(tB, 90, 10, 70)]
        pk = [k(tA, list(p.pos[-1].v), 33, 33)]
        for st in np.linspace(tA, tB, 7):
            u = (st - tA) / (tB - tA); e = kf._bez(u, 0.5, 0.1); ang = math.radians(90 * e)
            piv = hc + (target - hc) * 0.5 * e
            pk.append(K(st, [piv + rel * math.cos(ang), 0.0, -rel * math.sin(ang) + 90 * e], 33, 33, lin=True))
        p.pos = p.pos + pk
    sfx(tA - 0.06, "flipbig", 0.8)
    n3a = null("مفتاح - غالبًا", [k(tB, [xR - 40, CY, 90], 70, 10), k(tC, [xR, CY, 0], 80, 70)])
    n3b = null("مفتاح - عادي", [k(tB, [xL + 40, CY, 90], 70, 10), k(tC, [xL, CY, 0], 80, 70)])
    fin2 = {}
    for j, (nl, fn, sh, d) in enumerate(((n3a, "غالبًا", "ظل غالبا", 0.0), (n3b, "عادي", "ظل عادي", 0.04))):
        add(piece("ظل - " + fn, sh, pos=[0, 16, 0], parent=nl, op=[k(tC - 0.2, 0), k(tC + 0.1, 100), k(tE + 0.05, 100), k(tE + 0.3, 0)], shade=False, inp=tB, outp=tE + 0.4))
        fw_ = FACES[fn].w; hp = []
        for half, (cy0, cy1) in (("↑", (0, 135 + 0.5)), ("↓", (135 - 0.5, 270))):
            hp.append(add(piece("%s %s" % (fn, half), fn, (0, cy0, fw_, cy1), (fw_ / 2, 135), [0, 0, 0],
                                ry=[k(tB + d, -90, 70, 10), k(tC + d, 0, 35, 70), k(tC + d + 0.08, 5, 50, 50), k(tC + d + 0.18, 0, 60, 70)],
                                parent=nl, inp=tB, outp=None)))
        fin2[j] = tuple(hp)
        sfx(tC + d, "click", 0.9, pan=-0.3 if fn == "عادي" else 0.3)
    sfx(tC + 0.04, "settle", 0.8)
    fold_out(fin2, tE, delay=0.06, dur=0.34, drop=50, rtl=True)
    sfx(tE, "whoosh", 0.55)
    label("02", s0, tC, tE, CY - 150 - 80)
    TT["02"] = (s0, tA, tC, tE)

    # ======================= idea 3: «ما إلها حل» -> «إلها خيارات» / «بعد الفحص» (v2 cascade) =======================
    th4 = 230; sz4 = 165
    specs = [("ما", "إلها", 250), ("إلها", "خيارات", 520), ("حل", "بعد", 320)]
    for a_, b_, w_ in specs:
        Face("4غ " + a_, w_, th4, a_, sz4, "Bold", PALE)
        Face("4 فاضي " + b_, w_, th4, None, fill=(PINK if b_ == "بعد" else gb.TILE), stroke=(PINK_STROKE if b_ == "بعد" else gb.TILE_STROKE))
        if b_ == "بعد":
            Face("4 " + b_, w_, th4, b_, sz4, "Bold", INK, fill=PINK, stroke=PINK_STROKE)
        else:
            Face("4 " + b_, w_, th4, b_, sz4, "Bold", WHITE)
        ShadowFace("ظل4 " + b_, w_, th4)
    Face("4 الفحص", 590, th4, "الفحص", sz4, "Bold", INK, fill=PINK, stroke=PINK_STROKE); ShadowFace("ظل4 الفحص", 590, th4)
    so = 0.8; gp = 18
    ws = [250 * so, 520 * so, 320 * so]; tot = sum(ws) + 2 * gp; x = 540 + tot / 2; old = []
    for w_ in ws: old.append(x - w_ / 2); x -= w_ + gp
    R1, R2 = CY - 130, CY + 130
    new = {"إلها": (540 + 395 - 125, R1), "خيارات": (540 - 395 + 260, R1), "بعد": (540 + 465 - 160, R2), "الفحص": (540 - 465 + 295, R2)}
    s0 = S[2]; t4 = s0 + 0.15; tT = 10.45; tX = END[2]
    finals4 = [None] * 3
    for i in (2, 1, 0):
        a_, b_, w_ = specs[i]
        ea = t4 + i * 0.09
        nx, ny = new[b_]; ox = old[i]
        spread = [540 + (ox - 540) * 1.16, CY, 160]
        tm = tT + 0.38 + i * 0.1
        nl = null("مفتاح - %s/%s" % (a_, b_),
                  [k(ea, [ox, CY, 900], 70, 10), k(ea + 0.55, [ox, CY, 0], 85, 70),
                   k(tT + i * 0.04, [ox, CY, 0], 70, 50), k(tm, spread, 60, 45),
                   k(tm + 0.72, [nx, ny, 0], 75, 70)],
                  scale=[k(tm, 100 * so, 70, 40), k(tm + 0.72, 100, 75, 70)],
                  op=[k(ea, 0), k(ea + 0.3, 100)])
        add(piece("ظل4 - " + b_, "ظل4 " + b_, pos=[0, 16, 0], parent=nl, op=[k(ea + 0.2, 0), k(ea + 0.55, 100), k(tm - 0.1, 100), k(tm + 0.1, 25), k(tm + 0.6, 25), k(tm + 0.85, 100)], shade=False, inp=ea))
        fin = flap_tile(nl, ["4غ " + a_, "4 فاضي " + b_, "4 " + b_], tm - 0.05, strips=1, cascade=[0.3, 0.42], tag="غ03", start_in=ea, bounce=6.5)
        finals4[i] = (nl, fin)
        sfx(ea, "air", 0.4)
    sfx(tT + 0.3, "flipbig", 0.7)
    nx, ny = new["الفحص"]; tf = tT + 0.75
    nlf = null("مفتاح - الفحص", [k(tf, [nx - 40, ny + 40, 160], 70, 10), k(tf + 0.45, [nx, ny, 0], 80, 70)], op=[k(tf, 0), k(tf + 0.15, 100)])
    add(piece("ظل4 - الفحص", "ظل4 الفحص", pos=[0, 16, 0], parent=nlf, op=[k(tf + 0.2, 0), k(tf + 0.5, 100)], shade=False, inp=tf))
    for half, (cy0, cy1) in (("↓", (th4 / 2 - 0.5, th4)), ("↑", (0, th4 / 2 + 0.5))):
        add(piece("الفحص %s" % half, "4 الفحص", (0, cy0, 590, cy1), (295, 0), [0, -th4 / 2, 0],
                  rx=[k(tf, 88, 70, 10), k(tf + 0.42, 0, 30, 70), k(tf + 0.5, -5, 50, 50), k(tf + 0.6, 0, 60, 70)], parent=nlf, inp=tf))
    sfx(tf + 0.42, "click", 1.0, pan=-0.35)
    land3 = tf + 0.6
    # «بعد الفحص» = the key: both pink tiles pop together once the row is complete
    tp_ = land3 + 0.2
    nl_b = finals4[2][0]
    for nl in (nl_b, nlf):
        nl.scale = ext(nl.scale, [k(tp_, 100, 70, 40), k(tp_ + 0.16, 104, 40, 50), k(tp_ + 0.42, 100, 50, 80)])
    sfx(tp_ + 0.12, "settle", 0.9)
    # collapse (v2): all tiles fold and recede
    allp = [(nl, fin) for nl, fin in finals4] + [(nlf, None)]
    for i, (nl, fin) in enumerate(allp):
        a = tX + i * 0.05
        p_end = nl.pos[-1].v
        nl.pos = nl.pos + [k(a, list(p_end), 70, 50), k(a + 0.5, [540 + (p_end[0] - 540) * 0.45, CY + (p_end[1] - CY) * 0.45, 900], 30, 70)]
        nl.op = (nl.op if isinstance(nl.op, list) else [k(0, nl.op)]) + [k(a + 0.22, 100), k(a + 0.5, 0)]
        if fin is not None:
            for s, (tp, bp) in fin.items():
                for p in (tp, bp):
                    p.rx = (p.rx if isinstance(p.rx, list) else [k(0, p.rx)]) + [k(a, 0, 70, 45), k(a + 0.45, 80, 25, 70)]
    for p in gb.PIECES:
        if p.parent in [x[0] for x in allp] and p.outp is None: p.outp = tX + 0.6
    for p in gb.LAYERS:
        if isinstance(p, Piece) and p.parent is nlf and p.face == "4 الفحص":
            p.rx = p.rx + [k(tX + 0.2, 0, 70, 45), k(tX + 0.62, 80, 25, 70)]
    sfx(tX, "whoosh", 0.7)
    label("03", s0, land3, tX, R1 - th4 / 2 - 80)
    TT["03"] = (s0, tT, land3, tX)

    # ======================= ending (as v3) =======================
    word_line("خلاصة1", [("الفحص", PINK), ("بحدد", WHITE), ("السبب", WHITE)], 100, 890, 13.15, 0.1, 14.75)
    word_line("خلاصة2", [("وفيه", WHITE), ("خيارات", WHITE), ("مناسبة", WHITE)], 100, 1035, 13.55, 0.1, 14.8)
    word_line("دعوة1", [("إذا", WHITE), ("بتعانوا", WHITE), ("منها", WHITE)], 96, 880, 15.0, 0.08, 16.3)
    word_line("دعوة2", [("احجزوا", PINK), ("فحصكم", PINK)], 136, 1040, 15.25, 0.1, 16.35)
    sfx(14.72, "whoosh_soft", 0.5)
    # pink disc in the outro's own pink -> hard hand-over to the official outro at MAIN_LEN
    add(Shape("دائرة وردية (لون الخاتمة)", "disc", [540, 960], [k(16.45, [0, 0], 70, 20), k(17.0, [2300, 2300], 75, 70)], OUTRO_PINK, inp=16.43))
    sfx(16.45, "bloom", 0.8)
    gb.T.update(TT); gb.T["vlen"] = VLEN
    gb.MARKERS = [(0, "الافتتاحية: جلد الأوزة 3 أفكار غلط + 01 02 03"), (S[0], "الفكرة الغلط 01: مستحيل تروح ← الصح: هاي شائعة"),
                  (S[1], "الفكرة الغلط 02: خطيرة ← الصح: غالبًا عادي"), (S[2], "الفكرة الغلط 03: ما إلها حل ← الصح: إلها خيارات بعد الفحص"),
                  (13.15, "الخلاصة: الفحص بحدد السبب / وفيه خيارات مناسبة"), (15.0, "الدعوة: إذا بتعانوا منها احجزوا فحصكم"),
                  (16.45, "انتقال للخاتمة الوردية"), (MAIN_LEN, "الخاتمة الرسمية (قالب بالديرما)")]

# ---------------- frame template on top (renderer) ----------------
_frame = None
_render_at0 = gb.render_at
def render_at4(t):
    global _frame
    fr = _render_at0(t)
    if _frame is None:
        im = np.array(Image.open(FRAME_PNG).convert("RGBA"), np.float32)
        _frame = (im[..., :3], im[..., 3:4] / 255)
    o = val(FRAME_OP, t) / 100
    if o > 0.003:
        rgb, a = _frame; a = a * o
        fr = fr * (1 - a) + rgb * a
    return fr
gb.render_at = render_at4
_sig0 = gb.state_sig
gb.state_sig = lambda t: _sig0(t) + [round(val(FRAME_OP, t), 2)]

# ---------------- AE: frame + outro footage layers ----------------
def jsx_extra(pkg, js, r):
    shutil.copy(FRAME_PNG, os.path.join(pkg, "footage", "قالب الإطار 9x16.png"))
    shutil.copy(OUTRO_MP4, os.path.join(pkg, "footage", "خاتمة بالديرما 9x16.mp4"))
    ok = [(kk.t, kk.v) for kk in FRAME_OP]
    s = "try { var FR = MAIN.layers.add(imp('footage/قالب الإطار 9x16.png')); FR.name = 'قالب الإطار (بالديرما)';\n"
    s += "  var FO = FR.property('ADBE Transform Group').property('ADBE Opacity');\n"
    for t_, v_ in ok: s += "  FO.setValueAtTime(%s, %s);\n" % (r(t_), r(v_))
    s += "  FR.outPoint = %s; } catch (e) { ERRS.push('frame: ' + e); }\n" % r(MAIN_LEN)
    s += ("try { var OU = MAIN.layers.add(imp('footage/خاتمة بالديرما 9x16.mp4')); OU.name = 'الخاتمة الوردية (قالب بالديرما)';\n"
          "  OU.startTime = %s; OU.inPoint = %s; OU.outPoint = %s; } catch (e) { ERRS.push('outro: ' + e); }\n" % (r(MAIN_LEN), r(MAIN_LEN), r(VLEN)))
    return s
gb.JSX_EXTRA = jsx_extra

gb.build = build4
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
