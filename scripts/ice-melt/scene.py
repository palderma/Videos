#!/usr/bin/env python3
"""«ليش الشتا موسم التقشير؟» - melting-ice motion reel (Palderma, 2026-11-16).
Content (burgundy brand world) is a kf scene graph; the frost sheet on top is ice_fx.
Usage: python3 scene.py --t=3.5 [--t=...]          -> stills in work/
       python3 scene.py --frames=a:b --out=x.mp4   -> chunk render"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import kf
from kf import keys, K, text, rect, ellipse, image, footage, Comp, text_width
import icons
import ice_fx as IF

A = "/mnt/project-files/style-guide/assets/"
BG = A + "templates/خلفية-عنابي-9x16.png"
FRAME = A + "templates/frame-9x16.png"
OUTRO = A + "خاتمة-عمودي-9x16.mp4"
WINE, PINK, WHITE = (108, 13, 43), (243, 165, 189), (255, 255, 255)
FPS = 30
OUTRO_AT = 33.65
TOTAL = OUTRO_AT + 6.0

# ------------------------------------------------------------------ ice timeline
EV_SPEC = [  # kind, t0, t1, seed, origins(x, y, weight) , crack_at, crack origin
    ("melt", 2.90, 4.40, 101, [(540, 1060, 1.0), (560, 760, 1.25)], 2.45, (540, 1000)),
    ("freeze", 7.90, 8.70, 102, None, None, None),
    ("melt", 9.10, 10.60, 103, [(700, 1180, 1.0), (380, 800, 1.3)], 8.85, (640, 1150)),
    ("freeze", 14.10, 14.90, 104, None, None, None),
    ("melt", 15.30, 16.80, 105, [(420, 1240, 1.0), (640, 820, 1.2)], 15.05, (430, 1230)),
    ("freeze", 20.50, 21.30, 106, None, None, None),
    ("melt", 21.70, 23.20, 107, [(560, 1200, 1.0), (520, 700, 1.3)], 21.45, (560, 1180)),
    ("freeze", 26.70, 27.50, 108, None, None, None),
    ("melt", 27.90, 29.40, 109, [(540, 1120, 1.0), (380, 760, 1.4), (700, 760, 1.4)], 27.65, (540, 1110)),
    ("freeze", 32.70, 33.50, 110, None, None, None),
    ("melt", 33.80, 35.30, 111, [(540, 960, 1.0)], 33.55, (540, 960)),
]
_EVS = None
def evs():
    global _EVS
    if _EVS is None:
        _EVS = [IF.Ev(k, a, b, s, origins=o, crack_at=c, crack_origin=co) for k, a, b, s, o, c, co in EV_SPEC]
    return _EVS

def glint(t):
    # one slow light sweep across the frozen title, then again on each fully frozen hold
    for a in (0.6, 8.75, 14.95, 21.35, 27.55, 33.5):
        if a <= t <= a + 1.6:
            return -300 + (t - a) / 1.6 * 2700
    return None

SWAPS = [8.90, 15.10, 21.50, 27.70]       # slide changes happen under full frost

def k_(*a, **kw): return keys(*a, **kw)

# ------------------------------------------------------------------ helpers
def word_line(c, name, words, size, y, inp, outp, weight="Bold", gap=0.30, op=None, extra=None):
    """words = [(txt, colour)], laid out right-to-left and centred on x=540. returns layers"""
    ws = [text_width(w, size, weight) for w, _ in words]
    sp = size * gap; tot = sum(ws) + sp * (len(ws) - 1)
    x = 540 + tot / 2; out = []
    for (w, col), wd in zip(words, ws):
        cx = x - wd / 2
        L = c.add(text("%s - %s" % (name, w), w, size, weight, col, pos=[cx, y], inp=inp, outp=outp,
                       op=op if op is not None else 100.0))
        out.append(L); x -= wd + sp
    return out

def block(c, name, mains, sub, a, b, op, rv, y0=1205):
    """mains = list of word lists [(txt, col)], sub = plain white line under them"""
    y = y0; keyw = []
    for j, ws in enumerate(mains):
        Ls = word_line(c, "%s - سطر %d" % (name, j + 1), ws, 96, y, a, b, op=op)
        keyw += [L for L, (_, col) in zip(Ls, ws) if col == PINK]
        y += 122
    word_line(c, name + " - سطر فرعي", [(w, WHITE) for w in sub.split()], 58, y - 10, a, b, weight="Medium",
              op=[K(x.t, x.v * 0.82) for x in op])
    for L in keyw: pulse(L, rv - 0.1)

def fade_ops(inp, outp, fin=0.25, fout=0.25):
    ks = []
    ks.append(K(inp, 0)); ks.append(K(inp + fin, 100))
    ks.append(K(outp - fout, 100)); ks.append(K(outp, 0))
    return ks

def pulse(L, t, amt=8, dur=0.7):
    L.scale = [K(0, 100), K(t, 100, 60, 60), K(t + dur * 0.45, 100 + amt, 60, 60), K(t + dur, 100, 60, 60)]

def disc(c, name, x, y, d, inp, outp, op):
    c.add(ellipse(name + " - توهج", d * 1.15, fill=PINK, fill_op=14, pos=[x, y], inp=inp, outp=outp, op=op, blur=60))
    c.add(ellipse(name + " - زجاج", d, fill=WHITE, fill_op=7, stroke=PINK, stroke_w=3, stroke_op=55, pos=[x, y], inp=inp, outp=outp, op=op))

def chips(c, active, inp, outp, op):
    w, h, g = 104, 50, 18; n = 4; tot = n * w + (n - 1) * g
    for i in range(n):
        x = 540 + tot / 2 - w / 2 - i * (w + g)     # 01 on the right (RTL)
        on = (i + 1 == active); done = i + 1 < active
        c.add(rect("مؤشر %02d" % (i + 1), w, h, h / 2, fill=PINK if on else WHITE, fill_op=100 if on else (22 if done else 8),
                   stroke=None if on else WHITE, stroke_w=0 if on else 2, stroke_op=45, pos=[x, 560], inp=inp, outp=outp, op=op))
        c.add(text("مؤشر %02d - رقم" % (i + 1), "%02d" % (i + 1), 30, "Bold", WINE if on else WHITE, pos=[x, 571], inp=inp, outp=outp,
                   op=op if on else [K(k.t, k.v * 0.7) for k in op]))

def header(c, inp, outp, op):
    word_line(c, "عنوان صغير", [("ليش", WHITE), ("الشتا", WHITE), ("موسم", WHITE), ("التقشير؟", PINK)], 50, 470, inp, outp, "Bold", op=op)

# ------------------------------------------------------------------ build
def build():
    C = Comp("الجليد المنصهر - المحتوى", 1080, 1920, TOTAL, FPS, bg=WINE)
    C.add(image("خلفية عنابي", BG, pos=[540, 960], scale=[K(0, 100, 33, 33, lin=True), K(TOTAL, 106, 33, 33, lin=True)]))
    C.add(image("إطار بالديرما", FRAME, pos=[540, 960], outp=OUTRO_AT + 0.1))
    bounds = [0.0] + SWAPS + [OUTRO_AT + 0.1]
    IC = 230

    def slide(i):
        a, b = bounds[i], bounds[i + 1]
        fin = 0.0 if i == 0 else 0.22
        op = [K(a - (0 if i == 0 else 0.11), 0 if i else 100), K(a + fin, 100), K(b - 0.11, 100), K(b + 0.11, 0)]
        if i == 0: op = [K(0, 100), K(b - 0.11, 100), K(b + 0.11, 0)]
        return a - (0 if i == 0 else 0.11), b + 0.11, op

    # ---- slide 1 : شمس أقل نسبيًا
    a, b, op = slide(0); rv = EV_SPEC[0][2]
    header(C, a, b, op); chips(C, 1, a, b, op)
    disc(C, "أيقونة 1", 540, 840, 330, a, b, op)
    C.add(image("أيقونة 1 - شمس وغيمة", icons.icon("cloud-sun", WHITE, IC), pos=[K(0, [540, 840]), K(rv, [540, 840], 60, 60), K(rv + 1.2, [540, 828], 60, 60), K(b, [540, 834], 60, 60)], inp=a, outp=b, op=op))
    block(C, "نقطة 1", [[("الشمس", WHITE), ("أضعف", PINK)]], "والبشرة بعد التقشير حساسة للشمس", a, b, op, rv, y0=1235)

    # ---- slide 2 : حماية أسهل بعد الجلسة + shield
    a, b, op = slide(1); rv = EV_SPEC[2][2]
    header(C, a, b, op); chips(C, 2, a, b, op)
    disc(C, "أيقونة 2", 540, 840, 330, a, b, op)
    C.add(image("أيقونة 2 - قطرات", icons.icon("droplets", WHITE, IC), pos=[540, 840], inp=a, outp=b, op=op,
                scale=[K(0, 100), K(rv - 0.25, 100, 60, 60), K(rv + 0.15, 108, 60, 60), K(rv + 0.5, 100, 60, 60)]))
    block(C, "نقطة 2", [[("حر", WHITE), ("وعرق", WHITE), ("أقل", PINK)]], "يعني تهيّج أقل بفترة التعافي", a, b, op, rv, y0=1235)

    # ---- slide 3 : مش للجميع: الفحص أول + scan face
    a, b, op = slide(2); rv = EV_SPEC[4][2]
    header(C, a, b, op); chips(C, 3, a, b, op)
    disc(C, "أيقونة 3", 540, 840, 330, a, b, op)
    C.add(image("أيقونة 3 - فحص الوجه", icons.icon("scan-face", WHITE, IC), pos=[540, 840], inp=a, outp=b, op=op))
    sc_y = [K(0, 760)]; sc_o = [K(0, 0)]
    for j in range(3):
        s0 = rv - 0.3 + j * 0.9
        sc_y += [K(s0, 762, 50, 50), K(s0 + 0.8, 918, 50, 50)]
        sc_o += [K(s0, 0), K(s0 + 0.12, 90), K(s0 + 0.68, 90), K(s0 + 0.8, 0)]
    C.add(rect("أيقونة 3 - خط المسح", 170, 5, 2.5, fill=PINK, pos=[K(0, [540, 760])] and [K(k.t, [540, k.v], k.i, k.o) for k in sc_y],
               inp=a, outp=b, op=sc_o, blur=1.5))
    block(C, "نقطة 3", [[("البشرة", WHITE), ("باهتة", PINK)], [("وناشفة", PINK), ("بالشتا", WHITE)]], "والتقشير بيجدد مظهرها", a, b, op, rv)

    # ---- slide 4 : واقي شمس يوميًا + tube + 7 days
    a, b, op = slide(3); rv = EV_SPEC[6][2]
    header(C, a, b, op); chips(C, 4, a, b, op)
    disc(C, "أيقونة 4", 540, 840, 330, a, b, op)
    C.add(image("أيقونة 4 - تقويم", icons.icon("calendar-heart", WHITE, IC), pos=[540, 840], inp=a, outp=b, op=op,
                rot=[K(0, 0), K(rv - 0.2, 0, 60, 60), K(rv + 0.25, -7, 60, 60), K(rv + 0.6, 4, 60, 60), K(rv + 0.9, 0, 60, 60)]))
    block(C, "نقطة 4", [[("بتلحق", WHITE), ("قبل", WHITE), ("مناسبات", PINK)], [("آخر", PINK), ("السنة", PINK), ("والصيف", PINK)]],
          "النتيجة بتحتاج وقت", a, b, op, rv)

    # ---- slide 5 : CTA
    a, b, op = slide(4); rv = EV_SPEC[8][2]
    for nm, ic, x in (("حفظ", "bookmark", 690), ("إرسال", "send", 390)):
        disc(C, "أيقونة " + nm, x, 800, 260, a, b, op)
    C.add(image("أيقونة حفظ", icons.icon("bookmark", WHITE, 180), pos=[690, 800], inp=a, outp=b, op=op))
    C.add(image("أيقونة حفظ - معبّاة", icons.icon("bookmark", PINK, 180, fill=PINK), pos=[690, 800], inp=a, outp=b,
                op=[K(0, 0), K(rv - 0.1, 0), K(rv + 0.2, 100), K(b - 0.11, 100), K(b + 0.11, 0)],
                scale=[K(0, 60), K(rv - 0.1, 60, 70, 70), K(rv + 0.25, 112, 60, 60), K(rv + 0.5, 100, 60, 60)]))
    t2 = rv + 0.55
    C.add(image("أيقونة إرسال", icons.icon("send", WHITE, 170), pos=[K(0, [395, 800]), K(t2, [395, 800], 70, 70), K(t2 + 0.35, [430, 768], 60, 60), K(t2 + 0.8, [395, 800], 60, 60)],
                inp=a, outp=b, op=op, rot=[K(0, 0), K(t2, 0, 60, 60), K(t2 + 0.35, -8, 60, 60), K(t2 + 0.8, 0, 60, 60)]))
    ws = word_line(C, "دعوة أ", [("احفظوه", PINK)], 150, 1150, a, b, weight="Black", op=op)
    pulse(ws[0], rv + 0.05)
    word_line(C, "دعوة ب", [("وابعتوه", WHITE), ("لحدا", WHITE), ("بيأجل", WHITE), ("التقشير", PINK)], 78, 1290, a, b, op=op)

    # ---- outro (official pink Palderma outro), revealed by the last melt
    C.add(footage("الخاتمة الوردية (قالب بالديرما)", OUTRO, start=OUTRO_AT, inp=OUTRO_AT, outp=TOTAL))

    # ================== on the ice surface (melts with the ice)
    T = Comp("على الجليد - العنوان", 1080, 1920, TOTAL, FPS, bg=(0, 0, 0))
    T.add(image("ندفة ثلج", icons.icon("snowflake", PINK, 170, sw=1.5), pos=[540, 690], inp=0, outp=4.6,
                op=[K(0.10, 0), K(0.70, 100)], scale=[K(0.10, 70, 30, 30), K(0.9, 100, 60, 60)],
                rot=[K(0.1, -40, 20, 20), K(4.6, 30, 20, 20)], blur=[K(0.1, 18), K(0.7, 0)]))
    l1 = word_line(T, "عنوان سطر 1", [("ليش", WINE), ("الشتا", WINE)], 140, 960, 0, 4.6, weight="Black")
    for j, L in enumerate(l1):
        t0 = 0.30 + j * 0.14
        L.op = [K(t0, 0), K(t0 + 0.5, 100)]; L.blur = [K(t0, 20), K(t0 + 0.55, 0)]
        L.pos = [K(t0, [L.pos[0], 1000], 80, 30), K(t0 + 0.6, [L.pos[0], 960], 85, 35)]
    l2w = text_width("موسم", 104, "Black") + text_width("التقشير؟", 104, "Black") + 104 * 0.3
    pw = l2w + 100
    T.add(rect("عنوان سطر 2 - كبسولة وردية", pw, 150, 75, fill=PINK, pos=[540, 1090], inp=0, outp=4.6,
               size=[K(0.7, [150, 150], 80, 30), K(1.3, [pw, 150], 85, 35)], op=[K(0.7, 0), K(0.9, 100)]))
    l2 = word_line(T, "عنوان سطر 2", [("موسم", WINE), ("التقشير؟", WINE)], 104, 1120, 0, 4.6, weight="Black")
    for j, L in enumerate(l2):
        t0 = 1.0 + j * 0.14
        L.op = [K(t0, 0), K(t0 + 0.4, 100)]; L.blur = [K(t0, 14), K(t0 + 0.45, 0)]
    C.markers = [(0, "العنوان على الجليد"), (2.45, "تشقق"), (2.9, "ذوبان 1: الشمس أضعف"), (7.9, "تجمّد"),
                 (9.1, "ذوبان 2: حر وعرق أقل"), (14.1, "تجمّد"), (15.3, "ذوبان 3: البشرة باهتة وناشفة"), (20.5, "تجمّد"),
                 (21.7, "ذوبان 4: مناسبات آخر السنة"), (26.7, "تجمّد"), (27.9, "ذوبان 5: احفظوه وابعتوه"), (32.7, "تجمّد"),
                 (33.8, "ذوبان 6: الخاتمة الوردية")]
    return C, T

def frame_at(C, T, t):
    c = kf.render_comp(C, t)
    top = kf.render_comp(T, t, alpha=True) if t < 4.6 else None
    return IF.render(c, top, t, evs(), glint=glint)

if __name__ == "__main__":
    from PIL import Image
    C, T = build()
    ts = [float(a[4:]) for a in sys.argv[1:] if a.startswith("--t=")]
    fr = [a for a in sys.argv[1:] if a.startswith("--frames=")]
    if ts:
        for t in ts:
            Image.fromarray(frame_at(C, T, t).astype(np.uint8)).save(os.path.join(IF.WORK, "s_%05.2f.png" % t))
    if fr:
        import subprocess
        a, b = map(int, fr[0].split("=")[1].split(":"))
        out = [x for x in sys.argv[1:] if x.startswith("--out=")][0].split("=", 1)[1]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "8", "-pix_fmt", "yuv444p", out], stdin=subprocess.PIPE)
        for i in range(a, b):
            f = frame_at(C, T, i / FPS)
            p.stdin.write(np.clip(f + np.random.default_rng(i).uniform(-0.5, 0.5, f.shape), 0, 255).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
