#!/usr/bin/env python3
"""v4 = 2.5 s teaser hook «من أكثر 3 أسباب بتزيد الكلف» (doctor's own sentence, uncut) + the approved v3 comp as a precomp."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl2_edit as E
from kl2_edit import *
from kl_edit import R, o

H = 2.15                                   # hook length; v3 starts here (hidden by the user's flash)
SRC0 = o(24.33)                           # v6: hook = doctor saying «وبشرتك مش للتجربة»
def h(raw): return round(o(raw) - SRC0, 3)
VOICE_END = h(25.93)                      # real dip after «للتجربة»
DUR = round(H + E.DUR, 3)
# shifted times for the audio script
M1_IN, M1_OUT, M2_IN, M2_OUT = (x + H for x in (E.M1_IN, E.M1_OUT, E.M2_IN, E.M2_OUT))
SPEECH_END, T_OUTRO, T_WIPE = E.SPEECH_END + H, E.T_OUTRO + H, E.T_WIPE + H
T = {k: v + H for k, v in E.T.items()}
HT = dict(bashartak=h(24.37), mish=h(R["mish"]))

def build():
    C = Comp("أسباب فشل علاج الكلف - ريلز 9x16 v6 (هوك مش للتجربة)", W, E.H, DUR, FPS, bg=DEEP)
    FACE = [510 - 540, 640 - 960]
    zk = keys((0, 134), (H, 141), ease="lin")
    C.add(footage("هوك - الدكتور (بشرتك مش للتجربة)", PK + "doctor_graded_cut.mp4", start=-SRC0, anchor=FACE, pos=[540, 700], scale=zk,
                  remap=[K(0, SRC0, lin=True), K(VOICE_END, SRC0 + VOICE_END, lin=True), K(H + 0.1, SRC0 + VOICE_END, lin=True)],
                  inp=0, outp=H + 0.1, blur=keys((0, 8), (0.35, 0), ease="smooth")))
    C.add(image("هوك - تظليل تحت", PK + "shade_bottom.png", pos=[540, 960], outp=H + 0.1))
    # v6 (user): hook = «بشرتك مش للتجربة» with the doctor on screen saying it
    word_layer(C, "هوك - وبشرتك", "وبشرتك", 120, "Black", WHITE, 540, 1200, HT["bashartak"] - 0.06, H + 0.05, rise=22, dur=0.45, blur=16)
    tm = HT["mish"] - 0.12; pw2 = text_width("مش للتجربـــة", 116, "Black") + 140
    C.add(rect("هوك - كبسولة عنابي زجاج", pw2, 196, 98, fill=(0x4A, 0x05, 0x1E), fill_op=72, stroke=PINK, stroke_w=3, stroke_op=90, pos=[540, 1352],
               size=keys((tm, [pw2 * 0.6, 196]), (tm + 0.55, [pw2, 196]), ease="smooth"), op=fio(tm, H + 0.05, 0.35, 0.25), shadow=SH_CARD, inp=tm, outp=H + 0.08))
    word_layer(C, "هوك - مش للتجربة (وردي)", "مش للتجربـــة", 116, "Black", PINK, 540, 1392, HT["mish"] - 0.04, H + 0.05, rise=20, dur=0.4, blur=20, scale_pop=True)
    C.add(image("هوك - قالب الهوية", PK + "frame_template_9x16.png", pos=[540, 960], outp=H + 0.1))
    # the approved v3 edit, untouched, starts at H
    C.add(precomp("الفيديو v3 (معتمد)", E.build(), start=H, inp=H, outp=DUR))
    C.add(footage("انتقال فلاش هوك -> الفيديو (ملف المستخدم)", PK + "flash_transition.mov", seq="/home/user/klf/flash",
                  start=H - FLASH_PEAK, inp=H - FLASH_PEAK, outp=H - FLASH_PEAK + 24 / FPS))
    C.markers += [(0, "هوك 3 أسباب"), (H, "بداية الفيديو v3 (فلاش)")]
    return C
