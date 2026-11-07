#!/usr/bin/env python3
"""v4 = 2.5 s teaser hook «من أكثر 3 أسباب بتزيد الكلف» (doctor's own sentence, uncut) + the approved v3 comp as a precomp."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl2_edit as E
from kl2_edit import *
from kl_edit import R, o

H = 2.5                                   # hook length; v3 starts here (hidden by the user's flash)
SRC0 = o(8.2)                             # edit-time of the clip start (cut file), 4.4667
def h(raw): return round(o(raw) - SRC0, 3)
VOICE_END = h(10.57) + 0.05              # «...تزيد الكلف» ends; «وهي» is not used
DUR = round(H + E.DUR, 3)
# shifted times for the audio script
M1_IN, M1_OUT, M2_IN, M2_OUT = (x + H for x in (E.M1_IN, E.M1_OUT, E.M2_IN, E.M2_OUT))
SPEECH_END, T_OUTRO, T_WIPE = E.SPEECH_END + H, E.T_OUTRO + H, E.T_WIPE + H
T = {k: v + H for k, v in E.T.items()}
HT = dict(min=h(R["min"]), thalath=h(R["thalath"]), bitzeed=h(R["bitzeed"]))

def build():
    C = Comp("أسباب فشل علاج الكلف - ريلز 9x16 v4 (مع هوك)", W, E.H, DUR, FPS, bg=DEEP)
    FACE = [510 - 540, 640 - 960]
    zk = keys((0, 134), (H, 141), ease="lin")
    C.add(footage("هوك - الدكتور (من أكثر 3 أسباب)", PK + "doctor_graded_cut.mp4", start=-SRC0, anchor=FACE, pos=[540, 700], scale=zk,
                  inp=0, outp=H + 0.1, blur=keys((0, 8), (0.35, 0), ease="smooth")))
    C.add(image("هوك - تظليل تحت", PK + "shade_bottom.png", pos=[540, 960], outp=H + 0.1))
    tb = HT["thalath"] - 0.1
    for n, x in ((1, 640), (2, 540), (3, 440)):
        ta = tb + (n - 1) * 0.14
        C.add(ellipse(f"هوك - شارة {n}", 92, fill=PINK if n == 1 else CREAM, stroke=WHITE if n == 1 else PINK, stroke_w=4, pos=[x, 1045], shadow=SH_CARD,
                      scale=keys((ta, 40), (ta + 0.5, 100), ease="smooth"), op=fio(ta, H + 0.05, 0.25, 0.25), inp=ta - 0.02, outp=H + 0.08))
        C.add(text(f"هوك - شارة {n} رقم", str(n), 54, "Black", BURG, pos=[x, 1065], scale=keys((ta + 0.05, 40), (ta + 0.55, 100), ease="smooth"),
                   op=fio(ta + 0.05, H + 0.05, 0.25, 0.25), inp=ta - 0.02, outp=H + 0.08))
    word_layer(C, "هوك - من أكثر", "من أكثر", 58, "Medium", WHITE, 540, 1140, HT["min"] - 0.06, H + 0.05)
    word_layer(C, "هوك - 3 أسباب", "3 أسبـــاب", 150, "Black", WHITE, 540, 1290, HT["thalath"] - 0.06, H + 0.05, rise=24, dur=0.5, blur=18)
    pw = text_width("بتزيد الكلف", 84, "Black") + 130
    glass_pill(C, "هوك - كبسولة بتزيد الكلف", pw, 146, 1410, HT["bitzeed"] - 0.14, H + 0.05, stroke=PINK)
    word_layer(C, "هوك - بتزيد الكلف (وردي)", "بتزيد الكلف", 84, "Black", PINK, 540, 1440, HT["bitzeed"] - 0.06, H + 0.05, scale_pop=True)
    C.add(image("هوك - قالب الهوية", PK + "frame_template_9x16.png", pos=[540, 960], outp=H + 0.1))
    # the approved v3 edit, untouched, starts at H
    C.add(precomp("الفيديو v3 (معتمد)", E.build(), start=H, inp=H, outp=DUR))
    C.add(footage("انتقال فلاش هوك -> الفيديو (ملف المستخدم)", PK + "flash_transition.mov", seq="/home/user/klf/flash",
                  start=H - FLASH_PEAK, inp=H - FLASH_PEAK, outp=H - FLASH_PEAK + 24 / FPS))
    C.markers += [(0, "هوك 3 أسباب"), (H, "بداية الفيديو v3 (فلاش)")]
    return C
