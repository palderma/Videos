#!/usr/bin/env python3
"""«الشد المائي خرافة» - Palderma doctor reel, «تجمع سوائل» style (original window shot, pink->wine motion scenes,
glass pills, kashida titles, wine 6-petal flower, user's flash transition, messenger button -> pink outro).
The whole edit is a kf scene graph -> rendered here AND exported as an After Effects project (sm_build.py)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf import *

PK = "/home/user/sm/pkg/footage/"
W, H, FPS = 1080, 1920, 30
BURG = (0x6C, 0x0D, 0x2B); PINK = (0xF3, 0xA5, 0xBD); WHITE = (255, 255, 255); DEEP = (40, 3, 15); CREAM = (255, 247, 250)
SH_TXT = dict(color=DEEP, op=150, dist=4, soft=26, dir=180)
SH_CARD = dict(color=DEEP, op=90, dist=10, soft=40, dir=180)

# ---------------------------------------------------------------- time map (raw -> edit)
KEEP = [(1.0, 14.12), (14.33, 34.65)]      # v2: only one cut, hidden under the flash
def o(r):
    acc = 0.0
    for a, b in KEEP:
        if r < a: return acc
        if r <= b: return acc + r - a
        acc += b - a
    return acc + r - KEEP[-1][1]
CUTS = []
_acc = 0
for a, b in KEEP[:-1]: _acc += b - a; CUTS.append(_acc)          # 6.18, 12.90, 20.42

# word times (raw); whisper large-v3 on pause-delimited chunks, words spread inside each chunk
RAWW = [
    ("ضحكوا", 1.10, 1.62), ("عليكِ", 1.62, 2.02), ("وقالولك", 2.02, 2.55), ("الشد", 2.55, 2.98), ("المائي", 2.98, 3.72),
    ("بديل", 3.94, 4.22), ("الفيلر", 4.22, 4.62), ("هذا", 4.62, 4.80), ("الفيديو", 4.80, 5.12), ("ضروري", 5.12, 5.56),
    ("تشاركيه", 5.67, 6.30), ("مع", 6.30, 6.48), ("صحباتك", 6.48, 6.97),
    ("بموضوع", 7.48, 7.95), ("الشد", 7.95, 8.25), ("المائي", 8.25, 8.60), ("كثير", 8.75, 9.05), ("مسجات", 9.05, 9.36), ("بتوصلنا", 9.44, 9.91),
    ("دكتور", 10.01, 10.42), ("شو", 10.42, 10.58), ("فوائد", 10.58, 10.98), ("الشد", 10.98, 11.25), ("المائي", 11.25, 11.61),
    ("تكلفة", 11.72, 12.20), ("الشد", 12.29, 12.52), ("المائي", 12.52, 12.84), ("كيف", 12.92, 13.20), ("بصير", 13.20, 13.55),
    ("أول", 14.45, 14.70), ("شي", 14.70, 14.90), ("لازم", 14.90, 15.25), ("تعرفي", 15.25, 15.71),
    ("إنه", 15.79, 15.95), ("الشد", 15.95, 16.20), ("المائي", 16.20, 16.50), ("هو", 16.50, 16.71), ("الفيلر", 16.71, 17.05),
    ("الاسم", 17.47, 18.09), ("بما", 18.51, 18.75), ("يخص", 18.75, 19.10), ("الشد", 19.10, 19.54), ("المائي", 19.62, 19.95),
    ("هذا", 19.95, 20.15), ("اسم", 20.15, 20.40), ("فيك", 20.40, 20.66), ("وليس", 20.75, 21.15), ("صح", 21.15, 21.67),
    ("لذلك", 22.16, 22.60), ("نحن", 22.60, 22.90), ("في", 22.90, 23.05), ("مركز", 23.05, 23.40), ("بالديرما", 23.40, 24.05),
    ("نسمي", 24.05, 24.45), ("الأشياء", 24.45, 24.95), ("بمسمياتها", 24.95, 25.60),
    ("ويجب", 26.02, 26.40), ("أن", 26.40, 26.55), ("تعرفي", 26.55, 27.15), ("إنه", 27.30, 27.50), ("حقن", 27.50, 27.75), ("فيلر", 27.75, 28.07),
    ("ليس", 28.18, 28.60), ("إلا", 28.60, 29.11), ("ولا", 29.29, 29.50), ("أي", 29.50, 29.70), ("شي", 29.70, 30.08), ("ثاني", 30.16, 30.40),
    ("أهلاً", 30.77, 31.20), ("وسهلاً", 31.20, 31.70), ("بكم", 31.70, 31.95), ("في", 31.95, 32.08), ("مركز", 32.08, 32.35), ("بالديرما", 32.35, 32.69),
    ("للاستفسار", 32.77, 33.25), ("عبر", 33.25, 33.40), ("رسائل", 33.40, 33.62), ("الصفحة", 33.62, 33.86),
]
WORDS = [(w, o(a), o(b)) for w, a, b in RAWW]
def ws(word, n=0):
    k = [x for x in WORDS if x[0] == word]; return k[n][1]
def we(word, n=0):
    k = [x for x in WORDS if x[0] == word]; return k[n][2]
def wi(i): return WORDS[i]

SPEECH_END = o(33.86)                 # 32.22
T_MSG = ws("للاستفسار") - 0.05        # messenger button in
MSG_HOLD = 45                         # last frame before the FB page (clicked button)
T_OUTRO = T_MSG + MSG_HOLD / FPS + 0.35
OUTRO_LEN = 4.8
DUR = round(T_OUTRO + OUTRO_LEN, 3)

# scene times (edit time)
M1_IN, M1_OUT = o(6.95), CUTS[0]          # messages scene; flash peak at the cut
M3_IN, M3_OUT = o(21.62), o(25.82)          # «نسمي الأشياء بمسمياتها»; flash back to the doctor
FLASH_PEAK = 15 / FPS

# ---------------------------------------------------------------- helpers
def kin(t0, d=0.3, a=0.0, b=100.0, ease="smooth"): return keys((t0, a), (t0 + d, b), ease=ease)
def word_layer(c, name, txt, size, weight, col, x, y, t0, t1, rise=14, blur=10, dur=0.45, fade=0.28, shadow=SH_TXT, scale_pop=False):
    """word: blur + rise + fade in at t0, fade out at t1"""
    L = text(name, txt, size, weight, col, inp=t0 - 0.02, outp=t1 + 0.02, shadow=shadow)
    L.pos = keys((t0, [x, y + rise]), (t0 + dur, [x, y]), ease="smooth")
    L.op = keys((t0, 0), (t0 + dur * 0.8, 100), (t1 - fade, 100), (t1, 0), ease="soft")
    L.blur = keys((t0, blur), (t0 + dur, 0), ease="smooth")
    if scale_pop: L.scale = keys((t0, 88), (t0 + dur + 0.1, 100), ease="smooth")
    return c.add(L)

def line_layout(words, size, weight, gap=0.26):
    """RTL: returns x centres for the words centred on 540"""
    ws_ = [text_width(w, size, weight) for w in words]
    g = size * gap; tot = sum(ws_) + g * (len(ws_) - 1)
    x = 540 + tot / 2; xs = []
    for w_ in ws_: xs.append(x - w_ / 2); x -= w_ + g
    return xs, tot

def caption(c, label, items, y, t_end, size=68, gapk=0.26):
    """items = [(word, t_in, colour, weight)] one RTL line"""
    xs, tot = line_layout([w for w, *_ in items], size, "Bold", gapk)
    for (w, t0, col, *rest), x in zip(items, xs):
        sz = size
        word_layer(c, f"{label} - {w}", w, sz, rest[0] if rest else "Bold", col, x, y, t0, t_end)
    return xs, tot

# ---------------------------------------------------------------- motion background (precomp)
def motion_bg(c, dur, grid=False):
    # clean pink -> wine gradient (no flowers, user 2026-10-31) with a very slow push + one soft drifting light
    c.add(image("خلفية وردي-عنابي", PK + "bg_pink_wine.png", pos=[540, 960], scale=keys((0, 100), (dur, 105), ease="lin")))
    c.add(image("ضو ناعم", PK + "soft_light.png", pos=keys((0, [700, 640]), (dur, [420, 820]), ease="lin"), op=55,
                scale=keys((0, 100), (dur, 115), ease="lin")))

# ---------------------------------------------------------------- M1: «كثير مسجات بتوصلنا»
def build_M1():
    d = M1_OUT - M1_IN + 0.6
    c = Comp("مشهد 1 - كثير مسجات بتوصلنا", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M1_IN                              # main time -> precomp time
    end = d
    # line 1
    xs, _ = line_layout(["بموضوع", "الشد", "المائي"], 60, "Medium")
    for w_, x, n in zip(["بموضوع", "الشد", "المائي"], xs, [0, 1, 1]):
        word_layer(c, "سطر 1 - " + w_, w_, 60, "Medium", WHITE, x, 540, max(0.25, t(ws(w_, n))), end, shadow=SH_TXT)
    # big title
    word_layer(c, "عنوان - كثيـر مسجـــات", "كثيـر مسجـــات", 124, "Black", WHITE, 540, 700, t(ws("كثير")), end, rise=30, dur=0.4, blur=22)
    word_layer(c, "عنوان - بتوصلنا", "بتوصلنا", 66, "Bold", WHITE, 540, 815, t(ws("بتوصلنا")), end)
    # messages icon in a white circle + pink badge «+99»
    t0 = t(ws("مسجات")) - 0.05
    circ = c.add(ellipse("دائرة بيضاء - أيقونة المسجات", 210, fill=CREAM, stroke=PINK, stroke_w=5, pos=[540, 1000], shadow=SH_CARD,
                         scale=keys((t0, 70), (t0 + 0.6, 100), ease="smooth"), op=kin(t0, 0.4, ease="soft"), inp=t0))
    c.add(image("أيقونة المسجات", PK + "icon_messages.png", pos=[540, 1000], scale=keys((t0 + 0.1, 75), (t0 + 0.65, 100), ease="smooth"), op=kin(t0 + 0.1, 0.4, ease="soft"), inp=t0))
    tb = t(ws("بتوصلنا"))
    c.add(ellipse("شارة وردية", 92, fill=(0xE8, 0x3E, 0x8C), stroke=WHITE, stroke_w=4, pos=[628, 928],
                  scale=keys((tb, 40), (tb + 0.5, 100), ease="smooth"), op=kin(tb, 0.3, ease="soft"), inp=tb))
    c.add(text("رقم الشارة +99", "+99", 40, "Bold", WHITE, pos=[628, 942], scale=keys((tb + 0.05, 40), (tb + 0.55, 100), ease="smooth"), op=kin(tb + 0.05, 0.3, ease="soft"), inp=tb))
    # soft glass chat panel behind the bubbles (v2)
    tpn = t(ws("دكتور")) - 0.55
    c.add(rect("لوح زجاجي للشات", 940, 560, 52, fill=WHITE, fill_op=10, stroke=WHITE, stroke_w=2, stroke_op=35, pos=keys((tpn, [540, 1395]), (tpn + 0.7, [540, 1365]), ease="smooth"),
               op=kin(tpn, 0.6, ease="soft"), inp=tpn))
    # chat bubbles (right / left / right like a real chat)
    bubbles = [("دكتور، شو فوائد الشد المائي؟", ws("دكتور"), 1, 1200), ("تكلفة الشد المائي؟", ws("تكلفة"), -1, 1365), ("كيف بصير الشد المائي؟", ws("كيف"), 1, 1530)]
    for i, (txt, tw, side, y) in enumerate(bubbles):
        tw = t(tw) - 0.12
        wdt = text_width(txt, 54, "Bold") + 104; hgt = 120
        x = 540 + side * (470 - wdt / 2) * 0.5
        L = c.add(rect(f"فقاعة {i+1}", wdt, hgt, 60, fill=CREAM, fill_op=96, stroke=PINK, stroke_w=3, pos=keys((tw, [x + side * 24, y + 18]), (tw + 0.6, [x, y]), ease="smooth"),
                       scale=keys((tw, 82), (tw + 0.6, 100), ease="smooth"), op=kin(tw, 0.35, ease="soft"), shadow=SH_CARD, inp=tw))
        c.add(text(f"فقاعة {i+1} - نص", txt, 54, "Bold", BURG, pos=keys((tw + 0.06, [x + side * 24, y + 19 + 18]), (tw + 0.66, [x, y + 19]), ease="smooth"),
                   op=kin(tw + 0.1, 0.4, ease="soft"), blur=keys((tw + 0.06, 8), (tw + 0.5, 0), ease="smooth"), inp=tw))
        c.add(image(f"فقاعة {i+1} - علامة سؤال", PK + "icon_question.png", pos=keys((tw + 0.06, [x + side * (wdt / 2 - 2) + side * 24, y - 46 + 18]), (tw + 0.66, [x + side * (wdt / 2 - 2), y - 46]), ease="smooth"),
                    scale=keys((tw + 0.15, 50), (tw + 0.6, 100), ease="smooth"), op=kin(tw + 0.15, 0.3, ease="soft"), inp=tw))
    return c

# ---------------------------------------------------------------- M3: «في مركز بالديرما نسمّي الأشياء بمسمّياتها»
def build_M3():
    d = M3_OUT - M3_IN + 0.6
    c = Comp("مشهد 2 - نسمي الأشياء بمسمياتها", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M3_IN; end = d
    t0 = 0.25
    c.add(image("لوجو بالديرما", PK + "logo_white.png", pos=keys((t0, [540, 690]), (t0 + 0.6, [540, 660]), ease="smooth"),
                scale=keys((t0, 56), (t0 + 0.6, 60), ease="smooth"), op=kin(t0, 0.45), blur=keys((t0, 24), (t0 + 0.55, 0), ease="smooth")))
    xs, _ = line_layout(["في", "مركز", "بالديرما"], 62, "Medium")
    for w_, x in zip(["في", "مركز", "بالديرما"], xs):
        word_layer(c, "سطر - " + w_, w_, 62, "Medium", WHITE, x, 960, max(0.35, t(ws(w_))), end)
    word_layer(c, "عنوان - نسمّي الأشياء", "نسمّي الأشياء", 108, "Black", WHITE, 540, 1110, t(ws("نسمي")), end, rise=28, dur=0.38, blur=20)
    tp = t(ws("بمسمياتها")) - 0.12; pw = text_width("بمسمّياتهـــا", 132, "Black") + 150
    c.add(rect("كبسولة عنابي زجاج", pw, 210, 105, fill=(0x4A, 0x05, 0x1E), fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1270],
               size=keys((tp, [pw * 0.6, 210]), (tp + 0.65, [pw, 210]), ease="smooth"), op=kin(tp, 0.4, ease="soft"), shadow=SH_CARD, inp=tp))
    word_layer(c, "عنوان - بمسمّياتهـا (وردي)", "بمسمّياتهـــا", 132, "Black", PINK, 540, 1312, t(ws("بمسمياتها")), end, rise=24, dur=0.42, blur=24, scale_pop=True)
    return c

# ---------------------------------------------------------------- main comp
def build():
    C = Comp("الشد المائي خرافة - ريلز 9x16", W, H, DUR, FPS, bg=DEEP)
    C.markers += [(CUTS[0], "قص سكتة (مخفي تحت الفلاش)")]
    # ---- doctor: one graded clip, framing + soft zooms by keyframes (anchor = his face)
    FACE = [0, 612 - 960]
    Z = 125
    # v2: slow continuous pushes only (one per doctor part); every reset happens while a motion scene / flash covers him
    zk = [(0.0, 136), (1.6, 124),                       # gentle open
          (M1_IN + 0.75, 129),                          # slow push to the first scene
          (M1_OUT - 0.25, 125), (M3_IN + 0.75, 132),    # part 2: slow push
          (M3_OUT - 0.25, 125), (o(30.6), 130),         # part 3
          (T_OUTRO + 1.0, 133)]                         # ending
    doc = C.add(footage("الدكتور (ملوّن + قص السكتات)", PK + "doctor_graded_cut.mp4", start=0, anchor=FACE, pos=[540, 650],
                        scale=keys(*zk, ease="soft"), inp=0, outp=T_OUTRO + 1.0,
                        blur=keys((0, 10), (0.6, 0), ease="smooth")))
    # hook shake on the stamp (position keys)
    ts = ws("ضحكوا") + 0.9
    # (v2: no shake on the stamp)
    C.add(image("تظليل تحت (للكابشن)", PK + "shade_bottom.png", pos=[540, 960], op=keys((0, 100), (T_OUTRO, 100), (T_OUTRO + 0.4, 0)), outp=T_OUTRO + 0.5))

    # ---- HOOK (frame 1): «الشد المائي» + pill «بديل الفيلر؟» then the «خرافة» stamp
    h_end = we("المائي") - 0.0 if False else ws("هذا") - 0.05
    word_layer(C, "هوك - الشد المائـي", "الشد المائـــي", 128, "Black", WHITE, 540, 1185, -0.18, h_end, rise=26, dur=0.4, blur=20)
    pw = text_width("بديل الفيلر؟", 74, "Bold") + 110
    pill = C.add(rect("هوك - كبسولة زجاجية", pw, 128, 64, fill=(58, 8, 26), fill_op=62, stroke=WHITE, stroke_w=2.5, stroke_op=80, pos=[540, 1330],
                      size=keys((0.0, [pw * 0.6, 128]), (0.6, [pw, 128]), ease="smooth"), op=keys((0.0, 30), (0.3, 100), (h_end - 0.3, 100), (h_end, 0), ease="soft"), inp=0.0, outp=h_end + 0.02, shadow=SH_CARD))
    word_layer(C, "هوك - بديل الفيلر؟", "بديل الفيلر؟", 74, "Bold", WHITE, 540, 1356, 0.12, h_end, rise=12)
    t_st = ts
    sw_, shh = 430, 168
    C.add(rect("هوك - ختم خرافة", sw_, shh, 34, fill=PINK, fill_op=96, stroke=WHITE, stroke_w=6, pos=[540, 985], rot=keys((t_st, -11), (t_st + 0.6, -6), ease="smooth"),
               scale=keys((t_st, 150), (t_st + 0.6, 100), ease="smooth"), op=keys((t_st, 0), (t_st + 0.25, 100), (h_end - 0.3, 100), (h_end, 0)),
               blur=keys((t_st, 16), (t_st + 0.45, 0), ease="smooth"), shadow=dict(color=DEEP, op=150, dist=12, soft=40, dir=180), inp=t_st, outp=h_end + 0.02))
    C.add(text("هوك - خرافة (نص الختم)", "خرافة", 112, "Black", BURG, pos=[540, 985], rot=keys((t_st, -11), (t_st + 0.6, -6), ease="smooth"),
               anchor=[0, -36], scale=keys((t_st, 150), (t_st + 0.6, 100), ease="smooth"), op=keys((t_st, 0), (t_st + 0.25, 100), (h_end - 0.3, 100), (h_end, 0)),
               blur=keys((t_st, 16), (t_st + 0.45, 0), ease="smooth"), inp=t_st, outp=h_end + 0.02))

    # ---- captions (doctor parts) ; keyword = pink
    CY = 1330
    def cap(label, ws_list, t_end, size=68):
        items = []
        for w_ in ws_list:
            word, n = w_[0], w_[1]; col = w_[2] if len(w_) > 2 else WHITE
            items.append((word, ws(word, n), col))
        caption(C, label, items, CY, t_end, size)
    g = [
        ("كابشن 1", [("هذا", 0), ("الفيديو", 0)], ws("ضروري")),
        ("كابشن 2", [("ضروري", 0, PINK)], ws("تشاركيه")),
        ("كابشن 3", [("تشاركيه", 0), ("مع", 0), ("صحباتك", 0)], M1_IN + 0.2),
        ("كابشن 4", [("أول", 0), ("شي", 0)], ws("لازم")),
        ("كابشن 5", [("لازم", 0), ("تعرفي", 0)], ws("الشد", 4) - 0.12),
    ]
    for lab, it, te in g: cap(lab, it, te)
    # equation card: «الشد المائي = فيلر»
    te0 = ws("الشد", 4) - 0.12; te1 = ws("الاسم") - 0.02
    cw = 860; C.add(rect("بطاقة المعادلة - زجاج", cw, 190, 48, fill=(58, 8, 26), fill_op=60, stroke=WHITE, stroke_w=2.5, stroke_op=75, pos=[540, CY - 22],
                         size=keys((te0, [cw * 0.6, 190]), (te0 + 0.65, [cw, 190]), ease="smooth"), op=keys((te0, 0), (te0 + 0.35, 100), (te1 - 0.3, 100), (te1, 0), ease="soft"),
                         shadow=SH_CARD, inp=te0, outp=te1 + 0.02))
    eq = [("الشد المائي", ws("الشد", 4), WHITE, 76), ("=", ws("هو", 0), PINK, 92), ("فيلر", ws("الفيلر", 1), PINK, 96)]
    wl = [text_width(a, sz, "Black" if a != "الشد المائي" else "Bold") for a, _, _, sz in eq]; gp = 46
    x = 540 + (sum(wl) + gp * 2) / 2; xs = []
    for w_ in wl: xs.append(x - w_ / 2); x -= w_ + gp
    for (wd, t0, col, sz), x in zip(eq, xs):
        word_layer(C, "المعادلة - " + wd, wd, sz, "Black" if wd != "الشد المائي" else "Bold", col, x, CY + 6, t0, te1, scale_pop=(wd == "فيلر"))
    g2 = [
        ("كابشن 6", [("الاسم", 0)], ws("بما")),
        ("كابشن 7", [("بما", 0), ("يخص", 0)], ws("الشد", 4)),
        ("كابشن 8", [("الشد", 5), ("المائي", 5)], ws("هذا", 1)),
        ("كابشن 9", [("هذا", 1), ("اسم", 0), ("فيك", 0, PINK)], ws("وليس")),
        ("كابشن 10", [("وليس", 0), ("صح", 0, PINK)], M3_IN + 0.25),
        ("كابشن 11", [("ويجب", 0), ("أن", 0), ("تعرفي", 1)], ws("إنه", 1)),
        ("كابشن 12", [("إنه", 1)], ws("حقن") - 0.1),
    ]
    for lab, it, te in g2: cap(lab, it, te)
    # «حقن فيلر - ليس إلا» card
    tc0 = ws("حقن") - 0.14; tc1 = ws("ولا") - 0.02
    cw2 = 800
    C.add(rect("بطاقة حقن فيلر - زجاج", cw2, 200, 100, fill=(58, 8, 26), fill_op=60, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, CY - 30],
               size=keys((tc0, [cw2 * 0.6, 200]), (tc0 + 0.65, [cw2, 200]), ease="smooth"), op=keys((tc0, 0), (tc0 + 0.35, 100), (tc1 - 0.3, 100), (tc1, 0), ease="soft"),
               shadow=SH_CARD, inp=tc0, outp=tc1 + 0.02))
    C.add(image("بطاقة حقن فيلر - أيقونة", PK + "icon_syringe_white.png", pos=[540 + 312, CY - 30], scale=keys((tc0 + 0.2, 60), (tc0 + 0.7, 100), ease="smooth"),
                op=keys((tc0 + 0.2, 0), (tc0 + 0.5, 100), (tc1 - 0.25, 100), (tc1, 0), ease="soft"), inp=tc0, outp=tc1 + 0.02))
    word_layer(C, "حقن فيلـــر (وردي)", "حقن فيلـــر", 104, "Black", PINK, 540 - 34, CY + 6, ws("حقن"), tc1, rise=20, dur=0.36, blur=18)
    word_layer(C, "ليس إلا", "ليس إلا", 62, "Bold", WHITE, 540, CY + 150, ws("ليس"), tc1)
    g3 = [
        ("كابشن 13", [("ولا", 0), ("أي", 0), ("شي", 1), ("ثاني", 0)], ws("أهلاً") - 0.1),
        ("كابشن 14", [("أهلاً", 0), ("وسهلاً", 0), ("بكم", 0)], ws("في", 1)),
        ("كابشن 15", [("في", 1), ("مركز", 1), ("بالديرما", 1, PINK)], T_MSG + 0.1),
    ]
    for lab, it, te in g3: cap(lab, it, te)

    # ---- motion scenes (precomps): soft entry = opacity + scale + blur ; exit under the user's flash
    for comp_, tin, tout, nm in ((build_M1(), M1_IN, M1_OUT, "مشهد 1 - كثير مسجات"), (build_M3(), M3_IN, M3_OUT, "مشهد 2 - بمسمياتها")):
        C.add(precomp(nm, comp_, start=tin, inp=tin, outp=tout + 0.12,
                      op=keys((tin, 0), (tin + 0.7, 100), (tout - 0.12, 100), (tout + 0.12, 0), ease="soft"),
                      scale=keys((tin, 106), (tin + 1.0, 100), ease="smooth"), blur=keys((tin, 30), (tin + 0.75, 0), ease="smooth")))
        C.markers.append((tin, "دخول " + nm + " (ووش)"))
    # user's flash transition back to the doctor (full cover at its frame 15)
    for tp in (M1_OUT, M3_OUT):
        C.add(footage("انتقال فلاش (ملف المستخدم)", PK + "flash_transition.mov", seq="/home/user/sm/flash", start=tp - FLASH_PEAK, inp=tp - FLASH_PEAK, outp=tp - FLASH_PEAK + 24 / FPS))
        C.markers.append((tp, "فلاش رجوع للدكتور"))
    # ---- brand frame, messenger button (held on the click), pink outro
    C.add(image("تظليل فوق (للوجو)", PK + "shade_top.png", pos=[540, 960], op=keys((T_OUTRO, 100), (T_OUTRO + 0.35, 0)), outp=T_OUTRO + 0.4))
    C.add(image("قالب الهوية (الإطار)", PK + "frame_template_9x16.png", pos=[540, 960], op=keys((T_OUTRO, 100), (T_OUTRO + 0.35, 0)), outp=T_OUTRO + 0.4))
    C.add(footage("زر مراسلة الصفحة (ثابت على الضغطة)", PK + "messenger_button.mov", seq="/home/user/sm/msgfull", start=T_MSG, inp=T_MSG, outp=T_OUTRO + 0.5,
                  remap=[K(T_MSG, 0.0, lin=True), K(T_MSG + MSG_HOLD / FPS, MSG_HOLD / FPS, lin=True), K(T_OUTRO + 0.5, MSG_HOLD / FPS, lin=True)],
                  op=keys((T_OUTRO, 100), (T_OUTRO + 0.3, 0))))
    C.add(footage("خاتمة بالديرما الوردية", PK + "palderma_pink_outro.mp4", start=T_OUTRO, inp=T_OUTRO, outp=DUR,
                  op=keys((T_OUTRO, 0), (T_OUTRO + 0.7, 100), ease="soft"), scale=keys((T_OUTRO, 104), (T_OUTRO + 1.0, 100), ease="smooth"),
                  blur=keys((T_OUTRO, 20), (T_OUTRO + 0.45, 0), ease="smooth")))
    C.markers.append((T_MSG, "زر المراسلة"))
    C.markers.append((T_OUTRO, "الخاتمة الوردية"))
    return C

if __name__ == "__main__":
    C = build()
    print("dur", DUR, "cuts", CUTS, "M1", M1_IN, M1_OUT, "M3", M3_IN, M3_OUT, "msg", T_MSG, "outro", T_OUTRO)
    import numpy as np
    from PIL import Image
    ts = [float(x) for x in sys.argv[1:]] or [0.05, 1.5, 2.5, 4.5]
    for t in ts:
        fr = render_comp(C, t)
        Image.fromarray(fr.clip(0, 255).astype(np.uint8)).save(f"/home/user/sm/prev_{t:05.2f}.jpg", quality=88)
