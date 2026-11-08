#!/usr/bin/env python3
"""«ضرورة واقي الشمس بالشتاء» v2 - after the user's notes on v1 (transitions not nice, PiP not centred, 0:30 layout,
more creativity / stronger yet softer motion):
- NO flashes. Doctor -> scene: the full-frame doctor glides and shrinks INTO the card (one continuous move, the
  rounded card matte closes around him) while his head stays OUT of the card (person matte); scene -> doctor: the card
  opens back to full frame. The doctor never cuts.
- Card centred on the doctor's own face position for each scene; head pops out above the card's top edge.
- Hook: giant «واقي الشمس» behind the doctor's head (depth), «صيفًا وشتاءً» capsule in front; soft blur-dissolve into
  the video.
- Scenes rebuilt on a centred column grid; M2 winter/summer UV bars panel; drifting snowflakes / warm bokeh.
Same kf scene graph -> MP4 and After Effects project (track mattes are native AE track mattes)."""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf import *
import ws_edit as V
from ws_edit import (W, H, FPS, BURG, PINK, WHITE, DEEP, CREAM, OUTRO_PINK, GLASS, WINE_GLASS, SH_TXT, SH_CARD, R, T, PK,
                     M1_IN, M1_OUT, M2_IN, M2_OUT, SPEECH_END, T_MSG, MSG_CLICK, T_CLICK, T_WIPE, T_OUTRO, DUR, CY, FACE,
                     kin, fio, word_layer, line_layout, phrase, glass_pill, icon_circle, SRC0, VOICE_END, HK, hk, o)
from ws_cuts import CUTS, DOC_LEN

PKG = V.PKG
SH_SOFT = dict(color=DEEP, op=110, dist=18, soft=60, dir=180)
DOC = PK + "doctor_graded_cut.mp4"; MAT = PK + "doctor_matte.mp4"
AX, AY = 500, 610                                   # source point under the layer anchor (FACE offset)
FULL_POS = [540, 700]
# card geometry (comp px): face sits at y=FY, card top just under the chin -> head out of the card
FY = 470; CS = 75.0
CARD_W, CARD_H = 640, 440
CARD_TOP = FY + 112; CARD_C = CARD_TOP + CARD_H / 2; CARD_BOT = CARD_TOP + CARD_H
CARD_R = 46
FACE_AVG = {1: (492, 585), 2: (484, 586)}           # tracked face per scene (source px)
MORPH = 1.2                                          # doctor -> card glide
IN_LEAD, OUT_LEAD = 0.25, 0.55                       # glide starts this long before the scene in / out point
TOTAL = round(HK + DUR, 3)

def card_pos(k, s=CS):
    fx, fy = FACE_AVG[k]
    return [540 - (fx - AX) * s / 100, FY - (fy - AY) * s / 100]

def scene_windows():
    out = []
    for k, (tin, tout) in ((1, (M1_IN, M1_OUT)), (2, (M2_IN, M2_OUT))):
        a0 = {1: o(6.70), 2: o(22.25)}[k]; a1 = a0 + MORPH
        b0 = {1: o(14.85), 2: o(32.55)}[k]            # card opens only after his last word of the scene («باستمرار» / «الصيف»)
        b1 = b0 + MORPH
        out.append((k, a0, a1, b0, b1))
    return out
SW = scene_windows()

def KK(t, v, inf=70): return K(t, v, inf, inf)

