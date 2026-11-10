#!/usr/bin/env python3
"""«بوتوكس الرجال» - Palderma doctor reel in the approved «أسباب فشل علاج الكلف» look: brand frame on every frame,
doctor close on his original window background (uncut, gently stabilised), hook title «بوتوكس / الرجال» landing in his
natural pause after «أنت كشاب», white phrase captions with pink key words (no lines / circles), two full-screen
pink->wine motion scenes with a doctor PiP card (wrinkle areas; botox for men & women + the three areas), a glass
«5 دقائق» pill synced to his raised hand, WhatsApp pill on his last sentence -> centre pink circle -> pink outro.
Soft everything: no flashes, no punches, very slow continuous zooms, blur-dissolves into and out of the scenes.
The same kf scene graph renders the MP4 and exports the After Effects project."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf import *
from bm_cuts import o, DOC_LEN

PKG = os.environ.get("BM_PKG", "/home/user/bm/pkg")
PK = PKG + "/footage/"
SEQ = "/home/user/bm/"
W, H, FPS = 1080, 1920, 30
BURG = (0x6C, 0x0D, 0x2B); PINK = (0xF3, 0xA5, 0xBD); WHITE = (255, 255, 255); DEEP = (40, 3, 15); CREAM = (255, 247, 250)
OUTRO_PINK = (234, 153, 188); GLASS = (58, 8, 26); WINE_GLASS = (0x4A, 0x05, 0x1E)
SH_TXT = dict(color=DEEP, op=150, dist=4, soft=26, dir=180)
SH_CARD = dict(color=DEEP, op=90, dist=10, soft=40, dir=180)

# word onsets, RAW seconds (pause edges + whisper large-v3 per phrase)
R = dict(anta=2.06, kashab=2.33, end1=2.66,
         wbithib=3.66, ijraa=4.13, likhfaa=4.62, tajaeed=5.29, end2=6.0,
         jabha=6.39, end3=6.91, aw=7.64, hawalain=7.95, ein=8.40, end4=8.75,
         ijraa2=9.19, faqat=9.72, lmuddat=10.07, khams=10.36, daqaiq=10.72, end5=11.35,
         mumkin=11.88, tatkhallas=12.55, minhay=13.05, tajaeed2=13.60, end6=14.06,
         wbidoon=14.44, athar=14.95, end7=15.94,
         an=16.29, hqn=16.60, botox=17.0, end8=17.92,
         naam=18.04, botox2=18.30, yuhqan=18.70, rijal=19.05, end9=19.49,
         nisaa=19.86, end10=20.67,
         bamakin=20.95, khassa=21.45, likhfaa2=21.85, tajaeed3=22.05, jabha2=22.55, end11=23.44,
         qafla=23.77, ein2=24.20, hawalain2=24.86, uyoon=25.20, end12=25.56,
         ahlan=25.94, fikum=26.66, markaz=27.17, palderma=27.62, end13=28.60,
         istifsar=28.77, end=29.80)
T = {k: o(v) for k, v in R.items()}

M1_IN, M1_OUT = o(6.12), o(8.97)      # «في الجبهة / أو حوالين العين»
M2_IN, M2_OUT = o(16.08), o(25.74)    # «عن طريق حقن البوتوكس… للرجال وللنساء… بأماكن خاصة…»
SPEECH_END = T["end"]
T_WA = T["istifsar"] - 0.35           # WhatsApp clip: line at +0.5 s, green pill at +1.0 s
T_WIPE = round(SPEECH_END + 1.55, 3)
T_OUTRO = T_WIPE + 0.45
OUTRO_LEN = 5.5
DUR = round(T_OUTRO + OUTRO_LEN, 3)
CY = 1400
FACE = [505 - 540, 645 - 960]

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

def chip(c, name, label, y, t0, t1, ton=None, toff=None, w=None, size=68):
    """glass chip that turns pink-bordered while it is the current item"""
    w = w or text_width(label, size, "Black") + 150
    glass_pill(c, name + " - كبسولة", w, 128, y, t0, t1)
    if ton is not None:
        c.add(rect(name + " - إطار وردي (فعّال)", w, 128, 64, fill=None, stroke=PINK, stroke_w=4, pos=[540, y],
                   op=keys((ton, 0), (ton + 0.3, 100), (toff - 0.3, 100), (toff, 0), ease="soft"), inp=ton - 0.02, outp=toff + 0.02))
    word_layer(c, name, label, size, "Black", WHITE, 540, y + 24, t0 + 0.05, t1, rise=10)

# ---------------------------------------------------------------- M1: «في الجبهة / أو حوالين العين»
def build_M1():
    d = M1_OUT - M1_IN + 0.6
    c = Comp("مشهد 1 - أماكن التجاعيد", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M1_IN; end = d
    pip_card(c, "بطاقة الدكتور", "pip_m1", 512, 572, 640, d)
    word_layer(c, "لإخفاء التجاعيد", "لإخفاء التجاعيد", 58, "Medium", WHITE, 540, 1060, 0.25, end)
    word_layer(c, "في الجبهة", "في الجبهـــة", 112, "Black", WHITE, 540, 1200, t(T["jabha"]) - 0.06, end, rise=16, blur=14)
    tw = t(T["aw"]) - 0.06
    pw = text_width("أو حوالين العين", 74, "Black") + 130
    glass_pill(c, "كبسولة حوالين العين", pw, 132, 1350, tw, end + 0.3, stroke=PINK)
    word_layer(c, "أو حوالين العين (وردي)", "أو حوالين العين", 74, "Black", PINK, 540, 1377, tw + 0.06, end + 0.3, scale_pop=True)
    icon_circle(c, "جبهة", "icon_scan_face.png", 650, 1545, 150, t(T["jabha"]) + 0.1, end + 0.3)
    icon_circle(c, "عين", "icon_eye.png", 430, 1545, 150, tw + 0.2, end + 0.3)
    return c

# ---------------------------------------------------------------- M2: botox for men and women, in three areas
def build_M2():
    d = M2_OUT - M2_IN + 0.6
    c = Comp("مشهد 2 - البوتوكس للرجال والنساء", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    motion_bg(c, d)
    t = lambda x: x - M2_IN; end = d
    pip_card(c, "بطاقة الدكتور", "pip_m2", 440, 492, 585, d)
    b2 = t(T["naam"]) - 0.08; b3 = t(T["bamakin"]) - 0.08
    # block 1 «عن طريق حقن البوتوكس»
    word_layer(c, "عن طريق حقن", "عن طريق حقن", 60, "Medium", WHITE, 540, 1000, 0.25, b2)
    word_layer(c, "البوتوكس", "البوتـــوكس", 136, "Black", WHITE, 540, 1165, t(T["botox"]) - 0.12, b2, rise=18, blur=16)
    icon_circle(c, "حقنة", "icon_syringe.png", 540, 1380, 170, t(T["hqn"]), b2)
    # block 2 «نعم، البوتوكس بيُحقن للرجال وللنساء»
    word_layer(c, "نعم البوتوكس بيحقن", "نعم، البوتوكس بيُحقن", 64, "Bold", WHITE, 540, 1000, b2 + 0.06, b3)
    tr, tn = t(T["rijal"]) - 0.1, t(T["nisaa"]) - 0.1
    for nm, x, tt, col, stroke in (("للرجال", 540 + 200, tr, PINK, PINK), ("وللنساء", 540 - 200, tn, WHITE, WHITE)):
        pw = 350
        glass_pill(c, "كبسولة " + nm, pw, 150, 1190, tt, b3, stroke=stroke, x=x)
        word_layer(c, nm + (" (وردي)" if col == PINK else ""), nm, 82, "Black", col, x, 1220, tt + 0.06, b3, scale_pop=True)
    icon_circle(c, "رجال ونساء", "icon_users_round.png", 540, 1400, 150, tn + 0.15, b3)
    # block 3 «بأماكن خاصة لإخفاء تجاعيد الجبهة / وقفلة العين / وحوالين العيون»
    word_layer(c, "بأماكن خاصة", "بأماكن خاصة", 64, "Bold", WHITE, 540, 930, b3 + 0.06, end + 0.3)
    word_layer(c, "لإخفاء التجاعيد", "لإخفاء التجاعيد في", 52, "Medium", WHITE, 540, 1010, t(T["likhfaa2"]) - 0.04, end + 0.3)
    tj, tq, th = t(T["jabha2"]) - 0.1, t(T["qafla"]) - 0.1, t(T["hawalain2"]) - 0.1
    chip(c, "الجبهة", "الجبهة", 1140, tj, end + 0.3, tj, tq)
    chip(c, "قفلة العين", "قفلة العين", 1300, tq, end + 0.3, tq, th)
    chip(c, "حوالين العيون", "حوالين العيون", 1460, th, end + 0.3, th, end + 0.3)
    return c

# ---------------------------------------------------------------- main
def build_main():
    C = Comp("بوتوكس الرجال - ريلز 9x16", W, H, DUR, FPS, bg=DEEP)
    # opening signature zoom-out (soft), then one very slow push per doctor part; resets hidden under the scenes;
    # the doctor clip ends at DOC_LEN and holds its last frame (no ping-pong) until the pink circle
    zk = [K(0.0, 135), K(1.0, 128), K(M1_IN + 0.6, 131, hold=True), K(M1_OUT, 127.5), K(M2_IN + 0.6, 132, hold=True),
          K(M2_OUT, 128), K(T_OUTRO + 0.1, 133)]
    for k in zk: k.i, k.o = 45, 45
    zk[0].o = 70
    C.add(footage("الدكتور (ملوّن + تثبيت ناعم، بدون قص)", PK + "doctor_graded_cut.mp4", start=0, anchor=FACE, pos=[540, 700], scale=zk,
                  remap=[K(0, 0, lin=True), K(DOC_LEN - 1 / FPS, DOC_LEN - 1 / FPS, lin=True), K(T_OUTRO + 0.1, DOC_LEN - 1 / FPS, lin=True)],
                  inp=0, outp=T_OUTRO + 0.1, blur=keys((0, 10), (0.6, 0), ease="smooth")))
    C.add(image("تظليل تحت (للكابشن)", PK + "shade_bottom.png", pos=[540, 960], op=keys((0, 100), (T_WIPE, 100), (T_WIPE + 0.3, 0)), outp=T_WIPE + 0.35))

    # ---- HOOK: «أنت كشاب» … (pause) … «بوتوكس / الرجال»
    h_end = T["wbithib"] + 0.05
    phrase(C, "هوك - أنت كشاب", [("أنت", T["anta"], WHITE), ("كشاب", T["kashab"], PINK)], 1175, h_end, 66, "Bold")
    word_layer(C, "هوك - بوتوكس", "بوتوكس", 150, "Black", WHITE, 540, 1360, T["end1"] - 0.02, h_end, rise=22, dur=0.55, blur=20)
    tm = T["end1"] + 0.22; pw = text_width("الرجـــال", 120, "Black") + 160
    C.add(rect("هوك - كبسولة عنابي زجاج", pw, 190, 95, fill=WINE_GLASS, fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1500],
               size=keys((tm, [pw * 0.6, 190]), (tm + 0.65, [pw, 190]), ease="smooth"), op=fio(tm, h_end, 0.35, 0.3), shadow=SH_CARD, inp=tm, outp=h_end + 0.02))
    word_layer(C, "هوك - الرجال (وردي)", "الرجـــال", 120, "Black", PINK, 540, 1540, tm + 0.04, h_end, rise=16, dur=0.5, blur=18, scale_pop=True)

    # ---- captions, doctor part A
    phrase(C, "كابشن 1", [("وبتحب تسوي", T["wbithib"], WHITE), ("إجراء", T["ijraa"], WHITE)], CY, T["likhfaa"] - 0.06)
    phrase(C, "كابشن 2", [("لإخفاء", T["likhfaa"], WHITE), ("التجاعيد", T["tajaeed"], PINK)], CY, M1_IN + 0.4, 76, "Black")

    # ---- part B: «إجراء فقط لمدة خمس دقائق» (his raised open hand) / «ممكن إنك تتخلص من هاي التجاعيد» / «وبدون آثار جانبية»
    tb_end = T["mumkin"] - 0.06
    phrase(C, "كابشن 3", [("إجراء فقط", T["ijraa2"], WHITE), ("لمدة", T["lmuddat"], WHITE)], CY - 40, tb_end, 64, "Bold")
    tk = T["khams"] - 0.15; pw3 = text_width("5 دقائق", 96, "Black") + 220
    glass_pill(C, "كبسولة 5 دقائق", pw3, 164, CY + 120, tk, tb_end, stroke=PINK)
    C.add(image("أيقونة مؤقت", PK + "icon_timer_white.png", pos=[540 - pw3 / 2 + 84, CY + 120], op=fio(tk + 0.2, tb_end, 0.35, 0.35), inp=tk, outp=tb_end + 0.02))
    xs, _ = line_layout(["5", "دقائق"], 96, "Black", 0.22, cx=540 + 32)
    word_layer(C, "5 (وردي)", "5", 96, "Black", PINK, xs[0], CY + 154, T["khams"] - 0.04, tb_end, scale_pop=True)
    word_layer(C, "دقائق (وردي)", "دقائق", 96, "Black", PINK, xs[1], CY + 154, T["daqaiq"] - 0.04, tb_end, scale_pop=True)
    phrase(C, "كابشن 4", [("ممكن إنك", T["mumkin"], WHITE), ("تتخلص", T["tatkhallas"], PINK)], CY, T["minhay"] - 0.06, 76, "Black")
    phrase(C, "كابشن 5", [("من هاي", T["minhay"], WHITE), ("التجاعيد", T["tajaeed2"], WHITE)], CY, T["wbidoon"] - 0.06, 76, "Black")
    phrase(C, "كابشن 6", [("وبدون", T["wbidoon"], WHITE), ("آثار جانبية", T["athar"], PINK)], CY, M2_IN + 0.4, 72, "Black")

    # ---- part C: welcome + WhatsApp
    phrase(C, "كابشن 7", [("أهلًا وسهلًا", T["ahlan"], WHITE), ("فيكم", T["fikum"], WHITE)], CY, T["markaz"] - 0.06)
    phrase(C, "كابشن 8", [("بمركز", T["markaz"], WHITE), ("بالديرما", T["palderma"], PINK)], CY, T_WA + 0.4, 76, "Black")
    C.add(footage("زر واتساب +972598219030 (ملف المستخدم)", PK + "whatsapp_pill.mov", seq=SEQ + "wa", start=T_WA, inp=T_WA, outp=T_OUTRO + 0.05,
                  pos=[540, 960 - 30]))

    # ---- motion scenes: blur-dissolve in and out (no flash)
    for comp_, tin, tout, nm in ((build_M1(), M1_IN, M1_OUT, "مشهد 1 - أماكن التجاعيد"), (build_M2(), M2_IN, M2_OUT, "مشهد 2 - البوتوكس للرجال والنساء")):
        C.add(precomp(nm, comp_, start=tin, inp=tin - 0.05, outp=tout + 0.45,
                      op=keys((tin - 0.05, 0), (tin + 0.55, 100), (tout - 0.05, 100), (tout + 0.45, 0), ease="soft"),
                      scale=keys((tin - 0.05, 104), (tin + 1.0, 100), (tout - 0.05, 100), (tout + 0.45, 103), ease="smooth"),
                      blur=keys((tin - 0.05, 26), (tin + 0.7, 0), (tout - 0.05, 0), (tout + 0.45, 22), ease="smooth")))
        C.markers += [(tin, "دخول " + nm), (tout, "رجوع للدكتور")]

    # ---- brand frame until the circle; centre pink circle -> pink outro (logo only)
    C.add(image("قالب الهوية (الإطار)", PK + "frame_template_9x16.png", pos=[540, 960], op=keys((T_WIPE, 100), (T_WIPE + 0.3, 0)), outp=T_WIPE + 0.35))
    C.add(ellipse("دائرة وردية (انتقال الخاتمة)", 40, fill=OUTRO_PINK, pos=[540, 960], size=keys((T_WIPE, [40, 40]), (T_OUTRO, [2400, 2400]), ease="in"),
                  inp=T_WIPE, outp=T_OUTRO + 0.4))
    C.add(footage("خاتمة بالديرما الوردية", PK + "palderma_pink_outro.mp4", start=T_OUTRO - 0.05, inp=T_OUTRO - 0.05, outp=DUR,
                  op=keys((T_OUTRO - 0.05, 0), (T_OUTRO + 0.25, 100), ease="soft")))
    C.markers += [(0, "هوك"), (T_WA, "واتساب"), (T_WIPE, "دائرة وردية"), (T_OUTRO, "الخاتمة الوردية")]
    return C

if __name__ == "__main__":
    print("dur", DUR, "M1", M1_IN, M1_OUT, "M2", M2_IN, M2_OUT, "wa", T_WA, "wipe", T_WIPE)
    import numpy as np
    from PIL import Image
    C = build_main(); os.makedirs("/home/user/bm/prev", exist_ok=True)
    for tt in [float(x) for x in sys.argv[1:]]:
        Image.fromarray(render_comp(C, tt).clip(0, 255).astype(np.uint8)).save(f"/home/user/bm/prev/b_{tt:05.2f}.jpg", quality=88)
