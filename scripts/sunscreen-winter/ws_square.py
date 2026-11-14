#!/usr/bin/env python3
"""«ضرورة واقي الشمس بالشتاء» - SQUARE 1:1 (1080x1080) of the v3 edit: same timeline and audio, re-laid out for the
square (not a crop): doctor head-to-chest under the square brand header, captions in the lower band; in the scenes the
doctor glides into a card on the RIGHT with his head out of it, content in a column on the LEFT (RTL reading order);
hook title behind his head below the header; messenger button scaled into the square; square pink outro.
Same kf scene graph -> MP4 + native After Effects project."""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf import *
import ws_edit as V
import ws_edit2 as E
from ws_edit import (FPS, BURG, PINK, WHITE, DEEP, CREAM, OUTRO_PINK, GLASS, WINE_GLASS, SH_TXT, SH_CARD, R, T, PK, FACE,
                     T_MSG, MSG_CLICK, T_CLICK, T_WIPE, T_OUTRO, DUR, SRC0, VOICE_END, HK, hk, o, kin, fio, word_layer, line_layout)
from ws_cuts import CUTS, DOC_LEN
from ws_edit2 import DOC, MAT, AX, AY, FACE_AVG, MORPH, SW, person_comp, SH_SOFT, XD

W = H = 1080
TOTAL = round(HK + DUR, 3)
CY = 985                                       # caption baseline (lower band, below his scrub logo is out of frame)
FULL_POS = [540, 400]; Z0, Z1 = 115, 120       # face at y 400, head top under the header row (y<200)
# card on the right, content column on the left
CX, FY, CS = 790, 330, 62.0
CARD_W, CARD_H, CARD_R = 440, 410, 40
CARD_TOP = FY + 93; CARD_C = CARD_TOP + CARD_H / 2; CARD_BOT = CARD_TOP + CARD_H
LX = 290                                       # left column centre
LW = 470                                       # max text width in the column

def fit(txt, size, weight, maxw=LW, minsize=34):
    while text_width(txt, size, weight) > maxw and size > minsize: size -= 2
    return size

def icon_c(c, name, icon, x, y, d, t0, t1, isc=80):
    c.add(ellipse(name + " - دائرة", d, fill=CREAM, stroke=PINK, stroke_w=4, pos=[x, y], shadow=SH_CARD,
                  scale=keys((t0, 75), (t0 + 0.7, 100), ease="smooth"), op=fio(t0, t1, 0.45, 0.35), inp=t0 - 0.02, outp=t1 + 0.02))
    c.add(image(name + " - أيقونة", PK + icon, pos=[x, y], scale=keys((t0 + 0.1, isc * 0.78), (t0 + 0.75, isc), ease="smooth"),
                op=fio(t0 + 0.1, t1, 0.45, 0.35), inp=t0 - 0.02, outp=t1 + 0.02))

def pill(c, name, w, h, x, y, t0, t1, stroke=PINK, fill=GLASS, fill_op=62):
    return c.add(rect(name, w, h, h / 2, fill=fill, fill_op=fill_op, stroke=stroke, stroke_w=2.5, stroke_op=85, pos=[x, y], shadow=SH_CARD,
                      size=keys((t0, [w * 0.6, h]), (t0 + 0.7, [w, h]), ease="smooth"), op=fio(t0, t1, 0.35, 0.35), inp=t0 - 0.02, outp=t1 + 0.02))

def phrase(c, label, parts, y, t_end, size=60, weight="Bold", cx=540, maxw=W - 140):
    while True:
        xs, tot = line_layout([p[0] for p in parts], size, weight, cx=cx)
        if tot <= maxw or size <= 40: break
        size -= 2
    for (txt, t0, col), x in zip(parts, xs):
        word_layer(c, f"{label} - {txt}", txt, size, weight, col, x, y, t0 - 0.04, t_end)

def phrase_icon(c, label, parts, icon, t_icon, t_end, size=60, weight="Bold", d=84):
    _, tot = line_layout([p[0] for p in parts], size, weight)
    gap = 26; full = tot + gap + d; cx = 540 + (full - tot) / 2
    phrase(c, label, parts, CY, t_end, size, weight, cx=cx)
    icon_c(c, label + " - أيقونة", icon, 540 - full / 2 + d / 2, CY - 20, d, t_icon, t_end, 62)