def doctor_keys():
    """scale / pos / matte (size, pos, radius) / column matte keys over the whole body"""
    sc = [KK(0.0, 129.0, 40)]; ps = [KK(0.0, FULL_POS)]
    msz = [KK(0.0, [1300, 2200])]; mps = [KK(0.0, [540, 960])]; mr = [KK(0.0, 0)]
    csz = [KK(0.0, [1300, 2200])]; cps = [KK(0.0, [540, 960])]
    zfull = {1: (131.0, 128.0), 2: (131.0, 128.0)}
    for k, a0, a1, b0, b1 in SW:
        zin, zout = zfull[k]; cp = card_pos(k); cp2 = card_pos(k, CS + 2.5)
        sc += [KK(a0, zin, 40), KK(a1, CS), KK(b0, CS + 2.5), KK(b1, zout)]
        ps += [KK(a0, FULL_POS), KK(a1, cp), KK(b0, cp2), KK(b1, FULL_POS)]
        msz += [KK(a0, [1300, 2200]), KK(a1, [CARD_W, CARD_H]), KK(b0, [CARD_W, CARD_H]), KK(b1, [1300, 2200])]
        mps += [KK(a0, [540, 960]), KK(a1, [540, CARD_C]), KK(b0, [540, CARD_C]), KK(b1, [540, 960])]
        mr += [KK(a0, 0), KK(a1, CARD_R), KK(b0, CARD_R), KK(b1, 0)]
        colh = CARD_BOT + 400
        csz += [KK(a0, [1300, 2200]), KK(a1, [CARD_W, colh]), KK(b0, [CARD_W, colh]), KK(b1, [1300, 2200])]
        cps += [KK(a0, [540, 960]), KK(a1, [540, CARD_BOT - colh / 2]), KK(b0, [540, CARD_BOT - colh / 2]), KK(b1, [540, 960])]
    sc += [KK(T_OUTRO + 0.1, 133.5, 40)]
    return sc, ps, msz, mps, mr, csz, cps

def person_comp(name, remap=None, start=0.0, dur=DOC_LEN):
    """doctor footage keyed by the RVM person matte (luma track matte) - full frame, comp-space identity"""
    c = Comp(name, W, H, dur, FPS, bg=(0, 0, 0))
    mt = footage("ماسك الشخص (RVM)", MAT, start=start, remap=remap, inp=0, outp=dur)
    c.add(footage("الدكتور", DOC, start=start, remap=remap, inp=0, outp=dur, matte=mt, matte_mode="luma"))
    return c

# ---------------------------------------------------------------- scene backgrounds (under the doctor card)
def bg_comp(k, d):
    c = Comp(f"خلفية مشهد {k}", W, H, d, FPS, bg=(0x63, 0, 0x2A))
    c.add(image("خلفية وردي-عنابي", PK + "bg_pink_wine.png", pos=[540, 960], scale=keys((0, 100), (d, 105), ease="lin")))
    c.add(image("ضو ناعم", PK + "soft_light.png", pos=keys((0, [760, 560]), (d, [430, 760]), ease="lin"), op=60,
                scale=keys((0, 105), (d, 122), ease="lin")))
    rnd = random.Random(10 + k)
    if k == 1:          # warm bokeh drifting up
        for i in range(12):
            x = rnd.uniform(60, 1020); y0 = rnd.uniform(500, 2000); sz = rnd.uniform(10, 26); sp = rnd.uniform(40, 90)
            c.add(ellipse(f"بوكيه {i + 1}", sz, fill=(255, 228, 236), pos=keys((0, [x, y0]), (d, [x + rnd.uniform(-40, 40), y0 - sp * d]), ease="lin"),
                          op=keys((0, 0), (0.8, rnd.uniform(18, 38)), (d - 0.5, rnd.uniform(18, 38)), (d, 0), ease="soft")))
    else:               # slow snowfall
        for i in range(10):
            x = rnd.choice([rnd.uniform(40, 230), rnd.uniform(850, 1040)]); y0 = rnd.uniform(-200, 1700); sp = rnd.uniform(35, 75); s_ = rnd.uniform(55, 120)
            c.add(image(f"ثلجة {i + 1}", PK + "icon_snowflake_white.png", pos=keys((0, [x, y0]), (d, [x + rnd.uniform(-60, 60), y0 + sp * d]), ease="lin"),
                        scale=s_, rot=keys((0, 0), (d, rnd.uniform(-90, 90)), ease="lin"),
                        op=keys((0, 0), (0.8, rnd.uniform(12, 22)), (d - 0.5, rnd.uniform(12, 22)), (d, 0), ease="soft")))
    return c

