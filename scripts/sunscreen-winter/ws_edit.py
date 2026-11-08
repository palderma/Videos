#!/usr/bin/env python3
"""«ضرورة واقي الشمس بالشتاء» - Palderma doctor reel in the approved «أسباب فشل علاج الكلف» v6 look:
hook = the doctor ON SCREEN saying «بالنسبة لواقي الشمس يجب استخدامه صيفًا وشتاءً» (+ wine glass capsule), user's flash,
brand frame on every frame, close doctor on his original window background, white phrase captions with pink key words
(no lines / circles), full-screen pink->wine motion scenes with a doctor PiP card (watch/phone/UV scene, winter vs summer
UV bars), glass cards on the doctor, messenger button -> pink circle -> pink Palderma outro (logo only).
Soft everything: 6-frame dissolves at every pause cut, very slow continuous zooms, no punches.
The same kf scene graph renders the MP4 and exports the After Effects project."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf import *
from ws_cuts import o, CUTS, KEEP_F, STARTS, XF, DOC_LEN

PKG = os.environ.get("WS_PKG", "/home/user/ws/pkg")
PK = PKG + "/footage/"
SEQ = "/home/user/ws/"
W, H, FPS = 1080, 1920, 30
BURG = (0x6C, 0x0D, 0x2B); PINK = (0xF3, 0xA5, 0xBD); WHITE = (255, 255, 255); DEEP = (40, 3, 15); CREAM = (255, 247, 250)
OUTRO_PINK = (234, 153, 188); GLASS = (58, 8, 26); WINE_GLASS = (0x4A, 0x05, 0x1E)
SH_TXT = dict(color=DEEP, op=150, dist=4, soft=26, dir=180)
SH_CARD = dict(color=DEEP, op=90, dist=10, soft=40, dir=180)

# word / phrase onsets in RAW seconds (pause edges @10 ms + whisper large-v3 per phrase)
R = dict(tarif=1.25, saa=1.80, thakiya=3.15, aw=4.20, tags=5.30, jawal=5.95,
         mumkin=7.32, qadeesh=8.87, waqi=10.45, wtkoon=11.82, harees=12.40, bistimrar=14.08,
         hasab=15.45, uv=16.16, uvab=17.15, illi=18.67, saa2=19.40, samsung=20.75,
         tabi=22.86, umoor=24.65, khsusan=25.31, shita=26.05, li2no=27.37, btkoon=29.35, a3la=31.03, sayf=31.95,
         lahek=32.71, binnisba=34.26, waqi2=34.85, yajib=35.59, sayfan=36.65, end_hook=37.69,
         wmumkin=38.06, kul=39.35, ahlan=40.88, markaz=41.90, istifsar=42.85, end=43.85)
T = {k: o(v) for k, v in R.items()}

M1_IN, M1_OUT = o(6.95), o(14.95)              # 5.63 -> 12.17 : «ممكن يعطيك قديش… واقي الشمس… باستمرار»
M2_IN, M2_OUT = o(22.5), o(32.60)             # 18.20 -> ~27.8 : «تابعي هذه الأمور… الشتاء… أعلى بكثير من الصيف»
FLASH_PEAK = 15 / FPS
SPEECH_END = T["end"]
T_MSG = T["istifsar"] + 0.05
MSG_RATE = 1.4; MSG_CLICK = 62
T_CLICK = T_MSG + MSG_CLICK / FPS / MSG_RATE
T_WIPE = T_CLICK + 0.02
T_OUTRO = T_WIPE + 0.45
OUTRO_LEN = 6.0
DUR = round(T_OUTRO + OUTRO_LEN, 3)
CY = 1480
FACE = [500 - 540, 610 - 960]

def kin(t0, d=0.3, a=0.0, b=100.0, ease="smooth"): return keys((t0, a), (t0 + d, b), ease=ease)
def fio(t0, t1, d0=0.4, d1=0.35): return keys((t0, 0), (t0 + d0, 100), (t1 - d1, 100), (t1, 0), ease="soft")

def word_layer(c, name, txt, size, weight, col, x, y, t0, t1, rise=12, blur=10, dur=0.6, fade=0.35, shadow=SH_TXT, scale_pop=False):
    L = text(name, txt, size, weight, col, inp=t0 - 0.02, outp=t1 + 0.02, shadow=shadow)
    L.pos = keys((t0, [x, y + rise]), (t0 + dur, [x, y]), ease="smooth")
    L.op = keys((t0, 0), (t0 + dur * 0.8, 100), (t1 - fade, 100), (t1, 0), ease="soft")
    L.blur = keys((t0, blur), (t0 + dur, 0), ease="smooth")
    if scale_pop: L.scale = keys((t0, 92), (t0 + dur + 0.15, 100), ease="smooth")
    return c.add(L)

def line_layout(words, size, weight, gap=0.26, cx=540):
    ws_ = [text_width(w, size, weight) for w in words]
    g = size * gap; tot = sum(ws_) + g * (len(ws_) - 1)
    x = cx + tot / 2; xs = []
    for w_ in ws_: xs.append(x - w_ / 2); x -= w_ + g
    return xs, tot

def phrase(c, label, parts, y, t_end, size=68, weight="Bold", cx=540):
    """whole phrase on one centred RTL line; parts = [(text, t_in, colour)]"""
    xs, tot = line_layout([p[0] for p in parts], size, weight, cx=cx)
    for (txt, t0, col), x in zip(parts, xs):
        word_layer(c, f"{label} - {txt}", txt, size, weight, col, x, y, t0 - 0.04, t_end)
    return tot

def glass_pill(c, name, w, h, y, t0, t1, stroke=WHITE, x=540, fill=GLASS, fill_op=62):
    return c.add(rect(name, w, h, h / 2, fill=fill, fill_op=fill_op, stroke=stroke, stroke_w=2.5, stroke_op=85, pos=[x, y], shadow=SH_CARD,
                      size=keys((t0, [w * 0.6, h]), (t0 + 0.7, [w, h]), ease="smooth"), op=fio(t0, t1, 0.35, 0.35), inp=t0 - 0.02, outp=t1 + 0.02))

def icon_circle(c, name, icon, x, y, d, t0, t1):
    c.add(ellipse(name + " - دائرة", d, fill=CREAM, stroke=PINK, stroke_w=5, pos=[x, y], shadow=SH_CARD,
                  scale=keys((t0, 75), (t0 + 0.7, 100), ease="smooth"), op=fio(t0, t1, 0.45, 0.35), inp=t0 - 0.02, outp=t1 + 0.02))
    c.add(image(name + " - أيقونة", PK + icon, pos=[x, y], scale=keys((t0 + 0.1, 78), (t0 + 0.75, 100), ease="smooth"),
                op=fio(t0 + 0.1, t1, 0.45, 0.35), inp=t0 - 0.02, outp=t1 + 0.02))

def motion_bg(c, dur):
    c.add(image("خلفية وردي-عنابي", PK + "bg_pink_wine.png", pos=[540, 960], scale=keys((0, 100), (dur, 104), ease="lin")))
    c.add(image("ضو ناعم", PK + "soft_light.png", pos=keys((0, [700, 640]), (dur, [440, 800]), ease="lin"), op=55,
                scale=keys((0, 100), (dur, 112), ease="lin")))

def pip_card(c, nm, seqname, w, h, y, dur):
    c.add(rect(nm + " - إطار", w, h, 48, fill=CREAM, fill_op=30, stroke=WHITE, stroke_w=3, stroke_op=75, pos=[540, y], shadow=SH_CARD,
               scale=keys((0.0, 90), (0.9, 100), ease="smooth"), op=kin(0.0, 0.55, ease="soft")))
    c.add(footage(nm + " (فيديو)", PK + seqname + ".mov", seq=SEQ + seqname, start=0.0, pos=[540, y],
                  scale=keys((0.0, 90), (0.9, 100), ease="smooth"), op=kin(0.0, 0.55, ease="soft")))

# ---------------------------------------------------------------- M1: «ممكن يعطيك قديش تستخدم من واقي الشمس… حريص… باستمرار»
def build_M1():
    d = M1_OUT - M1_IN + 0.6
    c = Comp("مشهد 1 - الساعة بتقلك قديش", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M1_IN; end = d
    c.add(text("UV شبح", "UV", 640, "Black", WHITE, pos=[540, 1700], op=keys((0.2, 0), (0.9, 7), (end - 0.4, 7), (end, 0), ease="soft"),
               scale=keys((0.2, 94), (end, 100), ease="lin")))
    pip_card(c, "بطاقة الدكتور", "pip_m1", 512, 572, 640, d)
    b2 = t(T["wtkoon"]) - 0.08
    # block 1
    word_layer(c, "ممكن يعطيك", "ممكن يعطيك", 56, "Medium", WHITE, 540, 1060, 0.25, b2)
    word_layer(c, "قديش تستخدم", "قديش تستخدم", 104, "Black", WHITE, 540, 1195, t(T["qadeesh"]) - 0.04, b2, rise=16, blur=14)
    tp = t(T["waqi"]) - 0.12; pw = text_width("من واقي الشمس", 74, "Black") + 130
    glass_pill(c, "كبسولة واقي الشمس", pw, 132, 1345, tp, b2, stroke=PINK)
    word_layer(c, "من واقي الشمس (وردي)", "من واقي الشمس", 74, "Black", PINK, 540, 1372, tp + 0.06, b2, scale_pop=True)
    icon_circle(c, "ساعة", "icon_watch.png", 650, 1530, 150, 0.45, b2)
    icon_circle(c, "جوال", "icon_smartphone.png", 430, 1530, 150, 0.7, b2)
    # block 2
    word_layer(c, "وتكون حريص", "وتكون حريص", 56, "Medium", WHITE, 540, 1060, b2 + 0.1, end)
    word_layer(c, "على استخدامه", "على استخدامـه", 104, "Black", WHITE, 540, 1195, t(T["harees"]) - 0.04, end, rise=16, blur=14)
    tb = t(T["bistimrar"]) - 0.15; pw2 = text_width("باستمرار", 74, "Black") + 190
    glass_pill(c, "كبسولة باستمرار", pw2, 132, 1345, tb, end + 0.3, stroke=PINK)
    c.add(image("أيقونة تكرار", PK + "icon_repeat_white.png", pos=[540 - pw2 / 2 + 70, 1345], op=fio(tb + 0.15, end + 0.3, 0.3, 0.3), inp=tb))
    word_layer(c, "باستمرار (وردي)", "باستمرار", 74, "Black", PINK, 540 + 28, 1372, tb + 0.06, end + 0.3, scale_pop=True)
    icon_circle(c, "واقي - درع", "icon_shield_check.png", 540, 1530, 150, b2 + 0.25, end + 0.3)
    return c

# ---------------------------------------------------------------- M2: winter vs summer UV
def build_M2():
    d = M2_OUT - M2_IN + 0.6
    c = Comp("مشهد 2 - الشتاء أعلى من الصيف", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M2_IN; end = d
    pip_card(c, "بطاقة الدكتور", "pip_m2", 400, 446, 520, d)
    tl = t(T["li2no"]) - 0.1
    # part 1: «تابعي هذه الأمور وخصوصًا بفصل الشتاء»
    word_layer(c, "تابعي هذه الأمور", "تابعي هذه الأمور", 60, "Medium", WHITE, 540, 880, 0.3, tl)
    icon_circle(c, "شمس وغيم", "icon_cloud_sun.png", 540, 1110, 170, 0.5, t(T["khsusan"]) - 0.1)
    word_layer(c, "وخصوصًا", "وخصوصًا", 70, "Bold", WHITE, 540, 1010, t(T["khsusan"]) - 0.04, tl)
    word_layer(c, "بفصل الشتاء (وردي)", "بفصل الشتـــاء", 120, "Black", PINK, 540, 1160, t(T["shita"]) - 0.1, tl, rise=18, blur=16, scale_pop=True)
    icon_circle(c, "ثلج", "icon_snowflake.png", 540, 1360, 170, t(T["shita"]) + 0.1, tl)
    # part 2: «لأنه أحيانًا بفصل الشتاء بتكون UVA و UVB أعلى بكثير من فصل الصيف»
    ta = t(T["a3la"]) - 0.06
    word_layer(c, "أحيانًا بالشتاء", "أحيانًا بفصل الشتاء", 64, "Bold", WHITE, 540, 880, tl + 0.05, ta)
    word_layer(c, "أعلى بكثير (وردي)", "أعلى بكثيـــر", 104, "Black", PINK, 540, 895, ta, end + 0.3, rise=16, blur=14, scale_pop=True)
    pc = 1300; ph = 600; pw = 780
    c.add(rect("لوحة المقارنة - زجاج", pw, ph, 56, fill=GLASS, fill_op=55, stroke=WHITE, stroke_w=2.5, stroke_op=70, pos=[540, pc], shadow=SH_CARD,
               size=keys((tl, [pw, ph * 0.7]), (tl + 0.8, [pw, ph]), ease="smooth"), op=keys((tl, 0), (tl + 0.5, 100), ease="soft"), inp=tl - 0.02))
    tu = t(T["btkoon"]) + 0.2
    xs, _ = line_layout(["UVA", "·", "UVB"], 62, "Black", 0.35)
    for s_, x in zip(["UVA", "·", "UVB"], xs):
        word_layer(c, "عنوان اللوحة " + s_, s_, 62, "Black", WHITE, x, 1085, tu, end + 0.3)
    base = 1470; bw = 200
    for nm, x, col, ic, lab, h1, h2 in (("الشتاء", 540 + 160, PINK, "icon_snowflake_white.png", "الشتاء", 230, 380),
                                         ("الصيف", 540 - 160, CREAM, "icon_sun_white.png", "الصيف", 200, 200)):
        tg = tl + 0.5 if nm == "الشتاء" else tl + 0.7
        hk = [(tg, 8), (tg + 0.9, h1)] + ([(ta, h1), (ta + 1.1, h2)] if h2 != h1 else [])
        c.add(rect(f"عمود {nm}", bw, 8, 30, fill=col, fill_op=96 if nm == "الشتاء" else 70, pos=keys(*[(tt, [x, base - hh / 2]) for tt, hh in hk], ease="smooth"),
                   size=keys(*[(tt, [bw, hh]) for tt, hh in hk], ease="smooth"), shadow=SH_CARD, op=kin(tg, 0.3, ease="soft"), inp=tg - 0.02))
        word_layer(c, f"عنوان {nm}", lab, 58, "Bold", WHITE, x + 26, base + 75, tg + 0.1, end + 0.3)
        c.add(image(f"أيقونة {nm}", PK + ic, pos=[x - text_width(lab, 58, "Bold") / 2 - 10, base + 56], op=fio(tg + 0.15, end + 0.3, 0.4, 0.3), inp=tg))
    return c

# ---------------------------------------------------------------- body (doctor + captions + scenes + outro)
def build():
    C = Comp("ضرورة واقي الشمس بالشتاء - الجسم", W, H, DUR, FPS, bg=DEEP)
    for i, tc in enumerate(CUTS): C.markers.append((tc, f"قص سكتة {i + 1} (ذوبان 6 فريم)"))
    # very slow continuous push per doctor part; resets hidden under the scenes
    zk = [K(0.0, 129), K(M1_IN + 0.6, 131.5, hold=True), K(M1_OUT, 128), K(M2_IN + 0.6, 131, hold=True), K(M2_OUT, 128), K(T_OUTRO + 0.1, 133.5)]
    for k in zk: k.i, k.o = 45, 45
    C.add(footage("الدكتور (ملوّن + قص السكتات بذوبان ناعم)", PK + "doctor_graded_cut.mp4", start=0, anchor=FACE, pos=[540, 700],
                  scale=zk, inp=0, outp=T_OUTRO + 0.1))
    C.add(image("تظليل تحت (للكابشن)", PK + "shade_bottom.png", pos=[540, 960], op=keys((0, 100), (T_OUTRO, 100), (T_OUTRO + 0.3, 0)), outp=T_OUTRO + 0.35))

    # ---- part A: «تعرف إنه الساعة الذكية أو أي برنامج للطقس على الجوال»
    ta2 = T["aw"] - 0.06
    phrase(C, "كابشن 1", [("تعرف إنه", T["tarif"], WHITE), ("الساعة الذكية", T["saa"], PINK)], CY, ta2)
    icon_circle(C, "كابشن 1 - ساعة", "icon_watch.png", 540, 1322, 130, T["saa"], ta2)
    phrase(C, "كابشن 2", [("أو أي برنامج", T["aw"], WHITE), ("للطقس", T["tags"], PINK)], CY, M1_IN + 0.4)
    phrase(C, "كابشن 2 - على الجوال", [("على الجوال", T["jawal"], WHITE)], CY + 95, M1_IN + 0.4, 60, "Medium")
    icon_circle(C, "كابشن 2 - طقس", "icon_cloud_sun.png", 540, 1322, 130, T["aw"] + 0.1, M1_IN + 0.4)

    # ---- part B: «حسب الـUV… UVA و UVB… اللي بتعطيها ساعة سامسونج أو ساعة أبل»
    t0 = T["hasab"] - 0.06; t1 = T["illi"] - 0.06
    phrase(C, "كابشن 3 - حسب", [("حسب الـ", T["hasab"], WHITE), ("UV", T["uv"], PINK)], CY - 160, t1, 64, "Bold")
    tc = T["uvab"] - 0.15; cw = 760
    C.add(rect("بطاقة UVA UVB - زجاج", cw, 180, 90, fill=GLASS, fill_op=62, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, CY - 10], shadow=SH_CARD,
               size=keys((tc, [cw * 0.6, 180]), (tc + 0.7, [cw, 180]), ease="smooth"), op=fio(tc, t1, 0.4, 0.35), inp=tc - 0.02, outp=t1 + 0.02))
    xs, _ = line_layout(["UVA", "و", "UVB"], 92, "Black", 0.4)
    for s_, x, col in zip(["UVA", "و", "UVB"], xs, [PINK, WHITE, PINK]):
        word_layer(C, "بطاقة - " + s_, s_, 92 if s_ != "و" else 70, "Black", col, x, CY + 22, tc + 0.1 + (0.3 if s_ == "UVB" else 0), t1)
    ts = T["samsung"] - 0.06
    phrase(C, "كابشن 4", [("اللي بتعطيها", T["illi"], WHITE), ("الساعة", T["saa2"], PINK)], CY, ts)
    phrase(C, "كابشن 5", [("ساعة سامسونج", T["samsung"], WHITE), ("أو ساعة أبل", T["samsung"] + 0.7, WHITE)], CY, M2_IN + 0.4, 64)

    # ---- part C: «لهيك احنا بنقول: بالنسبة لواقي الشمس يجب استخدامه صيفًا وشتاءً… وممكن بالشتاء يكون كل ساعة ونص»
    tbn = T["binnisba"] - 0.06
    phrase(C, "كابشن 6", [("لهيك احنا", T["lahek"], WHITE), ("بنقول", T["lahek"] + 0.45, WHITE)], CY, tbn)
    tw = T["wmumkin"] - 0.06
    phrase(C, "كابشن 7 - بالنسبة", [("بالنسبة", T["binnisba"], WHITE), ("لواقي الشمس", T["waqi2"], PINK)], 1325, tw, 62, "Bold")
    word_layer(C, "كابشن 7 - يجب استخدامه", "يجب استخدامه", 78, "Black", WHITE, 540, 1432, T["yajib"] - 0.04, tw)
    tm = T["sayfan"] - 0.15; pw2 = text_width("صيفًا وشتاءً", 108, "Black") + 150
    C.add(rect("كبسولة صيفًا وشتاءً - عنابي زجاج", pw2, 184, 92, fill=WINE_GLASS, fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1572],
               size=keys((tm, [pw2 * 0.6, 184]), (tm + 0.7, [pw2, 184]), ease="smooth"), op=fio(tm, tw, 0.4, 0.35), shadow=SH_CARD, inp=tm, outp=tw + 0.02))
    word_layer(C, "صيفًا وشتاءً (وردي)", "صيفًا وشتاءً", 108, "Black", PINK, 540, 1609, T["sayfan"] - 0.04, tw, rise=16, blur=18, scale_pop=True)
    ta = T["ahlan"] - 0.06
    phrase(C, "كابشن 8 - وممكن بالشتاء", [("وممكن", T["wmumkin"], WHITE), ("بالشتاء", T["wmumkin"] + 0.5, PINK), ("يكون", T["wmumkin"] + 0.95, WHITE)], 1330, ta, 64, "Bold")
    tk = T["kul"] - 0.15; pw3 = text_width("كل ساعة ونص", 92, "Black") + 210
    glass_pill(C, "كبسولة كل ساعة ونص", pw3, 160, 1495, tk, ta, stroke=PINK)
    C.add(image("أيقونة مؤقت", PK + "icon_timer_white.png", pos=[540 - pw3 / 2 + 80, 1495], op=fio(tk + 0.2, ta, 0.35, 0.35), inp=tk, outp=ta + 0.02))
    word_layer(C, "كل ساعة ونص (وردي)", "كل ساعة ونص", 92, "Black", PINK, 540 + 30, 1527, T["kul"] - 0.04, ta, scale_pop=True)
    phrase(C, "كابشن 9", [("أهلًا وسهلًا بكم", T["ahlan"], WHITE)], CY, T["markaz"] - 0.06)
    phrase(C, "كابشن 10", [("من مركز", T["markaz"], WHITE), ("بالديرما", T["markaz"] + 0.35, PINK)], CY, T_MSG - 0.02, 76, "Black")

    # ---- motion scenes: soft dissolve-in over a cut, exit under the user's flash
    for comp_, tin, tout, nm in ((build_M1(), M1_IN, M1_OUT, "مشهد 1 - الساعة بتقلك قديش"), (build_M2(), M2_IN, M2_OUT, "مشهد 2 - الشتاء أعلى من الصيف")):
        C.add(precomp(nm, comp_, start=tin, inp=tin - 0.05, outp=tout + 0.14,
                      op=keys((tin - 0.05, 0), (tin + 0.55, 100), (tout - 0.12, 100), (tout + 0.14, 0), ease="soft"),
                      scale=keys((tin - 0.05, 104), (tin + 1.0, 100), ease="smooth"), blur=keys((tin - 0.05, 26), (tin + 0.7, 0), ease="smooth")))
        C.markers.append((tin, "دخول " + nm + " (ذوبان + ووش)"))
    for tp in (M1_OUT, M2_OUT):
        C.add(footage("انتقال فلاش (ملف المستخدم)", PK + "flash_transition.mov", seq=SEQ + "flash", start=tp - FLASH_PEAK, inp=tp - FLASH_PEAK, outp=tp - FLASH_PEAK + 24 / FPS))
        C.markers.append((tp, "فلاش رجوع للدكتور"))

    # ---- brand frame until the outro; messenger -> pink circle -> pink outro (logo only)
    C.add(image("قالب الهوية (الإطار)", PK + "frame_template_9x16.png", pos=[540, 960], op=keys((T_WIPE, 100), (T_WIPE + 0.3, 0)), outp=T_WIPE + 0.35))
    C.add(footage("زر مراسلة الصفحة (ثابت على الضغطة)", PK + "messenger_button.mov", seq=SEQ + "msg", start=T_MSG, inp=T_MSG, outp=T_OUTRO + 0.05,
                  remap=[K(T_MSG, 0.0, lin=True), K(T_CLICK, MSG_CLICK / FPS, lin=True), K(T_OUTRO + 0.05, MSG_CLICK / FPS, lin=True)]))
    C.add(ellipse("دائرة وردية (انتقال الخاتمة)", 40, fill=OUTRO_PINK, pos=[540, 960], size=keys((T_WIPE, [40, 40]), (T_OUTRO, [2400, 2400]), ease="in"),
                  inp=T_WIPE, outp=T_OUTRO + 0.4))
    C.add(footage("خاتمة بالديرما الوردية", PK + "palderma_pink_outro.mp4", start=T_OUTRO - 0.05, inp=T_OUTRO - 0.05, outp=DUR,
                  op=keys((T_OUTRO - 0.05, 0), (T_OUTRO + 0.25, 100), ease="soft")))
    C.markers += [(T_MSG, "زر المراسلة"), (T_WIPE, "دائرة وردية"), (T_OUTRO, "الخاتمة الوردية")]
    return C

# ---------------------------------------------------------------- hook + main
SRC0 = o(34.14)                               # hook = the doctor saying «بالنسبة لواقي الشمس يجب استخدامه صيفًا وشتاءً»
VOICE_END = round(o(37.84) - SRC0, 3)        # real dip after «وشتاءً» (next word starts 38.06)
HK = round(VOICE_END + 0.18, 3)               # hook length; body starts here under the user's flash
TOTAL = round(HK + DUR, 3)
def hk(raw): return round(o(raw) - SRC0, 3)

def build_main():
    C = Comp("ضرورة واقي الشمس بالشتاء - ريلز 9x16 v1", W, H, TOTAL, FPS, bg=DEEP)
    zk = keys((0, 132), (HK, 136), ease="lin")
    C.add(footage("هوك - الدكتور (صيفًا وشتاءً)", PK + "doctor_graded_cut.mp4", start=-SRC0, anchor=FACE, pos=[540, 700], scale=zk,
                  remap=[K(0, SRC0, lin=True), K(VOICE_END, SRC0 + VOICE_END, lin=True), K(HK + 0.1, SRC0 + VOICE_END, lin=True)],
                  inp=0, outp=HK + 0.1))
    C.add(image("هوك - تظليل تحت", PK + "shade_bottom.png", pos=[540, 960], outp=HK + 0.1))
    word_layer(C, "هوك - واقي الشمس", "واقي الشمس", 112, "Black", WHITE, 540, 1285, 0.0, HK + 0.05, rise=18, dur=0.5, blur=14)
    word_layer(C, "هوك - يجب استخدامه", "يجب استخدامه", 72, "Bold", WHITE, 540, 1405, hk(R["yajib"]) - 0.04, HK + 0.05)
    tm = hk(R["sayfan"]) - 0.15; pw2 = text_width("صيفًا وشتاءً", 112, "Black") + 150
    C.add(rect("هوك - كبسولة عنابي زجاج", pw2, 190, 95, fill=WINE_GLASS, fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1548],
               size=keys((tm, [pw2 * 0.6, 190]), (tm + 0.6, [pw2, 190]), ease="smooth"), op=fio(tm, HK + 0.05, 0.35, 0.2), shadow=SH_CARD, inp=tm, outp=HK + 0.08))
    word_layer(C, "هوك - صيفًا وشتاءً (وردي)", "صيفًا وشتاءً", 112, "Black", PINK, 540, 1586, hk(R["sayfan"]) - 0.04, HK + 0.05, rise=16, dur=0.5, blur=18, scale_pop=True)
    C.add(image("هوك - قالب الهوية", PK + "frame_template_9x16.png", pos=[540, 960], outp=HK + 0.1))
    C.add(precomp("الفيديو (الجسم)", build(), start=HK, inp=HK, outp=TOTAL))
    C.add(footage("انتقال فلاش هوك -> الفيديو (ملف المستخدم)", PK + "flash_transition.mov", seq=SEQ + "flash",
                  start=HK - FLASH_PEAK, inp=HK - FLASH_PEAK, outp=HK - FLASH_PEAK + 24 / FPS))
    C.markers += [(0, "هوك: صيفًا وشتاءً"), (HK, "بداية الفيديو (فلاش)")]
    return C

if __name__ == "__main__":
    print("HK", HK, "body", DUR, "total", TOTAL, "M1", M1_IN, M1_OUT, "M2", M2_IN, M2_OUT, "msg", T_MSG, "outro", T_OUTRO)
    import numpy as np
    from PIL import Image
    C = build_main(); os.makedirs("/home/user/ws/prev", exist_ok=True)
    for tt in [float(x) for x in sys.argv[1:]]:
        Image.fromarray(render_comp(C, tt).clip(0, 255).astype(np.uint8)).save(f"/home/user/ws/prev/b_{tt:05.2f}.jpg", quality=88)