def row_caps(c, label, lead, lead_t, cap, cap_t, t_end, lead_size=56, cap_size=70, y=CY + 15, h=104):
    """one centred row: white lead words on the right + wine glass capsule with pink words on the left"""
    tw = text_width(lead, lead_size, "Bold"); pw = text_width(cap, cap_size, "Black") + 84; gap = 26
    full = tw + gap + pw; xl = 540 + full / 2 - tw / 2; xc = 540 - full / 2 + pw / 2
    word_layer(c, label + " - " + lead, lead, lead_size, "Bold", WHITE, xl, y, lead_t - 0.04, t_end, rise=16, dur=0.7)
    tm = cap_t - 0.15
    c.add(rect(label + " - كبسولة عنابي زجاج", pw, h, h / 2, fill=WINE_GLASS, fill_op=74, stroke=PINK, stroke_w=3, stroke_op=90, pos=[xc, y - 22],
               size=keys((tm, [pw * 0.6, h]), (tm + 0.8, [pw, h]), ease="smooth"), op=fio(tm, t_end, 0.45, 0.35), shadow=SH_CARD, inp=tm, outp=t_end + 0.02))
    word_layer(c, label + " - " + cap, cap, cap_size, "Black", PINK, xc, y + 2, cap_t - 0.04, t_end, rise=14, blur=14, scale_pop=True, dur=0.7)

def card_pos(k, s=CS):
    fx, fy = FACE_AVG[k]
    return [CX - (fx - AX) * s / 100, FY - (fy - AY) * s / 100]

def KK(t, v, inf=70): return K(t, v, inf, inf)
BIG = [1300, 1300]
def doctor_keys():
    sc = [KK(0.0, Z0, 40)]; ps = [KK(0.0, FULL_POS)]
    msz = [KK(0.0, BIG)]; mps = [KK(0.0, [540, 540])]; mr = [KK(0.0, 0)]
    csz = [KK(0.0, BIG)]; cps = [KK(0.0, [540, 540])]
    colh = CARD_BOT + 400
    for k, a0, a1, b0, b1 in SW:
        sc += [KK(a0, Z0 + 2.5, 40), KK(a1, CS), KK(b0, CS + 2.0), KK(b1, Z0)]
        ps += [KK(a0, FULL_POS), KK(a1, card_pos(k)), KK(b0, card_pos(k, CS + 2.0)), KK(b1, FULL_POS)]
        msz += [KK(a0, BIG), KK(a1, [CARD_W, CARD_H]), KK(b0, [CARD_W, CARD_H]), KK(b1, BIG)]
        mps += [KK(a0, [540, 540]), KK(a1, [CX, CARD_C]), KK(b0, [CX, CARD_C]), KK(b1, [540, 540])]
        mr += [KK(a0, 0), KK(a1, CARD_R), KK(b0, CARD_R), KK(b1, 0)]
        csz += [KK(a0, BIG), KK(a1, [CARD_W, colh]), KK(b0, [CARD_W, colh]), KK(b1, BIG)]
        cps += [KK(a0, [540, 540]), KK(a1, [CX, CARD_BOT - colh / 2]), KK(b0, [CX, CARD_BOT - colh / 2]), KK(b1, [540, 540])]
    sc += [KK(T_OUTRO + 0.1, Z1, 40)]
    return sc, ps, msz, mps, mr, csz, cps

