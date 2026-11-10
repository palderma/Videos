#!/usr/bin/env python3
"""«جلد الأوزة: 3 أفكار غلط» v5 (2026-11-10): v4 + an explainer opening (what is it: real photo + two lines)
+ slower pacing (reading holds inserted at static moments of the v4 timeline; all keys/in/out/sfx shift with them).
Usage: python3 gb5.py [--t=..] [--frames=a:b --out=DIR] [--sfx] [--jsx=PKGDIR] [--check]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ["GB_WORK"] = os.environ.get("GB_WORK", "/home/user/gb/work5")
import numpy as np
import gb, kf, gb4
from gb import k, Face, ImgFace, Piece, Shape, piece, add, sfx, FACES
from kf import K, val
from gb5_time import g, INTRO, INS

PINK, WHITE = gb.PINK, gb.WHITE
CARD = "/home/user/gb/kp/card.png"

def _keys(prop): return prop if isinstance(prop, list) and prop and isinstance(prop[0], K) else None

def shift_all():
    """move every key / in / out / sfx of the v4 build to the new clock; report any hold that is not static"""
    props = []
    for p in gb.PIECES + [L for L in gb.LAYERS if isinstance(L, Piece) and L not in gb.PIECES]:
        props += [(p, a) for a in ("pos", "rx", "ry", "rz", "op", "blur", "scale")]
    for n in gb.NULLS: props += [(n, a) for a in ("pos", "scale", "op")]
    for s in gb.LAYERS:
        if isinstance(s, Shape): props += [(s, a) for a in ("pos", "size", "op")]
    bad = 0; seen = set()
    for obj, a in props:
        ks = _keys(getattr(obj, a))
        if ks is None or id(ks) in seen: continue
        seen.add(id(ks))
        for t_ins, _ in INS:
            lo = [x for x in ks if x.t <= t_ins]; hi = [x for x in ks if x.t > t_ins]
            if lo and hi and not np.allclose(np.array(lo[-1].v, float), np.array(hi[0].v, float), atol=1e-3) and not lo[-1].hold:
                bad += 1; print("NOT STATIC at", t_ins, getattr(obj, "name", "?"), a, lo[-1].t, lo[-1].v, hi[0].t, hi[0].v)
        for x in ks: x.t = g(x.t)
    objs = set()
    for L in list(gb.LAYERS) + list(gb.PIECES):
        if id(L) in objs: continue
        objs.add(id(L))
        L.inp = g(L.inp) if L.inp >= 0 else L.inp
        if L.outp is not None: L.outp = g(L.outp)
    gb.SFX[:] = [(round(g(t), 4),) + tuple(r) for t, *r in gb.SFX]
    gb.MARKERS = [(round(g(t), 2), m) for t, m in gb.MARKERS]
    return bad

def build5():
    gb4.build4()
    bad = shift_all()
    if bad: print("WARNING:", bad, "keyed values change across a hold")
    # frame: on from the very start (covers the explainer too)
    F = gb4.FRAME_OP
    F[:] = [k(0.0, 0), k(0.35, 100), k(g(16.35), 100), k(g(16.7), 0)]
    # ================= explainer (0 - INTRO): what is «جلد الأوزة»? =================
    OUT = INTRO - 0.55
    gb4.word_line("سؤال", [("شو", WHITE), ("يعني", WHITE), ("جلد", PINK), ("الأوزة؟", PINK)], 96, 470, 0.05, 0.09, OUT)
    ImgFace("صورة جلد الأوزة", CARD)
    f = FACES["صورة جلد الأوزة"]; fw, fh = f.w, f.h
    nl = gb.null("مفتاح - الصورة", [k(0.25, [540, 975, 160], 70, 10), k(0.95, [540, 975, 0], 85, 70),
                                    k(OUT - 0.05, [540, 975, 0], 70, 40), k(OUT + 0.4, [540, 975, -40], 40, 70)],
                 scale=[k(0.95, 100, 70, 40), k(OUT - 0.05, 103, 40, 70)])
    n = 6; sw = fw / n
    for s in range(n):
        col = n - 1 - s
        x0 = col * sw + (-0.5 if col > 0 else 0); x1 = (col + 1) * sw - (-0.5 if col < n - 1 else 0); cxs = (x0 + x1) / 2
        a = 0.25 + s * 0.0625; b = a + 0.42
        e = OUT + s * 0.035; eb = e + 0.36
        add(piece("صورة ش%d" % (s + 1), "صورة جلد الأوزة", (x0, 0, x1, fh), (cxs, fh / 2), [cxs - fw / 2, 0, 0],
                  ry=[k(a, 90, 70, 15), k(b, 0, 45, 70), k(b + 0.08, -4, 50, 50), k(b + 0.18, 0, 60, 70), k(e, 0, 70, 45), k(eb, -88, 20, 70)],
                  op=[k(a, 0), k(a + 0.12, 100), k(e + 0.2, 100), k(eb, 0)], parent=nl, inp=a, outp=eb, shade=True))
        sfx(b, "click", 0.55, pan=(cxs / fw - 0.5) * 0.6)
    gb4.word_line("شرح1", [("حبوب", WHITE), ("صغيرة", WHITE), ("وخشنة", PINK), ("ع", WHITE), ("الجلد", WHITE)], 70, 1460, 1.05, 0.07, OUT)
    gb4.word_line("شرح2", [("غالبًا", WHITE), ("ورا", WHITE), ("الذراع", WHITE), ("والفخذين", WHITE)], 62, 1560, 1.45, 0.07, OUT + 0.05)
    sfx(0.2, "whoosh_soft", 0.45); sfx(OUT, "whoosh", 0.55)
    gb.MARKERS = [(0.0, "التمهيد: شو يعني جلد الأوزة؟ (صورة + شرح)")] + gb.MARKERS
    gb.T["vlen"] = gb.VLEN

MAIN_LEN = g(17.0)
gb4.MAIN_LEN = MAIN_LEN
gb4.VLEN = gb.VLEN = MAIN_LEN + gb4.OUTRO_LEN
gb.build = build5

if __name__ == "__main__":
    os.makedirs(gb.WORK, exist_ok=True)
    if "--check" in sys.argv:
        build5(); print("main", round(MAIN_LEN, 2), "total", gb.VLEN, "frames", round(MAIN_LEN * 30)); sys.exit()
    jsx = [a for a in sys.argv[1:] if a.startswith("--jsx=")]
    if jsx:
        sys.argv = [sys.argv[0]]
        import gb_jsx
        gb_jsx.main(jsx[0].split("=", 1)[1])
    else:
        gb.main()
