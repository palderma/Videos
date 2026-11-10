#!/usr/bin/env python3
"""Compositor for «التوقيت قبل المناسبة»: background, pink light, 3D calendar layer, Arabic typography, logo, frame.
Built as a kf scene graph -> renders the MP4 frames here AND exports the After Effects build script.
usage: comp.py assets | comp.py render <f0> <f1> <out.mp4> | comp.py still <t,...> | comp.py jsx <pkgdir>"""
import sys, os, math, subprocess
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, "/home/user/cal")
import kf
from kf import keys, K, text, rect, image, footage, ellipse, Comp, text_width
from tl import *

HERE = "/home/user/cal"; A = HERE + "/assets"
BG, GLOW, FRAME = A + "/bg.png", A + "/glow.png", A + "/frame-9x16.png"
LOGO = A + "/logo-ar-en-white.png"
CALMOV, CALSEQ = A + "/calendar-3d-alpha.mov", HERE + "/calseq"

def make_assets():
    os.makedirs(A, exist_ok=True)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - 540) / 900, (yy - 820) / 1150)
    inner, mid, outer = np.array((134, 24, 60.)), np.array((108, 13, 43.)), np.array((50, 4, 19.))
    k1 = np.clip(r / 0.55, 0, 1)[..., None]; k2 = np.clip((r - 0.55) / 0.75, 0, 1)[..., None]
    c = inner + (mid - inner) * (k1 ** 1.2)
    c = c + (outer - c) * (k2 ** 1.4)
    Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save(BG)
    n = 900; yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    g = np.exp(-(((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (2 * (n / 5.2) ** 2)))
    im = np.zeros((n, n, 4), np.uint8); im[..., :3] = PINK; im[..., 3] = np.clip(g * 255, 0, 255)
    Image.fromarray(im).save(GLOW)
    os.system('cp "/mnt/project-files/style-guide/assets/templates/frame-9x16.png" %s' % FRAME)
    lg = Image.open("/home/user/Videos/brand/logo/arabic-english/png/white.png").convert("RGBA")
    lg = lg.resize((360, int(lg.height * 360 / lg.width)), Image.LANCZOS); lg.save(LOGO)

SM = "smooth"
def line_layers(comp, name, runs, size, weight, y, tin, tout, stagger=0.09, rise=34, white=WHITE, pink=PINK):
    """a line of RTL runs, each its own text layer (first run = right-most); fades/rises/unblurs in, lifts out"""
    sp = size * 0.30
    ws = [text_width(r, size, weight) for r, _ in runs]
    total = sum(ws) + sp * (len(runs) - 1)
    x = 540 + total / 2
    for i, ((r, pk), w) in enumerate(zip(runs, ws)):
        cx = x - w / 2; x -= w + sp
        t0 = tin + i * stagger
        pos = keys((t0, [cx, y + rise]), (t0 + 0.75, [cx, y]), ease=SM)
        op = keys((t0, 0), (t0 + 0.55, 100), ease=SM)
        bl = keys((t0, 14), (t0 + 0.6, 0), ease=SM)
        if tout is not None:
            pos += keys((tout, [cx, y]), (tout + 0.4, [cx, y - 26]), ease="in")
            op += keys((tout, 100), (tout + 0.36, 0), ease="in")
            bl += keys((tout, 0), (tout + 0.4, 10), ease="in")
        comp.add(text("%s %d «%s»" % (name, i + 1, r), r, size, weight, pink if pk else white, pos=pos, op=op, blur=bl,
                      inp=t0, outp=(tout + 0.45) if tout is not None else None))

def pill_layers(comp, name, txt, y, tin, tout):
    size = 50
    tw = text_width(txt, size, "Bold"); pw, ph = tw + 92, 96
    sz = keys((tin, [ph, ph]), (tin + 0.6, [pw, ph]), ease=SM) + keys((tout, [pw, ph]), (tout + 0.4, [pw * 0.9, ph]), ease="in")
    op = keys((tin, 0), (tin + 0.3, 100), ease=SM) + keys((tout, 100), (tout + 0.36, 0), ease="in")
    pos = keys((tin, [540, y + 20]), (tin + 0.6, [540, y]), ease=SM) + keys((tout, [540, y]), (tout + 0.4, [540, y - 22]), ease="in")
    comp.add(rect("%s - كبسولة" % name, pw, ph, ph / 2, fill=PINK, size=sz, op=op, pos=pos, inp=tin, outp=tout + 0.45,
                  shadow=dict(color=(40, 3, 15), op=90, dist=10, soft=36, dir=180)))
    t1 = tin + 0.22
    tpos = keys((t1, [540, y + 17 + 14]), (t1 + 0.6, [540, y + 17]), ease=SM) + keys((tout, [540, y + 17]), (tout + 0.4, [540, y + 17 - 22]), ease="in")
    top = keys((t1, 0), (t1 + 0.5, 100), ease=SM) + keys((tout, 100), (tout + 0.3, 0), ease="in")
    comp.add(text("%s - نص" % name, txt, size, "Bold", BURG, pos=tpos, op=top, inp=t1, outp=tout + 0.45))

def build(tiktok=False):
    c = Comp("التوقيت قبل المناسبة 9x16" + (" تيك توك" if tiktok else ""), W, H, DUR, FPS, bg=BURG)
    c.add(image("خلفية عنابي متدرجة", BG, pos=[540, 960]))
    # soft pink light behind the calendar, breathing slowly
    c.add(image("إضاءة وردية خلف التقويم", GLOW, pos=keys((0, [700, 980]), (7.5, [640, 760]), (15, [560, 700]), (DUR, [540, 680]), ease="soft"),
                scale=keys((0, 120), (15, 150), (DUR, 160), ease="soft"),
                op=keys((0, 0), (1.6, 34), (6, 26), (10, 32), (12.4, 26), (14, 40), (20, 30), (DUR, 40), ease="soft")))
    c.add(footage("التقويم ثلاثي الأبعاد (رندر مع ظلاله)", CALMOV, start=0.0, seq=CALSEQ, pos=[540, 960]))
    LY1, LY2 = 1468, 1586
    s0 = SCENES[0]
    line_layers(c, "افتتاحية سطر1", s0["l1"], 96, "Bold", LY1 - 6, s0["tin"], s0["tout"])
    line_layers(c, "افتتاحية سطر2", s0["l2"], 74, "Medium", LY2 + 14, s0["tin2"], s0["tout"] + 0.06, pink=WHITE)
    for k, s in enumerate(SCENES[1:], 1):
        line_layers(c, "صفحة%d عنوان" % k, s["l1"], 96, "Bold", LY1, s["tin"], s["tout"])
        pill_layers(c, "صفحة%d" % k, s["l2"], LY2 - 17 + 17, s["tin2"], s["tout"] + 0.06)
    # golden rule (calendar has receded to the top)
    R_ = RULE; ly = 1062
    lw = text_width(R_["label"], 44, "Bold") + 70
    tlb = R_["tlabel"]
    c.add(rect("القاعدة الذهبية - كبسولة", lw, 76, 38, fill=PINK, inp=tlb, outp=R_["tout"] + 0.45,
               op=keys((tlb, 0), (tlb + 0.5, 100), ease=SM) + keys((R_["tout"], 100), (R_["tout"] + 0.36, 0), ease="in"),
               pos=keys((tlb, [540, ly + 18]), (tlb + 0.6, [540, ly]), ease=SM) + keys((R_["tout"], [540, ly]), (R_["tout"] + 0.4, [540, ly - 22]), ease="in")))
    c.add(text("القاعدة الذهبية - نص", R_["label"], 44, "Bold", BURG, inp=tlb + 0.1, outp=R_["tout"] + 0.45,
               op=keys((tlb + 0.1, 0), (tlb + 0.6, 100), ease=SM) + keys((R_["tout"], 100), (R_["tout"] + 0.3, 0), ease="in"),
               pos=keys((tlb + 0.1, [540, ly + 15 + 18]), (tlb + 0.7, [540, ly + 15]), ease=SM) + keys((R_["tout"], [540, ly + 15]), (R_["tout"] + 0.4, [540, ly + 15 - 22]), ease="in")))
    for si, (runs2, t0, t1) in enumerate(((R_["s1"], R_["t1"], R_["o1"]), (R_["s2"], R_["t2"], R_["tout"]))):
        for li, runs in enumerate(runs2):
            line_layers(c, "القاعدة جملة%d سطر%d" % (si + 1, li + 1), runs, 66, "Bold", 1205 + li * 98, t0 + li * 0.32, t1 + li * 0.06, stagger=0.07)
    # call to action
    C_ = CTA
    line_layers(c, "الدعوة سطر1", C_["l1"], 72, "Bold", 1255, C_["tin"], C_["tout"])
    line_layers(c, "الدعوة سطر2", C_["l2"], 72, "Bold", 1365, C_["tin2"], C_["tout"] + 0.06)
    for nm_, y_, t_ in (("calendar-heart", 1120, C_["tin"] - 0.1), ):
        c.add(image("أيقونة احفظه", A + "/icon-%s.png" % nm_, inp=t_, outp=C_["tout"] + 0.45,
                    pos=keys((t_, [540, y_ + 24]), (t_ + 0.7, [540, y_]), ease=SM) + keys((C_["tout"], [540, y_]), (C_["tout"] + 0.4, [540, y_ - 22]), ease="in"),
                    scale=keys((t_, 80), (t_ + 0.7, 100), ease=SM),
                    op=keys((t_, 0), (t_ + 0.5, 100), ease=SM) + keys((C_["tout"], 100), (C_["tout"] + 0.36, 0), ease="in")))
    # ending: strong phrase + official logo
    fy = 1252
    c.add(image("توهج خلف العبارة", GLOW, pos=[540, fy - 40], scale=keys((FINAL["tin"] - 0.1, 70), (DUR, 95), ease="soft"),
                op=keys((FINAL["tin"] - 0.1, 0), (FINAL["tin"] + 0.9, 22), (DUR, 18), ease=SM)))
    ws = [text_width(r, 150, "Black") for r, _ in FINAL["runs"]]; sp = 150 * 0.3
    total = sum(ws) + sp; x = 540 + total / 2
    for i, ((r, pk), w) in enumerate(zip(FINAL["runs"], ws)):
        cx = x - w / 2; x -= w + sp; t0 = FINAL["tin"] + i * 0.16
        c.add(text("خاتمة «%s»" % r, r, 150, "Black", PINK if pk else WHITE, inp=t0,
                   pos=keys((t0, [cx, fy + 30]), (t0 + 0.9, [cx, fy]), ease=SM),
                   scale=keys((t0, 108), (t0 + 1.0, 100), ease=SM),
                   op=keys((t0, 0), (t0 + 0.6, 100), ease=SM), blur=keys((t0, 18), (t0 + 0.7, 0), ease=SM)))
    tl_ = FINAL["logo"]
    c.add(image("شعار بالديرما الرسمي", LOGO, inp=tl_, pos=keys((tl_, [540, 1515]), (tl_ + 0.9, [540, 1490]), ease=SM),
                op=keys((tl_, 0), (tl_ + 0.8, 100), ease=SM), blur=keys((tl_, 10), (tl_ + 0.7, 0), ease=SM),
                scale=keys((tl_, 96), (tl_ + 1.2, 100), ease=SM)))
    if not tiktok: c.add(image("إطار الهوية (لوجو + تواصل)", FRAME, pos=[540, 960], op=keys((0, 100), (FRAME_OUT[0], 100), (FRAME_OUT[1], 0), ease=SM),
                outp=FRAME_OUT[1] + 0.05))
    for nm, (t0, d) in FLIPS.items(): c.markers.append((t0, "تقليب صفحة: %s" % nm))
    c.markers += [(SCENES[1]["tin"], "قبل 4 أسابيع"), (SCENES[2]["tin"], "قبل أسبوعين"), (SCENES[3]["tin"], "قبل أسبوع"),
                  (RULE["tlabel"], "القاعدة الذهبية"), (CTA["tin"], "الدعوة: احفظه وابعتوه"), (FINAL["tin"], "التوقيت بيفرق")]
    return c

def frame_rgb(c, t, seed):
    fr = kf.render_comp(c, t)
    g = np.random.default_rng(seed).standard_normal((H, W)).astype(np.float32) * 1.3
    fr += g[..., None]
    return np.clip(fr + 0.5, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "assets": make_assets(); sys.exit()
    c = build(tiktok=os.environ.get("TIKTOK") == "1")
    if cmd == "still":
        for tv in sys.argv[2].split(","):
            t = float(tv); Image.fromarray(frame_rgb(c, t, 1)).save("%s/st_%05.2f.png" % (HERE, t))
    elif cmd == "render":
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            p.stdin.write(frame_rgb(c, fi / FPS, fi).tobytes())
        p.stdin.close(); p.wait()