def bg_comp(k, d):
    c = Comp(f"خلفية مشهد {k} (مربع)", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    c.add(image("خلفية وردي-عنابي", PK + "bg_pink_wine.png", pos=[540, 540], scale=keys((0, 100), (d, 105), ease="lin")))
    c.add(image("ضو ناعم", PK + "soft_light.png", pos=keys((0, [380, 420]), (d, [640, 640]), ease="lin"), op=55, scale=keys((0, 100), (d, 118), ease="lin")))
    rnd = random.Random(20 + k)
    if k == 1:
        for i in range(10):
            x = rnd.uniform(40, 1040); y0 = rnd.uniform(300, 1200); sp = rnd.uniform(35, 70); sz = rnd.uniform(10, 22)
            c.add(ellipse(f"بوكيه {i + 1}", sz, fill=(255, 228, 236), pos=keys((0, [x, y0]), (d, [x + rnd.uniform(-30, 30), y0 - sp * d]), ease="lin"),
                          op=keys((0, 0), (0.8, rnd.uniform(16, 32)), (d - 0.5, rnd.uniform(16, 32)), (d, 0), ease="soft")))
    else:
        for i in range(8):
            x = rnd.choice([rnd.uniform(30, 90), rnd.uniform(560, 600), rnd.uniform(1010, 1060)]); y0 = rnd.uniform(-150, 900)
            sp = rnd.uniform(30, 60); s_ = rnd.uniform(50, 100)
            c.add(image(f"ثلجة {i + 1}", PK + "icon_snowflake_white.png", pos=keys((0, [x, y0]), (d, [x + rnd.uniform(-40, 40), y0 + sp * d]), ease="lin"),
                        scale=s_, rot=keys((0, 0), (d, rnd.uniform(-90, 90)), ease="lin"),
                        op=keys((0, 0), (0.8, rnd.uniform(12, 22)), (d - 0.5, rnd.uniform(12, 22)), (d, 0), ease="soft")))
    return c

Y_A, Y_B, Y_P, Y_I = 420, 525, 650, 805
def txt_M1(d, t):
    c = Comp("مشهد 1 - نصوص (مربع)", W, H, d, FPS, bg=(0, 0, 0))
    s0 = MORPH - 0.4; end = d
    b2 = t(T["wtkoon"]) - 0.08
    word_layer(c, "ممكن يعطيك", "ممكن يعطيك", 46, "Medium", WHITE, LX, Y_A, s0, b2, rise=18, dur=0.7)
    word_layer(c, "قديش تستخدم", "قديش تستخدم", fit("قديش تستخدم", 80, "Black"), "Black", WHITE, LX, Y_B, max(s0 + 0.2, t(T["qadeesh"]) - 0.04), b2, rise=22, blur=14, dur=0.75)
    sz = fit("من واقي الشمس", 56, "Black", LW - 90); pw = text_width("من واقي الشمس", sz, "Black") + 90
    tp = t(T["waqi"]) - 0.12
    pill(c, "كبسولة واقي الشمس", pw, 100, LX, Y_P, tp, b2)
    word_layer(c, "من واقي الشمس (وردي)", "من واقي الشمس", sz, "Black", PINK, LX, Y_P + 20, tp + 0.08, b2, scale_pop=True, dur=0.7)
    for nm, ic, x, ta in (("ساعة", "icon_watch.png", LX + 75, s0 + 0.3), ("جوال", "icon_smartphone.png", LX - 75, s0 + 0.55)):
        icon_c(c, nm, ic, x, Y_I, 120, ta, b2, 78)
    word_layer(c, "وتكون حريص", "وتكون حريص", 46, "Medium", WHITE, LX, Y_A, b2 + 0.1, end, rise=18, dur=0.7)
    word_layer(c, "على استخدامه", "على استخدامـه", fit("على استخدامـه", 80, "Black"), "Black", WHITE, LX, Y_B, t(T["harees"]) - 0.04, end, rise=22, blur=14, dur=0.75)
    tb = t(T["bistimrar"]) - 0.2; pw2 = text_width("باستمرار", 56, "Black") + 150
    pill(c, "كبسولة باستمرار", pw2, 100, LX, Y_P, tb, end)
    c.add(image("أيقونة تكرار", PK + "icon_repeat_white.png", pos=[LX - pw2 / 2 + 55, Y_P], scale=85, op=fio(tb + 0.15, end, 0.35, 0.35),
                rot=keys((tb + 0.15, -90), (tb + 0.9, 0), ease="smooth"), inp=tb))
    word_layer(c, "باستمرار (وردي)", "باستمرار", 56, "Black", PINK, LX + 24, Y_P + 20, tb + 0.08, end, scale_pop=True, dur=0.7)
    icon_c(c, "واقي - درع", "icon_shield_check.png", LX, Y_I, 120, b2 + 0.3, end, 78)
    return c

def txt_M2(d, t):
    c = Comp("مشهد 2 - نصوص (مربع)", W, H, d, FPS, bg=(0, 0, 0))
    s0 = MORPH - 0.4; end = d
    tl = t(T["li2no"]) - 0.1; ta = t(T["a3la"]) - 0.06
    word_layer(c, "تابعي هذه الأمور", "تابعي هذه الأمور", 46, "Medium", WHITE, LX, Y_A, s0, tl, rise=18, dur=0.7)
    word_layer(c, "وخصوصًا", "وخصوصًا", 54, "Bold", WHITE, LX, Y_B, t(T["khsusan"]) - 0.04, tl, rise=18, dur=0.7)
    word_layer(c, "بفصل الشتاء (وردي)", "بفصل الشتـاء", fit("بفصل الشتـاء", 88, "Black"), "Black", PINK, LX, Y_P + 10, t(T["shita"]) - 0.1, tl, rise=22, blur=16, dur=0.8, scale_pop=True)
    icon_c(c, "ثلج", "icon_snowflake.png", LX, Y_I, 120, t(T["shita"]) + 0.15, tl, 78)
    icon_c(c, "شمس وغيم", "icon_cloud_sun.png", LX, Y_P - 10, 120, s0 + 0.3, t(T["khsusan"]) - 0.1, 78)
    word_layer(c, "أحيانًا بفصل الشتاء", "أحيانًا بفصل الشتاء", fit("أحيانًا بفصل الشتاء", 52, "Bold"), "Bold", WHITE, LX, Y_A + 10, tl - 0.2, ta, rise=18, dur=0.7)
    word_layer(c, "أعلى بكثير (وردي)", "أعلى بكثيـر", fit("أعلى بكثيـر", 80, "Black"), "Black", PINK, LX, Y_A + 20, ta, end, rise=22, blur=14, dur=0.75, scale_pop=True)
    tu = tl - 0.1; pw = text_width("UVA  ·  UVB", 40, "Black") + 80
    pill(c, "كبسولة UVA · UVB", pw, 76, LX, 520, tu, end, stroke=WHITE)
    word_layer(c, "عنوان UVA · UVB", "UVA  ·  UVB", 40, "Black", WHITE, LX, 534, tu + 0.08, end, rise=8, dur=0.7)
    base = 865; bw = 130
    for nm, x, col, fop, ic, h1, h2, dl in (("الشتاء", LX + 100, PINK, 96, "icon_snowflake_white.png", 80, 205, 0.15),
                                             ("الصيف", LX - 100, CREAM, 75, "icon_sun_white.png", 80, 80, 0.35)):
        tg = tl + 0.5 + dl
        hk_ = [(tg, 6), (tg + 1.0, h1)] + ([(ta - 0.1, h1), (ta + 0.9, h2)] if h2 != h1 else [])
        c.add(rect(f"عمود {nm}", bw, 6, 22, fill=col, fill_op=fop, pos=keys(*[(tt, [x, base - hh / 2]) for tt, hh in hk_], ease="io"),
                   size=keys(*[(tt, [bw, hh]) for tt, hh in hk_], ease="io"), shadow=SH_CARD, op=fio(tg, end, 0.3, 0.4), inp=tg - 0.02))
        lw = text_width(nm, 42, "Bold"); gx = 28
        word_layer(c, f"عنوان {nm}", nm, 42, "Bold", WHITE, x + gx / 2 + 5, base + 52, tg + 0.1, end, rise=10)
        c.add(image(f"أيقونة {nm}", PK + ic, pos=[x - lw / 2 - gx / 2 + 5, base + 37], scale=66, op=fio(tg + 0.15, end, 0.4, 0.4), inp=tg))
    c.add(ellipse("شارة أعلى - دائرة", 52, fill=CREAM, stroke=PINK, stroke_w=3, pos=[LX + 100, base - 205 + 38], shadow=SH_CARD,
                  scale=keys((ta + 0.9, 50), (ta + 1.5, 100), ease="smooth"), op=fio(ta + 0.9, end, 0.35, 0.4), inp=ta + 0.88))
    c.add(image("شارة أعلى - سهم", PK + "icon_chevrons_up.png", pos=[LX + 100, base - 205 + 38], scale=keys((ta + 0.95, 45), (ta + 1.55, 80), ease="smooth"),
                op=fio(ta + 0.95, end, 0.35, 0.4), inp=ta + 0.93))
    return c

def build():
    C = Comp("ضرورة واقي الشمس بالشتاء - الجسم (مربع)", W, H, DUR, FPS, bg=DEEP)
    for i, tc in enumerate(CUTS): C.markers.append((tc, f"قص سكتة {i + 1} (ذوبان 6 فريم)"))
    sc, ps, msz, mps, mr, csz, cps = doctor_keys()
    for k, a0, a1, b0, b1 in SW:
        d = b1 - a0 + 0.2
        C.add(precomp(f"خلفية مشهد {k}", bg_comp(k, d), start=a0, pos=[540, 540], inp=a0, outp=b1 + 0.05,
                      op=keys((a0, 0), (a0 + 0.4, 100), (b1 - 0.4, 100), (b1, 0), ease="soft")))
        C.add(rect(f"ظل البطاقة {k}", CARD_W, CARD_H, CARD_R, fill=CREAM, pos=[CX, CARD_C], shadow=SH_SOFT,
                   op=keys((a1 - 0.5, 0), (a1, 100), (b0, 100), (b0 + 0.4, 0), ease="soft"), inp=a1 - 0.5, outp=b0 + 0.45))
    mt = rect("ماسك البطاقة (يتقلص للمربع)", BIG[0], BIG[1], 0, fill=WHITE, size=msz, pos=mps, inp=0, outp=T_OUTRO + 0.1)
    mt.kw["radius"] = mr
    C.add(footage("الدكتور (ملوّن + قص السكتات بذوبان ناعم)", DOC, start=0, anchor=FACE, pos=ps, scale=sc, inp=0, outp=T_OUTRO + 0.1,
                  matte=mt, matte_mode="alpha"))
    for k, a0, a1, b0, b1 in SW:
        C.add(rect(f"إطار البطاقة {k}", CARD_W, CARD_H, CARD_R, stroke=WHITE, stroke_w=3.5, stroke_op=90, pos=[CX, CARD_C],
                   op=keys((a1 - 0.45, 0), (a1, 100), (b0, 100), (b0 + 0.35, 0), ease="soft"), inp=a1 - 0.5, outp=b0 + 0.4))
        cm = rect(f"ماسك العمود {k}", BIG[0], BIG[1], 0, fill=WHITE, size=csz, pos=cps, inp=a0, outp=b1)
        cm.kw["radius"] = mr
        C.add(precomp(f"راس الدكتور برا المربع {k}", person_comp(f"الدكتور مقصوص (RVM) {k}"), start=0, anchor=FACE, pos=ps, scale=sc,
                      inp=a0, outp=b1, matte=cm, matte_mode="alpha"))
    C.add(image("تظليل تحت (للكابشن)", PK + "shade_bottom_sq.png", pos=[540, 540],
                op=keys((0, 100), *[x for k, a0, a1, b0, b1 in SW for x in ((a0, 100), (a0 + 0.5, 0), (b1 - 0.5, 0), (b1, 100))], (T_OUTRO, 100), (T_OUTRO + 0.3, 0), ease="soft"),
                outp=T_OUTRO + 0.35))
    for (k, a0, a1, b0, b1), fn in zip(SW, (txt_M1, txt_M2)):
        d = b0 + 0.45 - a0
        comp_ = fn(d, lambda x, a0=a0: x - a0)
        C.add(precomp(comp_.name, comp_, start=a0, pos=[540, 540], inp=a0, outp=b0 + 0.45, op=keys((b0 - 0.15, 100), (b0 + 0.4, 0), ease="soft")))
        C.markers += [(a0, f"المشهد {k}: الدكتور يدخل المربع"), (b0, f"المشهد {k}: المربع يفتح للدكتور")]

    # ---- doctor captions (lower band)
    a0_1 = SW[0][1]; b1_1 = SW[0][4]; a0_2 = SW[1][1]; b1_2 = SW[1][4]
    ta2 = T["aw"] - 0.06
    phrase_icon(C, "كابشن 1", [("تعرف إنه", T["tarif"], WHITE), ("الساعة الذكية", T["saa"], PINK)], "icon_watch.png", T["saa"], ta2)
    phrase_icon(C, "كابشن 2", [("أو أي برنامج", T["aw"], WHITE), ("للطقس على الجوال", T["tags"], PINK)], "icon_cloud_sun.png", T["aw"] + 0.1, a0_1 + 0.35, 56)
    t0 = max(T["hasab"] - 0.06, b1_1 - 0.3); t1 = T["illi"] - 0.06
    phrase(C, "كابشن 3 - حسب", [("حسب الـ", t0 + 0.04, WHITE), ("UV", max(T["uv"], t0 + 0.3), PINK)], CY, T["uvab"] - 0.2, 60)
    tc = T["uvab"] - 0.15; cw = 600
    C.add(rect("بطاقة UVA UVB - زجاج", cw, 140, 70, fill=GLASS, fill_op=62, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, CY - 20], shadow=SH_CARD,
               size=keys((tc, [cw * 0.6, 140]), (tc + 0.8, [cw, 140]), ease="smooth"), op=fio(tc, t1, 0.45, 0.35), inp=tc - 0.02, outp=t1 + 0.02))
    xs, _ = line_layout(["UVA", "و", "UVB"], 72, "Black", 0.4)
    for s_, x, col in zip(["UVA", "و", "UVB"], xs, [PINK, WHITE, PINK]):
        word_layer(C, "بطاقة - " + s_, s_, 72 if s_ != "و" else 56, "Black", col, x, CY + 5, tc + 0.1 + (0.3 if s_ == "UVB" else 0), t1, dur=0.7)
    ts = T["samsung"] - 0.06
    phrase(C, "كابشن 4", [("اللي بتعطيها", T["illi"], WHITE), ("الساعة", T["saa2"], PINK)], CY, ts)
    phrase(C, "كابشن 5", [("ساعة سامسونج", T["samsung"], WHITE), ("أو ساعة أبل", T["samsung"] + 0.7, WHITE)], CY, a0_2 + 0.35, 56)
    tw = T["wmumkin"] - 0.06
    ty = T["yajib"] - 0.1
    phrase(C, "كابشن 7 - بالنسبة", [("بالنسبة", T["binnisba"], WHITE), ("لواقي الشمس", T["waqi2"], PINK)], CY, ty)
    row_caps(C, "كابشن 7", "يجب استخدامه", T["yajib"], "صيفًا وشتاءً", T["sayfan"], tw)
    ta = T["ahlan"] - 0.06; tk = T["kul"] - 0.15
    phrase(C, "كابشن 8 - وممكن بالشتاء", [("وممكن", T["wmumkin"], WHITE), ("بالشتاء", T["wmumkin"] + 0.5, PINK), ("يكون", T["wmumkin"] + 0.95, WHITE)], CY, tk)
    pw3 = text_width("كل ساعة ونص", 66, "Black") + 160; py = CY - 8
    pill(C, "كبسولة كل ساعة ونص", pw3, 108, 540, py, tk, ta)
    C.add(image("أيقونة مؤقت", PK + "icon_timer_white.png", pos=[540 - pw3 / 2 + 60, py], op=fio(tk + 0.2, ta, 0.35, 0.35),
                rot=keys((tk + 0.2, -60), (tk + 1.0, 0), ease="smooth"), inp=tk, outp=ta + 0.02))
    word_layer(C, "كل ساعة ونص (وردي)", "كل ساعة ونص", 66, "Black", PINK, 540 + 26, py + 23, T["kul"] - 0.04, ta, scale_pop=True, dur=0.7)
    phrase(C, "كابشن 9", [("أهلًا وسهلًا بكم", T["ahlan"], WHITE)], CY, T["markaz"] - 0.06)
    phrase(C, "كابشن 10", [("من مركز", T["markaz"], WHITE), ("بالديرما", T["markaz"] + 0.35, PINK)], CY, T_MSG - 0.02, 66, "Black")

    C.add(image("قالب الهوية (الإطار المربع)", PK + "frame_template_1x1.png", pos=[540, 540], op=keys((T_WIPE, 100), (T_WIPE + 0.3, 0)), outp=T_WIPE + 0.35))
    C.add(footage("زر مراسلة الصفحة (ثابت على الضغطة)", PK + "messenger_button.mov", seq=V.SEQ + "msg", start=T_MSG, inp=T_MSG, outp=T_OUTRO + 0.05,
                  pos=[540, 440], scale=85,
                  remap=[K(T_MSG, 0.0, lin=True), K(T_CLICK, MSG_CLICK / FPS, lin=True), K(T_OUTRO + 0.05, MSG_CLICK / FPS, lin=True)]))
    C.add(ellipse("دائرة وردية (انتقال الخاتمة)", 40, fill=OUTRO_PINK, pos=[540, 540], size=keys((T_WIPE, [40, 40]), (T_OUTRO, [1600, 1600]), ease="in"),
                  inp=T_WIPE, outp=T_OUTRO + 0.4))
    C.add(footage("خاتمة بالديرما الوردية (مربع)", PK + "palderma_pink_outro_1x1.mp4", start=T_OUTRO - 0.05, pos=[540, 540], inp=T_OUTRO - 0.05, outp=DUR,
                  op=keys((T_OUTRO - 0.05, 0), (T_OUTRO + 0.25, 100), ease="soft")))
    C.markers += [(T_MSG, "زر المراسلة"), (T_WIPE, "دائرة وردية"), (T_OUTRO, "الخاتمة الوردية")]
    return C