# ---------------------------------------------------------------- scene texts (above the card)
COL_Y1, COL_Y2, COL_PILL, COL_ICON = 1105, 1240, 1398, 1572

def txt_M1(d, t):
    c = Comp("مشهد 1 - نصوص (الساعة بتقلك قديش)", W, H, d, FPS, bg=(0, 0, 0))
    s0 = MORPH - IN_LEAD - 0.15                          # content starts as the card settles
    end = d
    c.add(text("UV شبح", "UV", 600, "Black", WHITE, pos=keys((s0, [540, 1760]), (end, [540, 1720]), ease="lin"),
               op=keys((s0, 0), (s0 + 0.9, 6), (end - 0.5, 6), (end, 0), ease="soft")))
    b2 = t(T["wtkoon"]) - 0.08
    word_layer(c, "ممكن يعطيك", "ممكن يعطيك", 58, "Medium", WHITE, 540, COL_Y1, s0, b2, rise=22, dur=0.7)
    word_layer(c, "قديش تستخدم", "قديش تستخدم", 106, "Black", WHITE, 540, COL_Y2, max(s0 + 0.2, t(T["qadeesh"]) - 0.04), b2, rise=26, blur=16, dur=0.75)
    tp = t(T["waqi"]) - 0.12; pw = text_width("من واقي الشمس", 76, "Black") + 140
    glass_pill(c, "كبسولة واقي الشمس", pw, 136, COL_PILL, tp, b2, stroke=PINK)
    word_layer(c, "من واقي الشمس (وردي)", "من واقي الشمس", 76, "Black", PINK, 540, COL_PILL + 27, tp + 0.08, b2, scale_pop=True, dur=0.7)
    for nm, ic, x, ta in (("ساعة", "icon_watch.png", 640, s0 + 0.3), ("جوال", "icon_smartphone.png", 440, s0 + 0.55)):
        icon_circle(c, nm, ic, x, COL_ICON, 150, ta, b2)
    word_layer(c, "وتكون حريص", "وتكون حريص", 58, "Medium", WHITE, 540, COL_Y1, b2 + 0.1, end, rise=22, dur=0.7)
    word_layer(c, "على استخدامه", "على استخدامـه", 106, "Black", WHITE, 540, COL_Y2, t(T["harees"]) - 0.04, end, rise=26, blur=16, dur=0.75)
    tb = t(T["bistimrar"]) - 0.2; pw2 = text_width("باستمرار", 76, "Black") + 200
    glass_pill(c, "كبسولة باستمرار", pw2, 136, COL_PILL, tb, end, stroke=PINK)
    c.add(image("أيقونة تكرار", PK + "icon_repeat_white.png", pos=[540 - pw2 / 2 + 74, COL_PILL], op=fio(tb + 0.15, end, 0.35, 0.35),
                rot=keys((tb + 0.15, -90), (tb + 0.9, 0), ease="smooth"), inp=tb))
    word_layer(c, "باستمرار (وردي)", "باستمرار", 76, "Black", PINK, 540 + 30, COL_PILL + 27, tb + 0.08, end, scale_pop=True, dur=0.7)
    icon_circle(c, "واقي - درع", "icon_shield_check.png", 540, COL_ICON, 150, b2 + 0.3, end)
    return c

