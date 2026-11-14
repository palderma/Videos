#!/usr/bin/env python3
"""SQUARE 1:1 of the user's finished «الكلف جاهز» (= their own 1.13 s hook + our v3 edit). Re-laid out for the square, not letterboxed:
doctor framed head-to-chest under the logo row, captions in the lower band, scene 1 = doctor card on the right + text column on the left,
scene 2 re-centred, messenger button under his face, square brand frame + square pink outro. Audio = the user's own final mix."""
import os, sys, copy
os.environ.setdefault("KL_PKG", "/home/user/klf/pkg_sq")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl2_edit as E
from kf import *
PK = E.PK; W = H = 1080; FPS = 30
HOOK = 34 / FPS                      # v3 frame 0 = user frame 34
DUR = 32.0

def mapv(p, f):
    if isinstance(p, list) and p and isinstance(p[0], K):
        out = []
        for k in p:
            k2 = copy.copy(k); k2.v = f(k.v); out.append(k2)
        return out
    return f(p)
def move(L, fx=lambda x: x, fy=lambda y: y, s=1.0):
    L.pos = mapv(L.pos, lambda v: [fx(v[0]), fy(v[1])])
    if s != 1.0: L.scale = mapv(L.scale, lambda v: [v[0] * s, v[1] * s] if isinstance(v, list) else v * s)

def sq_M1():
    c = E.build_M1(); c.h = H; c.name += " (مربع)"
    for L in c.layers:
        n = L.name
        if n.startswith("خلفية"): L.pos = [540, 540]
        elif n.startswith("ضو"): move(L, fy=lambda y: y - 420)
        elif n.startswith("بطاقة الدكتور") or n.startswith("شارة"):      # doctor card on the right
            move(L, lambda x: 800 + (x - 540) * 0.8, lambda y: 590 + (y - 640) * 0.8, 0.8)
        elif n.startswith("رقم شبح"):
            move(L, lambda x: 300 + (x - 540) * 0.6, lambda y: 640 + (y - 1640) * 0.6, 0.6)
        else:                                                              # text / icons column on the left
            move(L, lambda x: 300 + (x - 540) * 0.82, lambda y: 600 + (y - 1300) * 0.82, 0.82)
    return c

def sq_M2():
    c = E.build_M2(); c.h = H; c.name += " (مربع)"
    for L in c.layers:
        n = L.name
        if n.startswith("خلفية"): L.pos = [540, 540]
        elif n.startswith("ضو"): move(L, fy=lambda y: y - 420)
        else: move(L, lambda x: 540 + (x - 540) * 0.85, lambda y: 600 + (y - 975) * 0.85, 0.85)
    return c

def sq_v3():
    C = E.build(); C.h = H; C.name = "أسباب فشل علاج الكلف - مربع (المونتاج)"
    C.markers = [(t, m) for t, m in C.markers]
    for L in C.layers:
        n, k = L.name, L.kind
        if n.startswith("الدكتور"): L.pos = [540, 430]; L.scale = mapv(L.scale, lambda v: v * 0.8)
        elif n.startswith("تظليل تحت"): L.kw["path"] = PK + "shade_bottom_1x1.png"; L.pos = [540, 540]
        elif k == "precomp" and n.startswith("مشهد 1"): L.kw["comp"] = sq_M1(); L.pos = [540, 540]
        elif k == "precomp" and n.startswith("مشهد 2"): L.kw["comp"] = sq_M2(); L.pos = [540, 540]
        elif n.startswith("انتقال فلاش") or k == "ellipse": L.pos = [540, 540]
        elif n.startswith("قالب الهوية"): L.kw["path"] = PK + "frame_template_1x1.png"; L.pos = [540, 540]
        elif n.startswith("زر مراسلة"): L.pos = [540 + (540 - 551) * 0.7, 780 - (1421 - 960) * 0.7]; L.scale = 70
        elif n.startswith("خاتمة"): L.kw["path"] = PK + "palderma_pink_outro_1x1.mp4"; L.pos = [540, 540]
        elif k in ("text", "rect", "image"): move(L, fy=lambda y: y - 400)
        else: print("UNMAPPED", n)
    return C

def build():
    S = Comp("الكلف جاهز - مربع 1x1", W, H, DUR, FPS, bg=E.DEEP)
    # the user's own hook (their footage + text), cropped to the square, under their flash
    S.add(footage("هوك المستخدم (من الكلف جاهز - مقصوص مربع)", PK + "user_final_9x16.mp4", start=0, pos=[540, 540 + 960 - 840],
                  inp=0, outp=HOOK + 0.02))
    v3 = sq_v3()
    S.add(precomp("المونتاج (مربع)", v3, start=HOOK, inp=HOOK, outp=DUR, pos=[540, 540]))
    S.add(footage("انتقال فلاش هوك -> المونتاج (ملف المستخدم)", PK + "flash_transition.mov", seq="/home/user/klf/flash",
                  start=32 / FPS - E.FLASH_PEAK, inp=32 / FPS - E.FLASH_PEAK, outp=32 / FPS - E.FLASH_PEAK + 24 / FPS, pos=[540, 540]))
    S.markers += [(0, "هوك المستخدم"), (HOOK, "بداية المونتاج")]
    return S

if __name__ == "__main__":
    import numpy as np
    from PIL import Image
    if sys.argv[1:2] == ["render"]:
        import subprocess
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; C = build()
        p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1080", "-r", "30", "-i", "-",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for i in range(a, b): p.stdin.write(render_comp(C, i / 30).clip(0, 255).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait(); print("done", out); sys.exit()
    C = build(); ims = []
    ts = [float(x) for x in sys.argv[1:]]
    for t in ts: ims.append(Image.fromarray(render_comp(C, t).clip(0, 255).astype(np.uint8)).resize((360, 360)))
    cols = 6; sh = Image.new("RGB", (360 * cols, 360 * ((len(ims) + cols - 1) // cols)))
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * 360, (i // cols) * 360))
    sh.save("/home/user/klf/sq/sheet.jpg", quality=85)