HPOS = [540, 445]; HZ0, HZ1 = 110, 114
def build_main():
    C = Comp("ضرورة واقي الشمس بالشتاء - مربع 1x1 v1", W, H, TOTAL, FPS, bg=DEEP)
    zk = keys((0, HZ0), (HK + 0.2, HZ1), ease="lin")
    remap = [K(0, SRC0, lin=True), K(VOICE_END, SRC0 + VOICE_END, lin=True), K(HK + 0.3, SRC0 + VOICE_END, lin=True)]
    C.add(footage("هوك - الدكتور (صيفًا وشتاءً)", DOC, start=-SRC0, anchor=FACE, pos=HPOS, scale=zk, remap=remap, inp=0, outp=HK + 0.3))
    t_ = text("هوك - واقي الشمس (ورا الراس)", "واقي الشمس", 132, "Black", WHITE, inp=0, outp=HK + 0.3, shadow=dict(color=DEEP, op=90, dist=6, soft=36, dir=180))
    t_.pos = keys((0, [540, 326]), (0.9, [540, 304]), (HK + 0.3, [540, 298]), ease="smooth")
    t_.scale = keys((0, 90), (0.9, 100), (HK + 0.3, 103), ease="smooth")
    t_.op = keys((0, 0), (0.45, 100), ease="soft"); t_.blur = keys((0, 16), (0.6, 0), ease="smooth")
    C.add(t_)
    C.add(precomp("هوك - الدكتور مقصوص (قدام العنوان)", person_comp("هوك - الدكتور مقصوص (RVM)", remap=remap, start=-SRC0, dur=HK + 0.3),
                  start=0, anchor=FACE, pos=HPOS, scale=zk, inp=0, outp=HK + 0.3))
    C.add(image("هوك - تظليل تحت", PK + "shade_bottom_sq.png", pos=[540, 540], outp=HK + 0.3))
    row_caps(C, "هوك", "يجب استخدامه", hk(R["yajib"]), "صيفًا وشتاءً", hk(R["sayfan"]), HK + 0.25)
    C.add(image("هوك - قالب الهوية", PK + "frame_template_1x1.png", pos=[540, 540], outp=HK + 0.3))
    C.add(precomp("الفيديو (الجسم)", build(), start=HK, pos=[540, 540], inp=HK - XD / 2, outp=TOTAL,
                  op=keys((HK - XD / 2, 0), (HK + XD / 2, 100), ease="soft"), blur=keys((HK - XD / 2, 16), (HK + XD / 2 + 0.15, 0), ease="smooth"),
                  scale=keys((HK - XD / 2, 103), (HK + XD / 2 + 0.3, 100), ease="smooth")))
    C.markers += [(0, "هوك: واقي الشمس ورا الراس + صيفًا وشتاءً"), (HK, "بداية الفيديو (ذوبان ناعم)")]
    return C

if __name__ == "__main__":
    import numpy as np
    from PIL import Image
    C = build_main(); os.makedirs("/home/user/ws/prevsq", exist_ok=True)
    print("total", TOTAL)
    for tt in [float(x) for x in sys.argv[1:]]:
        Image.fromarray(render_comp(C, tt).clip(0, 255).astype(np.uint8)).save(f"/home/user/ws/prevsq/s_{tt:05.2f}.jpg", quality=88)
