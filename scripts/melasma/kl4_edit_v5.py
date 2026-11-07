#!/usr/bin/env python3
"""v4 = 2.5 s teaser hook «من أكثر 3 أسباب بتزيد الكلف» (doctor's own sentence, uncut) + the approved v3 comp as a precomp."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl2_edit as E
from kl2_edit import *
from kl_edit import R, o

H = 1.85                                   # hook length; v3 starts here (hidden by the user's flash)
SRC0 = o(8.2)                             # edit-time of the clip start (cut file), 4.4667
def h(raw): return round(o(raw) - SRC0, 3)
VOICE_END = h(9.62)                       # v5: stop after «ثلاث أسباب» (real dip before «تزيد»)
DUR = round(H + E.DUR, 3)
# shifted times for the audio script
M1_IN, M1_OUT, M2_IN, M2_OUT = (x + H for x in (E.M1_IN, E.M1_OUT, E.M2_IN, E.M2_OUT))
SPEECH_END, T_OUTRO, T_WIPE = E.SPEECH_END + H, E.T_OUTRO + H, E.T_WIPE + H
T = {k: v + H for k, v in E.T.items()}
HT = dict(min=h(R["min"]), thalath=h(R["thalath"]), bitzeed=h(R["bitzeed"]))

def build():
    C = Comp("أسباب فشل علاج الكلف - ريلز 9x16 v5 (مع هوك)", W, E.H, DUR, FPS, bg=DEEP)
    FACE = [510 - 540, 640 - 960]
    zk = keys((0, 134), (H, 141), ease="lin")
    C.add(footage("هوك - الدكتور (من أكثر 3 أسباب)", PK + "doctor_graded_cut.mp4", start=-SRC0, anchor=FACE, pos=[540, 700], scale=zk,
                  remap=[K(0, SRC0, lin=True), K(VOICE_END, SRC0 + VOICE_END, lin=True), K(H + 0.1, SRC0 + VOICE_END, lin=True)],
                  inp=0, outp=H + 0.1, blur=keys((0, 8), (0.35, 0), ease="smooth")))
    C.add(image("هوك - تظليل تحت", PK + "shade_bottom.png", pos=[540, 960], outp=H + 0.1))
    # v5 (user): no numbers / badges, only «من أكثر ثلاث أسباب»
    word_layer(C, "هوك - من أكثر", "من أكثر", 64, "Medium", WHITE, 540, 1150, HT["min"] - 0.06, H + 0.05)
    xs, _ = line_layout(["ثلاث", "أسبـــاب"], 150, "Black", 0.22)
    word_layer(C, "هوك - ثلاث (وردي)", "ثلاث", 150, "Black", PINK, xs[0], 1310, HT["thalath"] - 0.06, H + 0.05, rise=24, dur=0.45, blur=18, scale_pop=True)
    word_layer(C, "هوك - أسباب", "أسبـــاب", 150, "Black", WHITE, xs[1], 1310, HT["thalath"] + 0.12, H + 0.05, rise=24, dur=0.45, blur=18)
    C.add(image("هوك - قالب الهوية", PK + "frame_template_9x16.png", pos=[540, 960], outp=H + 0.1))
    # the approved v3 edit, untouched, starts at H
    C.add(precomp("الفيديو v3 (معتمد)", E.build(), start=H, inp=H, outp=DUR))
    C.add(footage("انتقال فلاش هوك -> الفيديو (ملف المستخدم)", PK + "flash_transition.mov", seq="/home/user/klf/flash",
                  start=H - FLASH_PEAK, inp=H - FLASH_PEAK, outp=H - FLASH_PEAK + 24 / FPS))
    C.markers += [(0, "هوك 3 أسباب"), (H, "بداية الفيديو v3 (فلاش)")]
    return C