def txt_M2(d, t):
    c = Comp("مشهد 2 - نصوص (الشتاء أعلى من الصيف)", W, H, d, FPS, bg=(0, 0, 0))
    s0 = MORPH - IN_LEAD - 0.15; end = d
    tl = t(T["li2no"]) - 0.1; ta = t(T["a3la"]) - 0.06
    # part 1: «تابعي هذه الأمور، وخصوصًا بفصل الشتاء»
    word_layer(c, "تابعي هذه الأمور", "تابعي هذه الأمور", 58, "Medium", WHITE, 540, COL_Y1, s0, tl, rise=22, dur=0.7)
    word_layer(c, "وخصوصًا", "وخصوصًا", 70, "Bold", WHITE, 540, 1218, t(T["khsusan"]) - 0.04, tl, rise=22, dur=0.7)
    word_layer(c, "بفصل الشتاء (وردي)", "بفصل الشتـــاء", 124, "Black", PINK, 540, 1372, t(T["shita"]) - 0.1, tl, rise=26, blur=18, dur=0.8, scale_pop=True)
    icon_circle(c, "ثلج", "icon_snowflake.png", 540, 1560, 160, t(T["shita"]) + 0.15, tl)
    icon_circle(c, "شمس وغيم", "icon_cloud_sun.png", 540, 1290, 160, s0 + 0.3, t(T["khsusan"]) - 0.1)
    # part 2: «لأنه أحيانًا بفصل الشتاء بتكون UVA و UVB أعلى بكثير من فصل الصيف»
    word_layer(c, "أحيانًا بفصل الشتاء", "أحيانًا بفصل الشتاء", 66, "Bold", WHITE, 540, 1128, tl - 0.2, ta, rise=22, dur=0.7)
    word_layer(c, "أعلى بكثير (وردي)", "أعلى بكثيـــر", 108, "Black", PINK, 540, 1140, ta, end, rise=26, blur=16, dur=0.75, scale_pop=True)
    # v3: clean, airy comparison (no box, no underline) that ends well above the brand frame's bottom row
    tu = tl - 0.1
    pw = text_width("UVA  ·  UVB", 50, "Black") + 110
    glass_pill(c, "كبسولة UVA · UVB", pw, 96, 1262, tu, end, stroke=WHITE)
    word_layer(c, "عنوان UVA · UVB", "UVA  ·  UVB", 50, "Black", WHITE, 540, 1280, tu + 0.08, end, rise=10, dur=0.7)
    base = 1545; bw = 168
    for nm, x, col, fop, ic, h1, h2, dl in (("الشتاء", 540 + 135, PINK, 96, "icon_snowflake_white.png", 95, 200, 0.15),
                                             ("الصيف", 540 - 135, CREAM, 75, "icon_sun_white.png", 95, 95, 0.35)):
        tg = tl + 0.5 + dl
        hk_ = [(tg, 6), (tg + 1.0, h1)] + ([(ta - 0.1, h1), (ta + 0.9, h2)] if h2 != h1 else [])
        c.add(rect(f"عمود {nm}", bw, 6, 26, fill=col, fill_op=fop, pos=keys(*[(tt, [x, base - hh / 2]) for tt, hh in hk_], ease="io"),
                   size=keys(*[(tt, [bw, hh]) for tt, hh in hk_], ease="io"), shadow=SH_CARD, op=fio(tg, end, 0.3, 0.4), inp=tg - 0.02))
        lw = text_width(nm, 50, "Bold"); gx = 32
        word_layer(c, f"عنوان {nm}", nm, 50, "Bold", WHITE, x + gx / 2 + 6, base + 60, tg + 0.1, end, rise=12)
        c.add(image(f"أيقونة {nm}", PK + ic, pos=[x - lw / 2 - gx / 2 + 6, base + 43], scale=78, op=fio(tg + 0.15, end, 0.4, 0.4), inp=tg))
    c.add(ellipse("شارة أعلى - دائرة", 60, fill=CREAM, stroke=PINK, stroke_w=4, pos=[540 + 135, base - 200 + 44], shadow=SH_CARD,
                  scale=keys((ta + 0.9, 50), (ta + 1.5, 100), ease="smooth"), op=fio(ta + 0.9, end, 0.35, 0.4), inp=ta + 0.88))
    c.add(image("شارة أعلى - سهم", PK + "icon_chevrons_up.png", pos=[540 + 135, base - 200 + 44], scale=keys((ta + 0.95, 50), (ta + 1.55, 92), ease="smooth"),
               op=fio(ta + 0.95, end, 0.35, 0.4), inp=ta + 0.93))
    return c

