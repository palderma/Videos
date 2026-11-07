#!/usr/bin/env python3
"""«أسباب فشل علاج الكلف» v2 - in the user's approved doctor-reel look («الشد المائي» v3 / «أحدث 3 معلومات عن البوتوكس» /
«فلستيم سي»): brand frame on every frame, doctor close on his original background, white phrase captions with pink key
words over a dark bottom shade, full-screen pink->wine motion scenes (doctor PiP card + 1-2-3 badges for the three
reasons, «بشرتك مش للتجربة» capsule), user's flash back to the doctor, messenger button -> pink outro + WhatsApp.
Same kf scene graph -> MP4 and After Effects project."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf import *
from kl_edit import KEEP, CUTS, T, SRC, o

import os as _os
PK = _os.environ.get("KL_PKG", "/home/user/klf/pkg2") + "/footage/"
W, H, FPS = 1080, 1920, 30
BURG = (0x6C, 0x0D, 0x2B); PINK = (0xF3, 0xA5, 0xBD); WHITE = (255, 255, 255); DEEP = (40, 3, 15); CREAM = (255, 247, 250)
OUTRO_PINK = (234, 153, 188); GLASS = (58, 8, 26)
SH_TXT = dict(color=DEEP, op=150, dist=4, soft=26, dir=180)
SH_CARD = dict(color=DEEP, op=90, dist=10, soft=40, dir=180)

M1_IN, M1_OUT = CUTS[1], CUTS[4]                 # 4.47 -> 14.60 : «3 أسباب» + the three reasons (PiP doctor)
M2_IN, M2_OUT = CUTS[5], T["ahlan"] - 0.05       # 16.60 -> ~21.0 : «فلهيك… احجز استشارتك… بشرتك مش للتجربة»
FLASH_PEAK = 15 / FPS
SPEECH_END = T["end11"]
T_MSG = T["istifsar"] + 0.05
MSG_RATE = 1.4; MSG_CLICK = 62
T_CLICK = T_MSG + MSG_CLICK / FPS / MSG_RATE
T_WIPE = T_CLICK + 0.02
T_OUTRO = T_WIPE + 0.45
OUTRO_LEN = 6.0
DUR = round(T_OUTRO + OUTRO_LEN, 3)
CY = 1330

def kin(t0, d=0.3, a=0.0, b=100.0, ease="smooth"): return keys((t0, a), (t0 + d, b), ease=ease)
def fio(t0, t1, d0=0.35, d1=0.3): return keys((t0, 0), (t0 + d0, 100), (t1 - d1, 100), (t1, 0), ease="soft")

def word_layer(c, name, txt, size, weight, col, x, y, t0, t1, rise=14, blur=10, dur=0.5, fade=0.3, shadow=SH_TXT, scale_pop=False):
    L = text(name, txt, size, weight, col, inp=t0 - 0.02, outp=t1 + 0.02, shadow=shadow)
    L.pos = keys((t0, [x, y + rise]), (t0 + dur, [x, y]), ease="smooth")
    L.op = keys((t0, 0), (t0 + dur * 0.8, 100), (t1 - fade, 100), (t1, 0), ease="soft")
    L.blur = keys((t0, blur), (t0 + dur, 0), ease="smooth")
    if scale_pop: L.scale = keys((t0, 88), (t0 + dur + 0.1, 100), ease="smooth")
    return c.add(L)

def line_layout(words, size, weight, gap=0.26, cx=540):
    ws_ = [text_width(w, size, weight) for w in words]
    g = size * gap; tot = sum(ws_) + g * (len(ws_) - 1)
    x = cx + tot / 2; xs = []
    for w_ in ws_: xs.append(x - w_ / 2); x -= w_ + g
    return xs, tot

def phrase(c, label, parts, y, t_end, size=68, weight="Bold", shadow=SH_TXT):
    """whole phrase on one centred RTL line; parts = [(text, t_in, colour)]"""
    xs, tot = line_layout([p[0] for p in parts], size, weight)
    for k, ((txt, t0, col), x) in enumerate(zip(parts, xs)):
        word_layer(c, f"{label} - {txt}", txt, size, weight, col, x, y, t0 - 0.04, t_end, rise=12, blur=10, dur=0.5, fade=0.28, shadow=shadow)
    return tot

def glass_pill(c, name, w, h, y, t0, t1, stroke=WHITE, x=540):
    return c.add(rect(name, w, h, h / 2, fill=GLASS, fill_op=62, stroke=stroke, stroke_w=2.5, stroke_op=80, pos=[x, y], shadow=SH_CARD,
                      size=keys((t0, [w * 0.6, h]), (t0 + 0.6, [w, h]), ease="smooth"), op=fio(t0, t1, 0.3, 0.3), inp=t0 - 0.02, outp=t1 + 0.02))

def icon_circle(c, name, icon, x, y, d, t0, t1):
    c.add(ellipse(name + " - دائرة", d, fill=CREAM, stroke=PINK, stroke_w=5, pos=[x, y], shadow=SH_CARD,
                  scale=keys((t0, 70), (t0 + 0.6, 100), ease="smooth"), op=fio(t0, t1, 0.4, 0.3), inp=t0 - 0.02, outp=t1 + 0.02))
    c.add(image(name + " - أيقونة", PK + icon, pos=[x, y], scale=keys((t0 + 0.1, 72), (t0 + 0.65, 100), ease="smooth"),
                op=fio(t0 + 0.1, t1, 0.4, 0.3), inp=t0 - 0.02, outp=t1 + 0.02))

def motion_bg(c, dur):
    c.add(image("خلفية وردي-عنابي", PK + "bg_pink_wine.png", pos=[540, 960], scale=keys((0, 100), (dur, 105), ease="lin")))
    c.add(image("ضو ناعم", PK + "soft_light.png", pos=keys((0, [700, 640]), (dur, [420, 820]), ease="lin"), op=55,
                scale=keys((0, 100), (dur, 115), ease="lin")))

# ---------------------------------------------------------------- M1: «من أكثر 3 أسباب بتزيد الكلف» + reasons 1-3
def build_M1():
    d = M1_OUT - M1_IN + 0.6
    c = Comp("مشهد 1 - 3 أسباب بتزيد الكلف", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M1_IN; end = d
    r1, r2, r3 = t(T["whye"]) - 0.06, t(T["istikhdam"]) - 0.06, t(T["w3adam"]) - 0.06
    # ghost numbers (very faint) behind the content, one per chapter
    for n, a, b in ((3, 0.2, r1), (1, r1, r2), (2, r2, r3), (3, r3, end)):
        c.add(text(f"رقم شبح {n}", str(n), 760, "Black", WHITE, pos=[540, 1640], op=fio(a, b, 0.5, 0.35), inp=a, outp=b + 0.02,
                   scale=keys((a, 92), (a + 0.8, 100), ease="smooth"), comment="opacity is multiplied below"))
        c.layers[-1].op = keys((a, 0), (a + 0.5, 7), (b - 0.35, 7), (b, 0), ease="soft")
    # doctor PiP card (rounded, pre-masked alpha clip) - keeps the doctor present through the whole list
    c.add(rect("بطاقة الدكتور - إطار", 512, 572, 50, fill=CREAM, fill_op=30, stroke=WHITE, stroke_w=3, stroke_op=75, pos=[540, 640], shadow=SH_CARD,
               scale=keys((0.0, 88), (0.8, 100), ease="smooth"), op=kin(0.0, 0.5, ease="soft")))
    c.add(footage("بطاقة الدكتور (فيديو)", PK + "doctor_pip_card.mov", seq="/home/user/klf/pip", start=0.0, pos=[540, 640],
                  scale=keys((0.0, 88), (0.8, 100), ease="smooth"), op=kin(0.0, 0.5, ease="soft")))
    # 1-2-3 badges on the card's bottom edge (RTL: 1 on the right); the current reason turns pink
    tb = t(T["thalath"]) - 0.1
    for n, x in ((1, 640), (2, 540), (3, 440)):
        ta = tb + (n - 1) * 0.12
        c.add(ellipse(f"شارة {n} - أبيض", 78, fill=CREAM, stroke=PINK, stroke_w=4, pos=[x, 927], shadow=SH_CARD,
                      scale=keys((ta, 50), (ta + 0.55, 100), ease="smooth"), op=kin(ta, 0.3, ease="soft"), inp=ta - 0.02))
        on = (r1, r2, r3)[n - 1]; off = (r2, r3, end)[n - 1]
        c.add(ellipse(f"شارة {n} - وردي (فعّالة)", 78, fill=PINK, stroke=WHITE, stroke_w=4, pos=[x, 927],
                      scale=keys((on, 70), (on + 0.5, 112), (off - 0.3, 112), (off, 100), ease="smooth"),
                      op=keys((on, 0), (on + 0.3, 100), (off - 0.3, 100), (off, 0) if n < 3 else (off, 100), ease="soft"), inp=on - 0.02))
        c.add(text(f"شارة {n} - رقم", str(n), 46, "Black", BURG, pos=[x, 944], scale=keys((ta + 0.05, 50), (ta + 0.6, 100), ease="smooth"),
                   op=kin(ta + 0.05, 0.3, ease="soft"), inp=ta - 0.02))
    # list title
    word_layer(c, "من أكثر", "من أكثر", 54, "Medium", WHITE, 540, 1060, t(T["min"]) - 0.04, r1)
    word_layer(c, "3 أسباب", "3 أسبـــاب", 112, "Black", WHITE, 540, 1190, t(T["thalath"]) - 0.04, r1, rise=20, dur=0.55, blur=16)
    pw = text_width("بتزيد الكلف", 74, "Black") + 120
    glass_pill(c, "كبسولة بتزيد الكلف", pw, 132, 1320, t(T["bitzeed"]) - 0.12, r1, stroke=PINK)
    word_layer(c, "بتزيد الكلف (وردي)", "بتزيد الكلف", 74, "Black", PINK, 540, 1348, t(T["bitzeed"]) - 0.04, r1, scale_pop=True)
    # reason 1 - recipes & creams
    word_layer(c, "سبب 1 - وهي: استخدام", "وهي: استخدام", 54, "Medium", WHITE, 540, 1060, r1 + 0.02, r2)
    word_layer(c, "سبب 1 - الوصفات", "الوصفـات", 100, "Black", WHITE, 540, 1180, t(T["wasfat"]) - 0.04, r2, rise=18, dur=0.55, blur=14)
    word_layer(c, "سبب 1 - والكريمات", "والكريمــات", 100, "Black", WHITE, 540, 1300, t(T["kreemat"]) - 0.04, r2, rise=18, dur=0.55, blur=14)
    icon_circle(c, "سبب 1 - وصفات", "icon_scroll_text.png", 640, 1495, 170, t(T["wasfat"]) + 0.05, r2)
    icon_circle(c, "سبب 1 - كريمات", "icon_droplets.png", 440, 1495, 170, t(T["kreemat"]) + 0.05, r2)
    # reason 2 - fast peeling without follow-up
    word_layer(c, "سبب 2 - استخدام", "استخدام", 54, "Medium", WHITE, 540, 1060, r2 + 0.02, r3)
    word_layer(c, "سبب 2 - تقشير سريع", "تقشيـر سريــع", 104, "Black", WHITE, 540, 1190, t(T["taqsheer"]) - 0.04, r3, rise=18, dur=0.55, blur=14)
    icon_circle(c, "سبب 2 - سرعة", "icon_timer.png", 540, 1348, 150, t(T["saree3"]) - 0.05, r3)
    tbd = t(T["bidoon"]) - 0.08
    pw2 = text_width("بدون متابعة", 62, "Bold") + 170
    glass_pill(c, "كبسولة بدون متابعة", pw2, 116, 1525, tbd, r3)
    c.add(image("أيقونة تقويم", PK + "icon_calendar_white.png", pos=[540 - pw2 / 2 + 62, 1525], op=fio(tbd + 0.15, r3, 0.3, 0.3), inp=tbd))
    word_layer(c, "سبب 2 - بدون متابعة", "بدون متابعة", 62, "Bold", PINK, 540 + 26, 1547, tbd + 0.04, r3, rise=10)
    # reason 3 - no moisturiser, no sunscreen
    word_layer(c, "سبب 3 - وعدم استخدام", "وعدم استخدام", 54, "Medium", WHITE, 540, 1060, r3 + 0.02, end)
    word_layer(c, "سبب 3 - المرطب", "المرطـب", 100, "Black", WHITE, 540, 1180, t(T["murattib"]) - 0.04, end, rise=18, dur=0.55, blur=14)
    word_layer(c, "سبب 3 - وواقي الشمس", "وواقي الشمــس", 100, "Black", WHITE, 540, 1300, t(T["waqi"]) - 0.04, end, rise=18, dur=0.55, blur=14)
    for nm, ic, x, tw in (("مرطب", "icon_droplet.png", 640, t(T["murattib"]) + 0.05), ("واقي شمس", "icon_cloud_sun.png", 440, t(T["waqi"]) + 0.05)):
        icon_circle(c, "سبب 3 - " + nm, ic, x, 1495, 170, tw, end)
        c.add(ellipse(f"سبب 3 - {nm} - شارة غياب", 58, fill=(0xE8, 0x3E, 0x8C), stroke=WHITE, stroke_w=3, pos=[x + 62, 1433],
                      scale=keys((tw + 0.35, 40), (tw + 0.8, 100), ease="smooth"), op=fio(tw + 0.35, end, 0.3, 0.3), inp=tw + 0.33))
        c.add(image(f"سبب 3 - {nm} - علامة ×", PK + "icon_x_white.png", pos=[x + 62, 1433], scale=keys((tw + 0.4, 40), (tw + 0.85, 100), ease="smooth"),
                    op=fio(tw + 0.4, end, 0.3, 0.3), inp=tw + 0.38))
    return c

# ---------------------------------------------------------------- M2: «فلهيك… عشان تعالج الكلف… احجز استشارتك… وبشرتك مش للتجربة»
def build_M2():
    d = M2_OUT - M2_IN + 0.6
    c = Comp("مشهد 2 - بشرتك مش للتجربة", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M2_IN; end = d
    tb = t(T["ihjiz"]) - 0.1
    word_layer(c, "فلهيك", "فلهيك،", 60, "Medium", WHITE, 540, 720, max(0.2, t(T["falhek"]) - 0.04), tb)
    word_layer(c, "عشان تعالج", "عشان تعالج", 76, "Bold", WHITE, 540, 860, t(T["ashan"]) - 0.04, tb)
    word_layer(c, "الكلف (وردي)", "الكلـــف", 150, "Black", PINK, 540, 1050, t(T["ashan"]) + 0.3, tb, rise=24, dur=0.55, blur=18, scale_pop=True)
    # booking
    icon_circle(c, "احجز - تقويم", "icon_calendar_heart.png", 540, 640, 190, tb + 0.05, end)
    pw = text_width("احجز استشارتك", 70, "Black") + 130
    glass_pill(c, "كبسولة احجز استشارتك", pw, 136, 860, tb + 0.1, end)
    word_layer(c, "احجز استشارتك", "احجز استشارتك", 70, "Black", WHITE, 540, 888, tb + 0.15, end, rise=10)
    word_layer(c, "وبشرتك", "وبشرتك", 110, "Black", WHITE, 540, 1110, t(T["wbashartak"]) - 0.04, end, rise=20, dur=0.55, blur=16)
    tm = t(T["mish"]) - 0.12; pw2 = text_width("مش للتجربـــة", 128, "Black") + 150
    c.add(rect("كبسولة عنابي زجاج", pw2, 210, 105, fill=(0x4A, 0x05, 0x1E), fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1268],
               size=keys((tm, [pw2 * 0.6, 210]), (tm + 0.65, [pw2, 210]), ease="smooth"), op=kin(tm, 0.4, ease="soft"), shadow=SH_CARD, inp=tm))
    word_layer(c, "مش للتجربة (وردي)", "مش للتجربـــة", 128, "Black", PINK, 540, 1310, t(T["mish"]), end, rise=24, dur=0.45, blur=24, scale_pop=True)
    return c

# ---------------------------------------------------------------- main comp
def build():
    C = Comp("أسباب فشل علاج الكلف - ريلز 9x16 v3", W, H, DUR, FPS, bg=DEEP)
    for i, tc in enumerate(CUTS): C.markers.append((tc, f"قص سكتة {i + 1}"))
    # doctor: close framing like the references (face ≈ upper third), slow continuous push per part, resets hidden by scenes/flash
    FACE = [510 - 540, 640 - 960]
    # v3: no zoom reset at the first cut (user: the 2 s transition must be very soft) -> one continuous glide
    zk = [K(0.0, 140), K(0.6, 128), K(M1_IN + 0.7, 133, hold=True),
          K(M1_OUT, 124), K(CUTS[5] + 0.7, 128, hold=True), K(M2_OUT, 124), K(T_OUTRO + 0.1, 130)]
    for k in zk: k.i, k.o = 60, 60
    C.add(footage("الدكتور (ملوّن + قص السكتات فقط)", PK + "doctor_graded_cut.mp4", start=0, anchor=FACE, pos=[540, 700],
                  scale=zk, inp=0, outp=T_OUTRO + 0.1,
                  blur=keys((0, 10), (0.5, 0), (CUTS[0] - 0.15, 0), (CUTS[0] + 0.08, 6), (CUTS[0] + 0.45, 0), ease="smooth")))
    # v3: the first silence cut (≈2.2 s) dissolves softly: last frame before the cut held on top and faded out
    C.add(footage("الدكتور - ذوبان ناعم عند القص الأول", PK + "doctor_graded_cut.mp4", start=0, anchor=FACE, pos=[540, 700], scale=zk,
                  remap=[K(0.0, 0.0, lin=True), K(CUTS[0] - 1 / FPS, CUTS[0] - 1 / FPS, lin=True), K(CUTS[0] + 0.6, CUTS[0] - 1 / FPS, lin=True)],
                  op=keys((CUTS[0] - 0.02, 100), (CUTS[0] + 0.35, 0), ease="soft"), inp=0, outp=CUTS[0] + 0.38,
                  blur=keys((0, 10), (0.5, 0), (CUTS[0] - 0.15, 0), (CUTS[0] + 0.1, 7), (CUTS[0] + 0.35, 7), ease="smooth")))
    C.add(image("تظليل تحت (للكابشن)", PK + "shade_bottom.png", pos=[540, 960], op=keys((0, 100), (T_OUTRO, 100), (T_OUTRO + 0.3, 0)), outp=T_OUTRO + 0.35))

    # ---- HOOK from frame 1: «الكلـــف» + glass pill «ما بيروح بالكريم»
    h_end = CUTS[0] + 0.02
    word_layer(C, "هوك - الكلف", "الكلـــــف", 150, "Black", WHITE, 540, 1200, -0.2, h_end, rise=26, dur=0.45, blur=20)
    pw = text_width("ما بيروح بالكريم", 70, "Bold") + 120
    glass_pill(C, "هوك - كبسولة زجاجية", pw, 128, 1340, T["ma"] - 0.15, h_end)
    xs, _ = line_layout(["ما بيروح", "بالكريم"], 70, "Bold")
    word_layer(C, "هوك - ما بيروح", "ما بيروح", 70, "Bold", WHITE, xs[0], 1365, T["ma"] - 0.04, h_end, rise=10)
    word_layer(C, "هوك - بالكريم (وردي)", "بالكريم", 70, "Bold", PINK, xs[1], 1365, T["bilkreem"] - 0.04, h_end, rise=10, scale_pop=True)
    # ---- captions (doctor parts)
    phrase(C, "كابشن 1", [("بيروح لما تعرف", T["yrooh"], WHITE)], CY, T["sababo"] - 0.06)
    phrase(C, "كابشن 2", [("سببه", T["sababo"], WHITE), ("الصحيح", T["sahih"] - 0.1, PINK)], CY, M1_IN + 0.3)
    # diagnosis card on the doctor (after the flash)
    t0 = T["wba3d"] - 0.1; t1 = CUTS[5] + 0.3
    phrase(C, "كابشن 3 - وبعض", [("وبعض", T["wba3d"], WHITE)], CY - 150, t1, 60, "Medium")
    cw = 820
    C.add(rect("بطاقة التشخيص - زجاج", cw, 190, 95, fill=GLASS, fill_op=62, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, CY - 22], shadow=SH_CARD,
               size=keys((t0, [cw * 0.6, 190]), (t0 + 0.65, [cw, 190]), ease="smooth"), op=fio(t0, t1, 0.35, 0.3), inp=t0 - 0.02, outp=t1 + 0.02))
    C.add(image("بطاقة التشخيص - أيقونة بحث", PK + "icon_search_white.png", pos=[540 + 330, CY - 22], scale=keys((t0 + 0.2, 60), (t0 + 0.7, 100), ease="smooth"),
                op=fio(t0 + 0.2, t1, 0.3, 0.3), inp=t0, outp=t1 + 0.02))
    xs, _ = line_layout(["التشخيص", "الخاطئ"], 84, "Black", 0.22, cx=520)
    word_layer(C, "التشخيص", "التشخيص", 84, "Black", WHITE, xs[0], CY + 8, T["tashkhees"] - 0.04, t1)
    word_layer(C, "الخاطئ (وردي)", "الخاطئ", 84, "Black", PINK, xs[1], CY + 8, T["khate"] - 0.04, t1, scale_pop=True)
    # welcome
    phrase(C, "كابشن 4", [("أهلًا وسهلًا فيكم", T["ahlan"], WHITE)], CY, T["markaz"] - 0.06)
    phrase(C, "كابشن 5", [("مركز", T["markaz"], WHITE), ("بالديرما", T["markaz"] + 0.3, PINK)], CY, T_MSG - 0.02, 76, "Black")

    # ---- motion scenes (soft entry on a cut = the cut is hidden), exit under the user's flash
    for comp_, tin, tout, nm in ((build_M1(), M1_IN, M1_OUT, "مشهد 1 - 3 أسباب"), (build_M2(), M2_IN, M2_OUT, "مشهد 2 - بشرتك مش للتجربة")):
        C.add(precomp(nm, comp_, start=tin, inp=tin, outp=tout + 0.12,
                      op=keys((tin, 0), (tin + 0.5, 100), (tout - 0.12, 100), (tout + 0.12, 0), ease="soft"),
                      scale=keys((tin, 106), (tin + 0.9, 100), ease="smooth"), blur=keys((tin, 30), (tin + 0.6, 0), ease="smooth")))
        C.markers.append((tin, "دخول " + nm + " (ووش)"))
    for tp in (M1_OUT, M2_OUT):
        C.add(footage("انتقال فلاش (ملف المستخدم)", PK + "flash_transition.mov", seq="/home/user/klf/flash", start=tp - FLASH_PEAK, inp=tp - FLASH_PEAK, outp=tp - FLASH_PEAK + 24 / FPS))
        C.markers.append((tp, "فلاش رجوع للدكتور"))

    # ---- brand frame (every frame until the outro), messenger -> pink circle -> outro + WhatsApp
    # v3: top dark shade removed (user)
    C.add(image("قالب الهوية (الإطار)", PK + "frame_template_9x16.png", pos=[540, 960], op=keys((T_WIPE, 100), (T_WIPE + 0.3, 0)), outp=T_WIPE + 0.35))
    C.add(footage("زر مراسلة الصفحة (ثابت على الضغطة)", PK + "messenger_button.mov", seq="/home/user/klf/msg", start=T_MSG, inp=T_MSG, outp=T_OUTRO + 0.05,
                  remap=[K(T_MSG, 0.0, lin=True), K(T_CLICK, MSG_CLICK / FPS, lin=True), K(T_OUTRO + 0.05, MSG_CLICK / FPS, lin=True)]))
    C.add(ellipse("دائرة وردية (انتقال الخاتمة)", 40, fill=OUTRO_PINK, pos=[540, 960], size=keys((T_WIPE, [40, 40]), (T_OUTRO, [2400, 2400]), ease="in"),
                  inp=T_WIPE, outp=T_OUTRO + 0.4))
    C.add(footage("خاتمة بالديرما الوردية", PK + "palderma_pink_outro.mp4", start=T_OUTRO - 0.05, inp=T_OUTRO - 0.05, outp=DUR,
                  op=keys((T_OUTRO - 0.05, 0), (T_OUTRO + 0.25, 100), ease="soft")))
    # v3: WhatsApp line + number removed from the outro (user)
    C.markers += [(T_MSG, "زر المراسلة"), (T_WIPE, "دائرة وردية"), (T_OUTRO, "الخاتمة الوردية")]
    return C

if __name__ == "__main__":
    C = build()
    print("dur", DUR, "M1", M1_IN, M1_OUT, "M2", M2_IN, M2_OUT, "msg", T_MSG, "outro", T_OUTRO)
    import numpy as np
    from PIL import Image
    for tt in [float(x) for x in sys.argv[1:]]:
        fr = render_comp(C, tt)
        Image.fromarray(fr.clip(0, 255).astype(np.uint8)).save(f"/home/user/klf/prev/q_{tt:05.2f}.jpg", quality=88)
