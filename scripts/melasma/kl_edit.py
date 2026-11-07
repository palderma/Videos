#!/usr/bin/env python3
"""«أسباب فشل علاج الكلف وزيادته» - Palderma doctor reel (Medical Editorial, «تجمع سوائل» line).
Doctor stays on his original wall; one evolving skin-section graphic (melanocytes + melanin granules) inside a wine
glass card over the chest; wine titles on the wall, pink key words on wine surfaces only; user's flash; messenger
button -> centre pink circle -> pink Palderma outro + WhatsApp pill.
The whole edit is a kf scene graph -> rendered here AND exported as an After Effects project (kl_build.py)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf import *

SRC = "/mnt/project-files/اسباب قشل علاج الكلف وزيادته.mp4"
PK = "/home/user/klf/pkg/footage/"
W, H, FPS = 1080, 1920, 30
WINE = (0x6C, 0x0D, 0x2B); PINK = (0xF3, 0xA5, 0xBD); WHITE = (255, 255, 255); DEEP = (40, 3, 15)
CARD = (0x5A, 0x08, 0x24); EPI = (255, 246, 242); DERM = (238, 190, 206); MEL = (107, 58, 46); MEL_D = (62, 26, 20)
OUTRO_PINK = (234, 153, 188)
SH_TXT = dict(color=DEEP, op=150, dist=4, soft=26, dir=180)
SH_WALL = dict(color=(120, 60, 75), op=40, dist=5, soft=22, dir=170)
SH_CARD = dict(color=DEEP, op=110, dist=12, soft=46, dir=180)

# ---------------------------------------------------------------- cuts (raw seconds) - only silences removed
KEEP = [(2.8667, 5.0667), (5.7333, 8.0), (8.2, 12.7), (12.9333, 15.4667), (15.5, 18.6), (18.7333, 20.7333), (21.3667, 23.1667), (23.3, 29.6)]
def o(r):
    acc = 0.0
    for a, b in KEEP:
        if r < a: return acc
        if r <= b: return acc + r - a
        acc += b - a
    return acc + r - KEEP[-1][1]
CUTS = []; _acc = 0
for a, b in KEEP[:-1]: _acc += b - a; CUTS.append(round(_acc, 4))
DOC_LEN = round(sum(b - a for a, b in KEEP), 4)

# phrase / word onsets in RAW time (pause edges @20 ms + whisper large-v3 per phrase)
R = dict(
    kalaf=2.95, ma=3.94, bilkreem=4.38, end1=4.92,
    yrooh=5.85, ta3ref=6.52, sababo=6.95, sahih=7.40, end2=7.91,
    min=8.31, thalath=8.96, bitzeed=9.60, end3=10.57,
    whye=10.69, wasfat=11.08, kreemat=11.78, end4=12.60,
    istikhdam=13.09, taqsheer=13.50, saree3=13.95, bidoon=14.40, end5=15.32,
    w3adam=15.61, murattib=16.64, waqi=17.36, end6=18.48,
    wba3d=18.85, tashkhees=19.16, khate=19.86, end7=20.66,
    falhek=21.50, ashan=22.32, end8=23.06,
    ihjiz=23.41, wbashartak=24.34, mish=25.10, end9=25.90,
    ahlan=25.94, markaz=26.86, end10=27.80,
    istifsar=27.82, end11=29.04)
T = {k: round(o(v), 3) for k, v in R.items()}

SPEECH_END = T["end11"]
T_MSG = T["istifsar"] + 0.05
MSG_RATE = 1.4                          # the button clip is played 1.4x so the click lands right after the sentence
MSG_CLICK = 62                          # last frame before the FB page (clicked button)
T_CLICK = T_MSG + MSG_CLICK / FPS / MSG_RATE
T_WIPE = T_CLICK + 0.02                 # centre pink circle
T_OUTRO = T_WIPE + 0.45
OUTRO_LEN = 6.0
DUR = round(T_OUTRO + OUTRO_LEN, 3)
FLASH_PEAK = 15 / FPS
T_FLASH = CUTS[5]                       # 16.55: after «الخاطئ», before «فلهيك»

# ---------------------------------------------------------------- helpers
def kin(t0, d=0.3, a=0.0, b=100.0, ease="smooth"): return keys((t0, a), (t0 + d, b), ease=ease)
def fio(t0, t1, d0=0.35, d1=0.3): return keys((t0, 0), (t0 + d0, 100), (t1 - d1, 100), (t1, 0), ease="soft")

def word_layer(c, name, txt, size, weight, col, x, y, t0, t1, rise=14, blur=10, dur=0.5, fade=0.3, shadow=SH_TXT, scale_pop=False):
    L = text(name, txt, size, weight, col, inp=t0 - 0.02, outp=t1 + 0.02, shadow=shadow)
    L.pos = keys((t0, [x, y + rise]), (t0 + dur, [x, y]), ease="smooth")
    L.op = keys((t0, 0), (t0 + dur * 0.8, 100), (t1 - fade, 100), (t1, 0), ease="soft")
    L.blur = keys((t0, blur), (t0 + dur, 0), ease="smooth")
    if scale_pop: L.scale = keys((t0, 90), (t0 + dur + 0.1, 100), ease="smooth")
    return c.add(L)

def line_layout(words, size, weight, gap=0.26, cx=540):
    ws_ = [text_width(w, size, weight) for w in words]
    g = size * gap; tot = sum(ws_) + g * (len(ws_) - 1)
    x = cx + tot / 2; xs = []
    for w_ in ws_: xs.append(x - w_ / 2); x -= w_ + g
    return xs, tot

def phrase(c, label, parts, y, t_end, size, weight="Bold", shadow=SH_TXT, stagger=0.0):
    """parts = [(text, t_in, colour)] laid out RTL on one centred line; each part comes in at its own spoken onset"""
    xs, tot = line_layout([p[0] for p in parts], size, weight)
    for (txt, t0, col), x in zip(parts, xs):
        word_layer(c, f"{label} - {txt}", txt, size, weight, col, x, y, t0 - 0.04, t_end, rise=12, blur=10, dur=0.5, fade=0.28, shadow=shadow)
    return tot

# ---------------------------------------------------------------- main comp
def build():
    C = Comp("أسباب فشل علاج الكلف - ريلز 9x16", W, H, DUR, FPS, bg=DEEP)
    for i, t in enumerate(CUTS): C.markers.append((t, f"قص سكتة {i + 1}"))

    # ---- doctor: one graded clip; framing changes ONLY on cuts, one slow push inside each part (no punches)
    FACE = [510 - 540, 640 - 960]          # anchor offset from frame centre -> his face
    part = [(0.0, 110, 113), (CUTS[0], 100, 103), (CUTS[1], 108, 111), (CUTS[2], 100, 103), (CUTS[3], 108, 111),
            (CUTS[4], 114, 116), (CUTS[5], 100, 103), (CUTS[6], 108, 112), (T["ahlan"] - 0.03, 100, 102)]
    zk = []
    for k, (t0, z0, z1) in enumerate(part):
        t1 = part[k + 1][0] if k + 1 < len(part) else T_OUTRO + 0.1
        zk.append(K(t0, z0, lin=True)); zk.append(K(t1 - 1 / FPS, z1, lin=True, hold=True))
    C.add(footage("الدكتور (ملوّن + قص السكتات فقط)", PK + "doctor_graded_cut.mp4", start=0, anchor=FACE, pos=[510, 640],
                  scale=zk, inp=0, outp=T_OUTRO + 0.1,
                  comment="تكبير رقمي: يتغير الكادر فقط على القصات، ودفع بطيء داخل كل جزء"))

    # ---- wall title «الكلـــف» (hook) -> running header
    tk = -0.12
    ttl = C.add(text("عنوان الجدار - الكلـــف", "الكلـــــف", 150, "Black", WINE, inp=tk, outp=T_FLASH + 0.05, shadow=SH_WALL))
    ttl.pos = keys((tk, [540, 352]), (tk + 0.55, [540, 330]), (CUTS[0] - 0.05, [540, 330]), (CUTS[0] + 0.6, [540, 262]), ease="smooth")
    ttl.scale = keys((tk, 94), (tk + 0.6, 100), (CUTS[0] - 0.05, 100), (CUTS[0] + 0.6, 58), ease="smooth")
    ttl.op = keys((tk, 0), (tk + 0.4, 100), (T_FLASH - 0.35, 100), (T_FLASH, 0), ease="soft")
    ttl.blur = keys((tk, 22), (tk + 0.5, 0), ease="smooth")

    # ---- the wine glass card over the chest (y 1050-1450), carries the skin section + headers
    c_in, c_out = 0.80, T_FLASH - 0.05
    C.add(rect("بطاقة زجاج عنابي", 820, 400, 42, fill=CARD, fill_op=84, stroke=PINK, stroke_w=2, stroke_op=45, shadow=SH_CARD,
               pos=keys((c_in, [540, 1290]), (c_in + 0.7, [540, 1250]), (c_out - 0.45, [540, 1250]), (c_out, [540, 1290]), ease="smooth"),
               size=keys((c_in, [600, 330]), (c_in + 0.7, [820, 400]), ease="smooth"),
               op=keys((c_in, 0), (c_in + 0.45, 100), (c_out - 0.4, 100), (c_out, 0), ease="soft"), inp=c_in, outp=c_out + 0.02))
    SM_Y, MAIN_Y = 1128, 1196

    def card_el(L, t0=c_in + 0.25, t1=c_out - 0.05):
        """skin elements follow the card in / out"""
        L.inp = t0 - 0.02; L.outp = t1 + 0.02
        L.op = keys((t0, 0), (t0 + 0.45, 100), (t1 - 0.35, 100), (t1, 0), ease="soft") if not animated(L.op) else L.op
        return C.add(L)

    # skin section (native shape layers: editable in AE)
    card_el(rect("جلد - الأدمة", 660, 130, 20, fill=DERM, pos=[540, 1331]))
    card_el(rect("جلد - البشرة", 660, 50, 20, fill=EPI, pos=[540, 1291]))
    card_el(rect("جلد - الطبقة القاعدية", 640, 3, 1, fill=WINE, fill_op=30, pos=[540, 1316]))
    MC = [300, 420, 540, 660, 780]
    for i, x in enumerate(MC):
        card_el(ellipse(f"خلية صبغية {i + 1}", 16, fill=WINE, fill_op=85, pos=[x, 1316]))
    GR = [(392, 1280, 10), (414, 1296, 8), (436, 1284, 11), (468, 1302, 9), (566, 1282, 10), (590, 1299, 8), (612, 1286, 11), (642, 1303, 9), (668, 1291, 8)]
    for i, (x, y, d) in enumerate(GR):
        card_el(ellipse(f"ميلانين {i + 1}", d, fill=MEL, pos=[x, y]))
    # thin top layer that peels in reason 2
    tp = T["taqsheer"] + 0.1
    peel = C.add(rect("جلد - طبقة سطحية (تتقشر)", 652, 12, 6, fill=(238, 206, 216), inp=c_in + 0.23, outp=tp + 0.5))
    peel.pos = keys((tp, [540, 1273]), (tp + 0.35, [560, 1208]), ease="in")
    peel.rot = keys((tp, 0), (tp + 0.35, -5), ease="in")
    peel.op = keys((c_in + 0.25, 0), (c_in + 0.7, 100), (tp + 0.1, 100), (tp + 0.38, 0), ease="soft")

    # ---- S1 hook: «ما بيروح بالكريم» + cream layer that sits on the surface while pigment stays below
    phrase(C, "هوك", [("ما بيروح", T["ma"], WHITE), ("بالكريم", T["bilkreem"], PINK)], MAIN_Y, CUTS[0] + 0.05, 64, "Black")
    tc = T["bilkreem"]
    cr = C.add(rect("طبقة الكريم", 600, 16, 8, fill=PINK, fill_op=92, inp=tc - 0.02, outp=CUTS[1] + 0.3))
    cr.pos = keys((tc, [540, 1226]), (tc + 0.55, [540, 1259]), ease="smooth")
    cr.op = keys((tc, 0), (tc + 0.3, 100), (CUTS[1] - 0.1, 100), (CUTS[1] + 0.25, 0), ease="soft")

    # ---- S2 promise: «بيروح لما تعرف» / «سببه الصحيح» + glass lens finds the pigment
    e2 = CUTS[1] + 0.02
    phrase(C, "الوعد سطر صغير", [("بيروح لما تعرف", T["yrooh"], WHITE)], SM_Y, e2, 42, "Medium")
    phrase(C, "الوعد", [("سببه الصحيح", T["sababo"], PINK)], MAIN_Y, e2, 64, "Black")
    tl = T["ta3ref"]; th = T["sahih"]
    halo = C.add(ellipse("هالة وردية حول الصبغة", 150, fill=PINK, inp=th - 0.02, outp=e2 + 0.02,
                         pos=[600, 1292], op=keys((th, 0), (th + 0.4, 45), (e2 - 0.3, 45), (e2, 0), ease="soft"),
                         scale=keys((th, 60), (th + 0.6, 100), ease="smooth")))
    C.layers.remove(halo); C.layers.insert([L.name for L in C.layers].index("ميلانين 1"), halo)   # behind the granules
    lp = keys((tl, [250, 1298]), (tl + 0.9, [602, 1292]), ease="smooth")
    lop = keys((tl, 0), (tl + 0.35, 100), (e2 - 0.35, 100), (e2, 0), ease="soft")
    C.add(ellipse("عدسة - زجاج", 124, fill=WHITE, fill_op=16, stroke=WHITE, stroke_w=4, pos=lp, op=lop, inp=tl - 0.02, outp=e2 + 0.02, shadow=dict(color=DEEP, op=90, dist=4, soft=14, dir=180)))
    C.add(rect("عدسة - مقبض", 54, 11, 5, fill=WHITE, rot=45, op=lop, inp=tl - 0.02, outp=e2 + 0.02,
               pos=keys((tl, [250 + 62, 1298 + 62]), (tl + 0.9, [602 + 62, 1292 + 62]), ease="smooth")))

    # ---- S3 «من أكثر 3 أسباب بتزيد الكلف» + 3 progress dots
    e3 = T["whye"] - 0.06
    phrase(C, "القائمة سطر صغير", [("من أكثر", T["min"], WHITE)], SM_Y, e3, 42, "Medium")
    phrase(C, "القائمة", [("3 أسباب", T["thalath"], WHITE), ("بتزيد الكلف", T["bitzeed"], PINK)], MAIN_Y, e3, 64, "Black")
    td = T["thalath"] + 0.2; d_out = T["wba3d"] - 0.1
    for i, x in enumerate([580, 540, 500]):           # RTL: first dot on the right
        C.add(ellipse(f"نقطة تقدم {i + 1} (فارغة)", 16, stroke=PINK, stroke_w=2.5, stroke_op=90, pos=[x, 1428],
                      op=keys((td + i * 0.08, 0), (td + i * 0.08 + 0.3, 100), (d_out - 0.3, 100), (d_out, 0), ease="soft"), inp=td, outp=d_out + 0.02))

    # ---- reasons 1-3: number badge + filled dot + header
    reasons = [
        (1, T["whye"], T["istikhdam"] - 0.06, [("وهي: استخدام", T["whye"], WHITE)], [("الوصفات", T["wasfat"], PINK), ("والكريمات", T["kreemat"], PINK)], 580),
        (2, T["istikhdam"], T["w3adam"] - 0.06, [("استخدام", T["istikhdam"], WHITE)], [("تقشير سريع", T["taqsheer"], PINK), ("بدون متابعة", T["bidoon"], WHITE)], 540),
        (3, T["w3adam"], T["wba3d"] - 0.06, [("وعدم استخدام", T["w3adam"], WHITE)], [("المرطب", T["murattib"], PINK), ("وواقي الشمس", T["waqi"], PINK)], 500),
    ]
    for n, t0, t1, sm, mn, dx in reasons:
        phrase(C, f"السبب {n} سطر صغير", sm, SM_Y, t1, 42, "Medium")
        phrase(C, f"السبب {n}", mn, MAIN_Y, t1, 60 if n != 2 else 56, "Black")
        C.add(ellipse(f"شارة السبب {n}", 84, fill=PINK, stroke=WHITE, stroke_w=3, pos=[858, 1052], shadow=SH_CARD,
                      scale=keys((t0, 55), (t0 + 0.55, 100), ease="smooth"), op=fio(t0, t1, 0.3, 0.25), inp=t0 - 0.02, outp=t1 + 0.02))
        C.add(text(f"رقم السبب {n}", str(n), 52, "Black", WINE, pos=[858, 1071], scale=keys((t0 + 0.05, 55), (t0 + 0.6, 100), ease="smooth"),
                   op=fio(t0 + 0.05, t1, 0.3, 0.25), inp=t0 - 0.02, outp=t1 + 0.02))
        C.add(ellipse(f"نقطة تقدم {n} (ممتلئة)", 16, fill=PINK, pos=[dx, 1428], scale=keys((t0 + 0.1, 30), (t0 + 0.5, 100), ease="smooth"),
                      op=keys((t0 + 0.1, 0), (t0 + 0.35, 100), (d_out - 0.3, 100), (d_out, 0), ease="soft"), inp=t0, outp=d_out + 0.02))

    # reason 1 - irritation pulse + 3 new granules
    tk_ = T["kreemat"] + 0.15
    C.add(ellipse("نبضة تهيج", 120, stroke=PINK, stroke_w=4, pos=[505, 1286], scale=keys((tk_, 30), (tk_ + 0.8, 120), ease="out"),
                  op=keys((tk_, 0), (tk_ + 0.2, 90), (tk_ + 0.8, 0), ease="soft"), inp=tk_ - 0.02, outp=tk_ + 0.85))
    for i, (x, y, d) in enumerate([(492, 1282, 9), (514, 1298, 10), (532, 1278, 8)]):
        card_el(ellipse(f"ميلانين جديد (سبب 1) {i + 1}", d, fill=MEL, pos=[x, y], scale=keys((tk_ + 0.25 + i * 0.1, 0), (tk_ + 0.75 + i * 0.1, 100), ease="smooth")), tk_ + 0.25 + i * 0.1)
    # reason 2 - fast peel (top layer above), flushed epidermis, darker granules
    tf = tp + 0.3
    card_el(rect("بشرة متهيجة بعد التقشير", 660, 50, 20, fill=PINK, pos=[540, 1291], op=keys((tf, 0), (tf + 0.5, 38), (c_out - 0.35, 38), (c_out - 0.05, 0), ease="soft")), tf)
    for i, (x, y, d) in enumerate(GR):
        card_el(ellipse(f"ميلانين أغمق (سبب 2) {i + 1}", d + 1, fill=MEL_D, pos=[x, y], op=keys((tf + 0.1 + i * 0.03, 0), (tf + 0.7 + i * 0.03, 100), (c_out - 0.35, 100), (c_out - 0.05, 0), ease="soft")), tf + 0.1)
    # reason 3 - empty droplet (no moisturiser) ; sun rays hit the skin -> melanocytes light up -> granules rise
    tm = T["murattib"]
    C.add(image("أيقونة قطرة (المرطب غائب)", PK + "icon_droplet_pink.png", pos=[238, 1232], scale=keys((tm, 60), (tm + 0.5, 100), ease="smooth"),
                op=keys((tm, 0), (tm + 0.3, 100), (tm + 0.9, 100), (tm + 1.4, 45), (d_out - 0.3, 45), (d_out, 0), ease="soft"), inp=tm - 0.02, outp=d_out + 0.02))
    ts = T["waqi"]
    C.add(ellipse("شمس", 40, fill=PINK, stroke=WHITE, stroke_w=3, pos=[848, 1222], scale=keys((ts, 40), (ts + 0.5, 100), ease="smooth"),
                  op=fio(ts, d_out, 0.3, 0.3), inp=ts - 0.02, outp=d_out + 0.02))
    for i, (x2, y2) in enumerate([(812, 1270), (760, 1268), (700, 1270)]):
        sx, sy = 848 - 18, 1222 + 10
        ln = math.hypot(x2 - sx, y2 - sy) * 0.8
        L = C.add(rect(f"شعاع شمس {i + 1}", ln, 5, 2.5, fill=WHITE, inp=ts + 0.15, outp=d_out + 0.02))
        L.pos = [(sx + x2) / 2, (sy + y2) / 2]
        L.rot = math.degrees(math.atan2(y2 - sy, x2 - sx))
        L.scale = keys((ts + 0.2 + i * 0.08, [0, 100]), (ts + 0.65 + i * 0.08, [100, 100]), ease="smooth")
        L.op = keys((ts + 0.2 + i * 0.08, 0), (ts + 0.4 + i * 0.08, 85), (d_out - 0.3, 85), (d_out, 0), ease="soft")
    tg = ts + 0.55
    for i, x in enumerate(MC):
        C.add(ellipse(f"توهج خلية صبغية {i + 1}", 34, fill=PINK, pos=[x, 1316], op=keys((tg + i * 0.05, 0), (tg + 0.3 + i * 0.05, 75), (d_out - 0.3, 75), (d_out, 0), ease="soft"),
                      scale=keys((tg + i * 0.05, 40), (tg + 0.4 + i * 0.05, 100), ease="smooth"), inp=tg - 0.02, outp=d_out + 0.02))
    for i, x in enumerate([330, 450, 690, 750]):
        card_el(ellipse(f"ميلانين صاعد (سبب 3) {i + 1}", 9, fill=MEL, pos=keys((tg + 0.2 + i * 0.07, [x, 1312]), (tg + 0.9 + i * 0.07, [x + 6, 1284]), ease="smooth"),
                        op=keys((tg + 0.2 + i * 0.07, 0), (tg + 0.45 + i * 0.07, 100), (c_out - 0.35, 100), (c_out - 0.05, 0), ease="soft")), tg + 0.2)

    # ---- S7 diagnosis: «وبعض» / «التشخيص الخاطئ» ; lens back, reveals pigment at a different depth
    e7 = c_out - 0.05
    phrase(C, "التشخيص سطر صغير", [("وبعض", T["wba3d"], WHITE)], SM_Y, e7, 42, "Medium")
    phrase(C, "التشخيص", [("التشخيص", T["tashkhees"], WHITE), ("الخاطئ", T["khate"], PINK)], MAIN_Y, e7, 64, "Black")
    tl2 = T["tashkhees"]
    lp2 = keys((tl2, [900, 1312]), (tl2 + 0.9, [610, 1342]), ease="smooth")
    lop2 = keys((tl2, 0), (tl2 + 0.35, 100), (e7 - 0.3, 100), (e7, 0), ease="soft")
    for i, (x, y, d) in enumerate([(592, 1346, 10), (614, 1362, 12), (632, 1342, 9), (602, 1372, 8)]):
        C.add(ellipse(f"صبغة عميقة {i + 1}", d, fill=MEL, pos=[x, y], op=keys((tl2 + 0.7 + i * 0.06, 0), (tl2 + 1.1 + i * 0.06, 100), (e7 - 0.3, 100), (e7, 0), ease="soft"),
                      inp=tl2 + 0.6, outp=e7 + 0.02))
    C.add(ellipse("عدسة التشخيص - زجاج", 132, fill=WHITE, fill_op=14, stroke=WHITE, stroke_w=4, pos=lp2, op=lop2, inp=tl2 - 0.02, outp=e7 + 0.02,
                  shadow=dict(color=DEEP, op=90, dist=4, soft=14, dir=180)))
    C.add(rect("عدسة التشخيص - مقبض", 56, 11, 5, fill=WHITE, rot=45, op=lop2, inp=tl2 - 0.02, outp=e7 + 0.02,
               pos=keys((tl2, [900 + 66, 1312 + 66]), (tl2 + 0.9, [610 + 66, 1342 + 66]), ease="smooth")))

    # ---- user's flash at the cut before «فلهيك»
    C.add(footage("انتقال فلاش (ملف المستخدم)", PK + "flash_transition.mov", seq="/home/user/klf/flash", start=T_FLASH - FLASH_PEAK,
                  inp=T_FLASH - FLASH_PEAK, outp=T_FLASH - FLASH_PEAK + 24 / FPS))
    C.markers.append((T_FLASH, "فلاش (تغطية كاملة)"))

    # ---- S8 captions on the chest, on a soft wine glass plate (calms the pocket embroidery behind the words)
    CY = 1240
    p0, p1 = T_FLASH + 0.05, T_MSG - 0.02
    C.add(rect("لوح زجاجي خلف الكابشن", 900, 330, 80, fill=CARD, fill_op=62, pos=[540, 1222], blur=30,
               op=keys((p0, 0), (p0 + 0.5, 100), (p1 - 0.35, 100), (p1, 0), ease="soft"), inp=p0, outp=p1 + 0.02))
    e8a = T["ashan"] - 0.04
    phrase(C, "كابشن 1", [("فلهيك،", T["falhek"], WHITE)], CY, e8a, 72)
    phrase(C, "كابشن 2", [("عشان", T["ashan"], WHITE), ("تعالج الكلف", T["ashan"] + 0.28, PINK)], CY, CUTS[6] + 0.02, 72)

    # ---- S9 «احجز استشارتك» (wall pill) + «وبشرتك / مش للتجربة»
    ti = T["ihjiz"]; e9 = T["ahlan"] - 0.04
    pw = text_width("احجز استشارتك", 54, "Bold") + 150
    C.add(rect("كبسولة احجز استشارتك", pw, 112, 56, fill=WINE, fill_op=94, stroke=PINK, stroke_w=2, stroke_op=60, pos=[540, 300], shadow=SH_WALL,
               size=keys((ti - 0.05, [pw * 0.55, 112]), (ti + 0.55, [pw, 112]), ease="smooth"), op=fio(ti - 0.05, e9, 0.3, 0.3), inp=ti - 0.07, outp=e9 + 0.02))
    C.add(image("أيقونة تقويم", PK + "icon_calendar_heart_white.png", pos=[540 - (pw - 150) / 2 - 18, 300], op=fio(ti + 0.15, e9, 0.3, 0.3),
                scale=keys((ti + 0.15, 60), (ti + 0.6, 100), ease="smooth"), inp=ti, outp=e9 + 0.02))
    word_layer(C, "احجز استشارتك", "احجز استشارتك", 54, "Bold", WHITE, 540 + 24, 319, ti + 0.05, e9, rise=10, shadow=None)
    word_layer(C, "وبشرتك", "وبشرتك", 84, "Bold", WHITE, 540, 1180, T["wbashartak"] - 0.04, e9, rise=14)
    word_layer(C, "مش للتجربة (وردي)", "مش للتجربــــة", 112, "Black", PINK, 540, 1320, T["mish"] - 0.04, e9, rise=22, blur=18, dur=0.6, scale_pop=True)

    # ---- S10 welcome + official logo on the wall
    e10 = T_MSG - 0.04
    phrase(C, "كابشن 3", [("أهلًا وسهلًا فيكم", T["ahlan"], WHITE)], CY - 60, e10, 66)
    phrase(C, "كابشن 4", [("مركز", T["markaz"], WHITE), ("بالديرما", T["markaz"] + 0.3, PINK)], CY + 40, e10, 76, "Black")
    tlg = T["markaz"] - 0.05
    C.add(image("شعار بالديرما الرسمي (عنابي)", PK + "logo_burgundy.png", pos=keys((tlg, [540, 318]), (tlg + 0.7, [540, 300]), ease="smooth"),
                scale=keys((tlg, 90), (tlg + 0.8, 100), ease="smooth"), blur=keys((tlg, 18), (tlg + 0.6, 0), ease="smooth"),
                op=keys((tlg, 0), (tlg + 0.45, 100), (T_WIPE, 100), (T_WIPE + 0.3, 0), ease="soft"), inp=tlg - 0.02, outp=T_WIPE + 0.32))

    # ---- S11 messenger button (held on the click) -> centre pink circle -> pink outro + WhatsApp
    C.add(footage("زر مراسلة الصفحة (ثابت على الضغطة)", PK + "messenger_button.mov", seq="/home/user/klf/msg", start=T_MSG, inp=T_MSG, outp=T_OUTRO + 0.05,
                  remap=[K(T_MSG, 0.0, lin=True), K(T_CLICK, MSG_CLICK / FPS, lin=True), K(T_OUTRO + 0.05, MSG_CLICK / FPS, lin=True)]))
    C.add(ellipse("دائرة وردية (انتقال الخاتمة)", 40, fill=OUTRO_PINK, pos=[540, 960], size=keys((T_WIPE, [40, 40]), (T_OUTRO, [2400, 2400]), ease="in"),
                  inp=T_WIPE, outp=T_OUTRO + 0.4))
    C.add(footage("خاتمة بالديرما الوردية", PK + "palderma_pink_outro.mp4", start=T_OUTRO - 0.05, inp=T_OUTRO - 0.05, outp=DUR,
                  op=keys((T_OUTRO - 0.05, 0), (T_OUTRO + 0.25, 100), ease="soft")))
    ta = T_OUTRO + 2.2
    C.add(footage("زر واتساب +972598219030", PK + "whatsapp_pill.mov", seq="/home/user/klf/wa", start=ta, inp=ta, outp=DUR, pos=[540, 960 + 190]))
    C.markers += [(T_MSG, "زر المراسلة"), (T_WIPE, "دائرة وردية"), (T_OUTRO, "الخاتمة الوردية"), (ta, "واتساب")]
    return C

if __name__ == "__main__":
    C = build()
    print("dur", DUR, "doc", DOC_LEN, "cuts", CUTS, "msg", T_MSG, "click", T_CLICK, "outro", T_OUTRO)
    print({k: T[k] for k in ("kalaf", "ma", "bilkreem", "yrooh", "sahih", "whye", "taqsheer", "waqi", "khate", "falhek", "mish", "markaz", "istifsar", "end11")})
    import numpy as np
    from PIL import Image
    for t in [float(x) for x in sys.argv[1:]]:
        fr = render_comp(C, t)
        Image.fromarray(fr.clip(0, 255).astype(np.uint8)).save(f"/home/user/klf/prev/p_{t:05.2f}.jpg", quality=88)