# ---------------------------------------------------------------- body
def build():
    C = Comp("ضرورة واقي الشمس بالشتاء - الجسم v3", W, H, DUR, FPS, bg=DEEP)
    for i, tc in enumerate(CUTS): C.markers.append((tc, f"قص سكتة {i + 1} (ذوبان 6 فريم)"))
    sc, ps, msz, mps, mr, csz, cps = doctor_keys()
    # scene backgrounds (under the doctor)
    for k, a0, a1, b0, b1 in SW:
        d = b1 - a0 + 0.2
        C.add(precomp(f"خلفية مشهد {k}", bg_comp(k, d), start=a0, inp=a0, outp=b1 + 0.05, op=keys((a0, 0), (a0 + 0.4, 100), (b1 - 0.4, 100), (b1, 0), ease="soft")))
        C.add(rect(f"ظل البطاقة {k}", CARD_W, CARD_H, CARD_R, fill=CREAM, fill_op=100, pos=[540, CARD_C], shadow=SH_SOFT,
                   op=keys((a1 - 0.5, 0), (a1, 100), (b0, 100), (b0 + 0.4, 0), ease="soft"), inp=a1 - 0.5, outp=b0 + 0.45))
    # the doctor: one continuous layer, a rounded matte that is full-frame on his parts and closes into the card in the scenes
    mt = rect("ماسك البطاقة (يتقلص للمربع)", 1300, 2200, 0, fill=WHITE, size=msz, pos=mps, inp=0, outp=T_OUTRO + 0.1)
    mt.kw["radius"] = mr
    C.add(footage("الدكتور (ملوّن + قص السكتات بذوبان ناعم)", DOC, start=0, anchor=FACE, pos=ps, scale=sc, inp=0, outp=T_OUTRO + 0.1,
                  matte=mt, matte_mode="alpha"))
    # card stroke + head out of the card
    for k, a0, a1, b0, b1 in SW:
        C.add(rect(f"إطار البطاقة {k}", CARD_W, CARD_H, CARD_R, stroke=WHITE, stroke_w=4, stroke_op=90, pos=[540, CARD_C],
                   op=keys((a1 - 0.45, 0), (a1, 100), (b0, 100), (b0 + 0.35, 0), ease="soft"), inp=a1 - 0.5, outp=b0 + 0.4))
        cm = rect(f"ماسك العمود {k}", 1300, 2200, 0, fill=WHITE, size=csz, pos=cps, inp=a0, outp=b1)
        cm.kw["radius"] = mr
        C.add(precomp(f"راس الدكتور برا المربع {k}", person_comp(f"الدكتور مقصوص (RVM) {k}"), start=0, anchor=FACE, pos=ps, scale=sc,
                      inp=a0, outp=b1, matte=cm, matte_mode="alpha"))
    C.add(image("تظليل تحت (للكابشن)", PK + "shade_bottom.png", pos=[540, 960],
                op=keys((0, 100), *[x for k, a0, a1, b0, b1 in SW for x in ((a0, 100), (a0 + 0.5, 0), (b1 - 0.5, 0), (b1, 100))], (T_OUTRO, 100), (T_OUTRO + 0.3, 0), ease="soft"),
                outp=T_OUTRO + 0.35))
    # scene texts
    for (k, a0, a1, b0, b1), fn in zip(SW, (txt_M1, txt_M2)):
        d = b0 + 0.45 - a0
        comp_ = fn(d, lambda x, a0=a0: x - a0)
        C.add(precomp(comp_.name, comp_, start=a0, inp=a0, outp=b0 + 0.45, op=keys((b0 - 0.15, 100), (b0 + 0.4, 0), ease="soft")))
        C.markers += [(a0, f"المشهد {k}: الدكتور يدخل المربع"), (b0, f"المشهد {k}: المربع يفتح للدكتور")]

    # ---- doctor captions (same timing as v1)
    ta2 = T["aw"] - 0.06; a0_1 = SW[0][1]
    phrase(C, "كابشن 1", [("تعرف إنه", T["tarif"], WHITE), ("الساعة الذكية", T["saa"], PINK)], CY, ta2)
    icon_circle(C, "كابشن 1 - ساعة", "icon_watch.png", 540, 1322, 130, T["saa"], ta2)
    phrase(C, "كابشن 2", [("أو أي برنامج", T["aw"], WHITE), ("للطقس", T["tags"], PINK)], CY, a0_1 + 0.35)
    phrase(C, "كابشن 2 - على الجوال", [("على الجوال", T["jawal"], WHITE)], CY + 95, a0_1 + 0.35, 60, "Medium")
    icon_circle(C, "كابشن 2 - طقس", "icon_cloud_sun.png", 540, 1322, 130, T["aw"] + 0.1, a0_1 + 0.35)
    b1_1 = SW[0][4]; a0_2 = SW[1][1]
    t0 = max(T["hasab"] - 0.06, b1_1 - 0.3); t1 = T["illi"] - 0.06
    phrase(C, "كابشن 3 - حسب", [("حسب الـ", t0 + 0.04, WHITE), ("UV", max(T["uv"], t0 + 0.3), PINK)], CY - 160, t1, 64, "Bold")
    tc = T["uvab"] - 0.15; cw = 760
    C.add(rect("بطاقة UVA UVB - زجاج", cw, 180, 90, fill=GLASS, fill_op=62, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, CY - 10], shadow=SH_CARD,
               size=keys((tc, [cw * 0.6, 180]), (tc + 0.8, [cw, 180]), ease="smooth"), op=fio(tc, t1, 0.45, 0.35), inp=tc - 0.02, outp=t1 + 0.02))
    xs, _ = line_layout(["UVA", "و", "UVB"], 92, "Black", 0.4)
    for s_, x, col in zip(["UVA", "و", "UVB"], xs, [PINK, WHITE, PINK]):
        word_layer(C, "بطاقة - " + s_, s_, 92 if s_ != "و" else 70, "Black", col, x, CY + 22, tc + 0.1 + (0.3 if s_ == "UVB" else 0), t1, dur=0.7)
    ts = T["samsung"] - 0.06
    phrase(C, "كابشن 4", [("اللي بتعطيها", T["illi"], WHITE), ("الساعة", T["saa2"], PINK)], CY, ts)
    phrase(C, "كابشن 5", [("ساعة سامسونج", T["samsung"], WHITE), ("أو ساعة أبل", T["samsung"] + 0.7, WHITE)], CY, a0_2 + 0.35, 64)
    b1_2 = SW[1][4]
    tbn = T["binnisba"] - 0.06
    tw = T["wmumkin"] - 0.06
    phrase(C, "كابشن 7 - بالنسبة", [("بالنسبة", T["binnisba"], WHITE), ("لواقي الشمس", T["waqi2"], PINK)], 1352, tw, 62, "Bold")
    word_layer(C, "كابشن 7 - يجب استخدامه", "يجب استخدامه", 78, "Black", WHITE, 540, 1456, T["yajib"] - 0.04, tw)
    tm = T["sayfan"] - 0.15; pw2 = text_width("صيفًا وشتاءً", 108, "Black") + 150
    C.add(rect("كبسولة صيفًا وشتاءً - عنابي زجاج", pw2, 184, 92, fill=WINE_GLASS, fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1590],
               size=keys((tm, [pw2 * 0.6, 184]), (tm + 0.8, [pw2, 184]), ease="smooth"), op=fio(tm, tw, 0.45, 0.35), shadow=SH_CARD, inp=tm, outp=tw + 0.02))
    word_layer(C, "صيفًا وشتاءً (وردي)", "صيفًا وشتاءً", 108, "Black", PINK, 540, 1627, T["sayfan"] - 0.04, tw, rise=18, blur=18, scale_pop=True, dur=0.7)
    ta = T["ahlan"] - 0.06
    phrase(C, "كابشن 8 - وممكن بالشتاء", [("وممكن", T["wmumkin"], WHITE), ("بالشتاء", T["wmumkin"] + 0.5, PINK), ("يكون", T["wmumkin"] + 0.95, WHITE)], 1330, ta, 64, "Bold")
    tk = T["kul"] - 0.15; pw3 = text_width("كل ساعة ونص", 92, "Black") + 210
    glass_pill(C, "كبسولة كل ساعة ونص", pw3, 160, 1495, tk, ta, stroke=PINK)
    C.add(image("أيقونة مؤقت", PK + "icon_timer_white.png", pos=[540 - pw3 / 2 + 80, 1495], op=fio(tk + 0.2, ta, 0.35, 0.35),
                rot=keys((tk + 0.2, -60), (tk + 1.0, 0), ease="smooth"), inp=tk, outp=ta + 0.02))
    word_layer(C, "كل ساعة ونص (وردي)", "كل ساعة ونص", 92, "Black", PINK, 540 + 30, 1527, T["kul"] - 0.04, ta, scale_pop=True, dur=0.7)
    phrase(C, "كابشن 9", [("أهلًا وسهلًا بكم", T["ahlan"], WHITE)], CY, T["markaz"] - 0.06)
    phrase(C, "كابشن 10", [("من مركز", T["markaz"], WHITE), ("بالديرما", T["markaz"] + 0.35, PINK)], CY, T_MSG - 0.02, 76, "Black")

    # ---- brand frame; messenger -> pink circle -> pink outro (logo only)
    C.add(image("قالب الهوية (الإطار)", PK + "frame_template_9x16.png", pos=[540, 960], op=keys((T_WIPE, 100), (T_WIPE + 0.3, 0)), outp=T_WIPE + 0.35))
    C.add(footage("زر مراسلة الصفحة (ثابت على الضغطة)", PK + "messenger_button.mov", seq=V.SEQ + "msg", start=T_MSG, inp=T_MSG, outp=T_OUTRO + 0.05,
                  remap=[K(T_MSG, 0.0, lin=True), K(T_CLICK, MSG_CLICK / FPS, lin=True), K(T_OUTRO + 0.05, MSG_CLICK / FPS, lin=True)]))
    C.add(ellipse("دائرة وردية (انتقال الخاتمة)", 40, fill=OUTRO_PINK, pos=[540, 960], size=keys((T_WIPE, [40, 40]), (T_OUTRO, [2400, 2400]), ease="in"),
                  inp=T_WIPE, outp=T_OUTRO + 0.4))
    C.add(footage("خاتمة بالديرما الوردية", PK + "palderma_pink_outro.mp4", start=T_OUTRO - 0.05, inp=T_OUTRO - 0.05, outp=DUR,
                  op=keys((T_OUTRO - 0.05, 0), (T_OUTRO + 0.25, 100), ease="soft")))
    C.markers += [(T_MSG, "زر المراسلة"), (T_WIPE, "دائرة وردية"), (T_OUTRO, "الخاتمة الوردية")]
    return C

# ---------------------------------------------------------------- hook + main
XD = 0.55                                            # hook -> body soft blur dissolve
def build_main():
    C = Comp("ضرورة واقي الشمس بالشتاء - ريلز 9x16 v3", W, H, TOTAL, FPS, bg=DEEP)
    zk = keys((0, 131), (HK + 0.2, 135.5), ease="lin")
    remap = [K(0, SRC0, lin=True), K(VOICE_END, SRC0 + VOICE_END, lin=True), K(HK + 0.3, SRC0 + VOICE_END, lin=True)]
    C.add(footage("هوك - الدكتور (صيفًا وشتاءً)", DOC, start=-SRC0, anchor=FACE, pos=[540, 800], scale=zk, remap=remap, inp=0, outp=HK + 0.3))
    # giant title BEHIND his head (person matte on top) -> depth
    t_ = text("هوك - واقي الشمس (ورا الراس)", "واقي الشمس", 158, "Black", WHITE, inp=0, outp=HK + 0.3, shadow=dict(color=DEEP, op=90, dist=6, soft=40, dir=180))
    t_.pos = keys((0, [540, 600]), (0.9, [540, 572]), (HK + 0.3, [540, 565]), ease="smooth")
    t_.scale = keys((0, 90), (0.9, 100), (HK + 0.3, 103), ease="smooth")
    t_.op = keys((0, 0), (0.45, 100), ease="soft"); t_.blur = keys((0, 18), (0.6, 0), ease="smooth")
    C.add(t_)
    C.add(precomp("هوك - الدكتور مقصوص (قدام العنوان)", person_comp("هوك - الدكتور مقصوص (RVM)", remap=remap, start=-SRC0, dur=HK + 0.3),
                  start=0, anchor=FACE, pos=[540, 800], scale=zk, inp=0, outp=HK + 0.3))
    C.add(image("هوك - تظليل تحت", PK + "shade_bottom.png", pos=[540, 960], outp=HK + 0.3))
    word_layer(C, "هوك - يجب استخدامه", "يجب استخدامه", 76, "Bold", WHITE, 540, 1468, hk(R["yajib"]) - 0.04, HK + 0.25, rise=22, dur=0.7)
    tm = hk(R["sayfan"]) - 0.15; pw2 = text_width("صيفًا وشتاءً", 104, "Black") + 140
    C.add(rect("هوك - كبسولة عنابي زجاج", pw2, 172, 86, fill=WINE_GLASS, fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1590],
               size=keys((tm, [pw2 * 0.6, 172]), (tm + 0.7, [pw2, 172]), ease="smooth"), op=fio(tm, HK + 0.25, 0.4, 0.3), shadow=SH_CARD, inp=tm, outp=HK + 0.3))
    word_layer(C, "هوك - صيفًا وشتاءً (وردي)", "صيفًا وشتاءً", 104, "Black", PINK, 540, 1625, hk(R["sayfan"]) - 0.04, HK + 0.25, rise=18, dur=0.65, blur=18, scale_pop=True)
    C.add(image("هوك - قالب الهوية", PK + "frame_template_9x16.png", pos=[540, 960], outp=HK + 0.3))
    # body fades in over the held hook frame with a soft blur (no flash)
    C.add(precomp("الفيديو (الجسم)", build(), start=HK, inp=HK - XD / 2, outp=TOTAL,
                  op=keys((HK - XD / 2, 0), (HK + XD / 2, 100), ease="soft"), blur=keys((HK - XD / 2, 16), (HK + XD / 2 + 0.15, 0), ease="smooth"),
                  scale=keys((HK - XD / 2, 103), (HK + XD / 2 + 0.3, 100), ease="smooth")))
    C.markers += [(0, "هوك: واقي الشمس ورا الراس + صيفًا وشتاءً"), (HK, "بداية الفيديو (ذوبان ناعم)")]
    return C

if __name__ == "__main__":
    print("HK", HK, "body", DUR, "total", TOTAL, "scenes", SW)
    import numpy as np
    from PIL import Image
    C = build_main(); os.makedirs("/home/user/ws/prev2", exist_ok=True)
    for tt in [float(x) for x in sys.argv[1:]]:
        Image.fromarray(render_comp(C, tt).clip(0, 255).astype(np.uint8)).save(f"/home/user/ws/prev2/p_{tt:05.2f}.jpg", quality=88)
